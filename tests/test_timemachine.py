"""Synthetic-only statistical invariants; no historical or clinical results."""
import copy
import unittest
from timemachine import analyze, era_ablation, validate_dataset, wilson_interval, calibration
from timemachine.engine import _claims_at
import random


def fixture():
    taxa, claims, ledger, effort = [], [], [], []
    for i in range(8):
        for suffix in ('a', 'b'):
            species = f'Plant {i}{suffix}'
            taxa.append({'species': species, 'family': f'Family {i}'})
            effort.append({'species': species, 'year': 1899, 'count': 10})
            for cat in ('urinary', 'skin'):
                ledger.append({'species': species, 'category': cat, 'tested_year': 1905,
                               'confirmed_year': 1908 if (suffix == 'a' or i % 2 == 0) else None})
        claims.append({'id': str(i), 'identity_group': str(i), 'year': 60,
                       'layer': 'dioscorides', 'category': 'urinary', 'identity_available_year': 60,
                       'candidates': [{'species': f'Plant {i}a', 'probability': 1.}]})
    return {'taxa': taxa, 'claims': claims, 'ledger': ledger, 'effort': effort, 'observation_end': 2026}


class TemporalTests(unittest.TestCase):
    def run_analysis(self, data, **kwargs):
        return analyze(data, freeze_year=1900, bootstrap=120, imputations=3, **kwargs)

    def test_matched_rates_and_family_bootstrap(self):
        r = self.run_analysis(fixture())
        self.assertEqual(r['eligible_tested_pairs'], 32)
        methods = {m['method']: m for m in r['methods']}
        self.assertEqual(methods['within_species']['risk_ratio'], 1.)
        self.assertEqual(methods['within_family']['risk_ratio'], 2.)
        self.assertEqual(methods['research_effort']['risk_ratio'], 2.)
        self.assertEqual(methods['within_family']['family_clusters'], 8)
        self.assertIsNotNone(methods['within_species']['ci95'])
        self.assertGreater(methods['within_family']['undefined_bootstrap_replicates'], 0)
        self.assertIsNone(methods['within_family']['ci95'])

    def test_reproducible(self):
        self.assertEqual(self.run_analysis(fixture()), self.run_analysis(fixture()))

    def test_post_freeze_claims_and_effort_never_leak(self):
        data = fixture()
        old = self.run_analysis(data)
        data['claims'].append({'id': 'future', 'identity_group': 'future', 'year': 1901,
                               'layer': 'renaissance', 'category': 'skin', 'identity_available_year': 1901,
                               'candidates': [{'species': 'Plant 0a', 'probability': 1.}]})
        data['effort'].append({'species': 'Plant 0a', 'year': 1902, 'count': 100000})
        self.assertEqual(old, self.run_analysis(data))

    def test_first_test_not_confirmation_defines_cohort(self):
        data = fixture()
        # Confirmed after freeze, but already tested before freeze: never eligible.
        data['ledger'][0]['tested_year'] = 1890
        result = self.run_analysis(data)
        self.assertEqual(result['eligible_tested_pairs'], 31)

    def test_future_confirmation_is_not_a_window_success(self):
        data = fixture()
        for row in data['ledger']:
            if row['species'].endswith('b'):
                row['confirmed_year'] = 1921
        result = self.run_analysis(data)
        method = result['methods'][1]
        self.assertEqual(method['control_confirmation_risk'], 0.)
        self.assertIsNone(method['risk_ratio'])
        self.assertIsNone(method['ci95'])

    def test_unknown_effort_not_zero(self):
        data = fixture()
        data['effort'] = []
        self.assertEqual(self.run_analysis(data)['methods'][2]['mean_matched_pairs'], 0)

    def test_untested_absence_not_negative(self):
        data = fixture()
        data['ledger'] = [r for r in data['ledger'] if r['species'].endswith('a') and r['category'] == 'urinary']
        for method in self.run_analysis(data)['methods']:
            self.assertIsNone(method['risk_ratio'])
            self.assertEqual(method['mean_matched_pairs'], 0)

    def test_incomplete_followup_is_pending(self):
        data = fixture()
        self.assertEqual(analyze(data, freeze_year=2010)['status'], 'pending')

    def test_identity_prior_not_available_at_freeze(self):
        data = fixture()
        for claim in data['claims']:
            claim['identity_available_year'] = 1901
        self.assertEqual(self.run_analysis(data)['methods'][0]['mean_matched_pairs'], 0)

    def test_shared_identity_group_draw(self):
        data = fixture()
        claim = data['claims'][0]
        claim['candidates'] = [{'species': 'Plant 0a', 'probability': .5}, {'species': 'Plant 0b', 'probability': .5}]
        second = dict(claim, id='copy', category='skin')
        data['claims'] = [claim, second]
        for seed in range(10):
            pairs, _, _ = _claims_at(data, 1900, None, random.Random(seed))
            self.assertEqual(len({p[0] for p in pairs}), 1)
            self.assertEqual(len(pairs), 2)

    def test_inherited_is_not_an_independent_pair(self):
        data = fixture()
        claim = dict(data['claims'][0], id='later', year=600, layer='byzantine')
        data['claims'].append(claim)
        result = self.run_analysis(data)
        self.assertEqual(result['mean_inherited_claim_records'], 1)
        self.assertEqual(result['methods'][0]['mean_eligible_claimed_pairs'], 8)
        novel = self.run_analysis(data, novel_in_layer='byzantine')
        self.assertEqual(novel['methods'][0]['mean_eligible_claimed_pairs'], 0)

    def test_era_ablation_does_not_see_later_layers(self):
        data = fixture()
        data['claims'][0]['layer'] = 'byzantine'
        result = era_ablation(data, freeze_year=1900, bootstrap=0, imputations=1)
        self.assertEqual(result[0]['analysis']['methods'][0]['mean_eligible_claimed_pairs'], 7)
        self.assertEqual(result[1]['analysis']['methods'][0]['mean_eligible_claimed_pairs'], 8)

    def test_conflicting_evidence_sensitivity(self):
        data = fixture()
        for row in data['ledger']:
            if row['species'].endswith('a'):
                row['refuted_year'] = 1910
        result = self.run_analysis(data, count_refuted_as_failure=True)
        self.assertEqual(result['methods'][1]['claimed_confirmation_risk'], 0)

    def test_in_vitro_is_sensitivity_only(self):
        data = fixture()
        for row in data['ledger']:
            row['confirmed_year'] = None
            row['in_vitro_confirmed_year'] = 1910
        primary = self.run_analysis(data)
        sensitivity = self.run_analysis(data, allow_in_vitro=True)
        self.assertEqual(primary['methods'][0]['claimed_confirmation_risk'], 0)
        self.assertEqual(sensitivity['methods'][0]['claimed_confirmation_risk'], 1)

    def test_bad_probability_and_dates_rejected(self):
        data = fixture()
        data['claims'][0]['candidates'][0]['probability'] = .9
        with self.assertRaises(ValueError):
            validate_dataset(data)
        data = fixture()
        data['ledger'][0]['confirmed_year'] = 1900
        with self.assertRaises(ValueError):
            validate_dataset(data)

    def test_missing_identity_availability_rejected(self):
        data = fixture()
        data['claims'][0].pop('identity_available_year')
        with self.assertRaisesRegex(ValueError, 'identity_available_year'):
            self.run_analysis(data)

    def test_identity_draws_without_matches_suppress_selection_biased_estimate(self):
        data = fixture()
        data['claims'] = [data['claims'][0]]
        data['claims'][0]['candidates'] = [
            {'species': 'Plant 0a', 'probability': .5},
            {'species': 'Plant 0b', 'probability': .5}]
        # Only the first candidate has a claim-category row; missing rows
        # cannot be converted to experimental failures or discarded draws.
        data['ledger'] = [row for row in data['ledger']
                          if not (row['species'] == 'Plant 0b' and row['category'] == 'urinary')]
        result = analyze(data, freeze_year=1900, imputations=40, bootstrap=120)
        for method in result['methods']:
            self.assertIsNone(method['risk_ratio'])
            self.assertIsNone(method['ci95'])

    def test_bootstrap_rematching_is_reproducible(self):
        a=self.run_analysis(fixture(),resample_matching=True)
        b=self.run_analysis(fixture(),resample_matching=True)
        self.assertEqual(a,b)
        self.assertIn('rematching',a['ci_method'])
        self.assertEqual(a['methods'][1]['risk_ratio'],2.)

    def test_external_overlap_requires_verified_reference_labels(self):
        from timemachine.external_checks import yarnell_overlap
        self.assertEqual(yarnell_overlap(['Example plant'])['status'],'pending')
        self.assertEqual(yarnell_overlap(['Example plant'],['Example plant'],reference_source='citation')['status'],'pending')
        result=yarnell_overlap(['Plant A',' Plant B '],['plant a','plant c'],reference_verified=True,
                               reference_source='Synthetic-only fixture',counting_unit='species')
        self.assertEqual(result['overlap_count'],1)
        self.assertEqual(result['reference_recall'],.5)
        self.assertEqual(result['jaccard'],1/3)

    def test_wilson_and_calibration(self):
        lo, hi = wilson_interval(50, 100)
        self.assertAlmostEqual(lo, .40383153)
        self.assertAlmostEqual(hi, .59616847)
        self.assertIsNone(wilson_interval(0, 0))
        self.assertEqual(calibration([0., 1.], [0, 1])['ece'], 0)
        self.assertIsNone(calibration([], [])['ece'])


if __name__ == '__main__':
    unittest.main()
