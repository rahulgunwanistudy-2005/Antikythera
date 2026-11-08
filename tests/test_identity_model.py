"""Synthetic expert labels test calibration software only, not identity accuracy."""
import copy
import json
import unittest
from identity.calibrate_prior import fit_identity_calibration,apply_identity_calibration


def rows(prefix):
    return [{'group_id':f'{prefix}-{i}','label_available_year':1900+i,
             'candidates':[{'species_id':'A','probability':.95,'source':'synthetic'},
                           {'species_id':'__other__','probability':.05,'source':'unresolved option'}],
             'true_species_id':'A' if i%4 else '__other__'} for i in range(24)]


class IdentityModelTests(unittest.TestCase):
    def test_fits_deterministically_with_heldout_improvement_on_known_overconfidence(self):
        cal,ev=rows('fit'),rows('eval')
        first=fit_identity_calibration(cal,ev)
        self.assertEqual(first,fit_identity_calibration(cal,ev))
        self.assertEqual(first['status'],'fitted')
        self.assertGreater(first['temperature'],1.)
        self.assertLess(first['evaluation']['after']['ece'],first['evaluation']['before']['ece'])
        self.assertLess(first['evaluation']['after']['negative_log_likelihood'],first['evaluation']['before']['negative_log_likelihood'])
        self.assertEqual(first['evaluation']['after']['n'],24)
        json.dumps(first,allow_nan=False)

    def test_evaluation_labels_cannot_change_fitted_temperature(self):
        cal,ev=rows('fit'),rows('eval')
        first=fit_identity_calibration(cal,ev)
        for r in ev:r['true_species_id']='A'
        second=fit_identity_calibration(cal,ev)
        self.assertEqual(first['temperature'],second['temperature'])
        self.assertNotEqual(first['evaluation'],second['evaluation'])

    def test_disjoint_groups_and_explicit_candidate_truth_required(self):
        with self.assertRaisesRegex(ValueError,'overlap'):fit_identity_calibration(rows('same'),rows('same'))
        bad=rows('bad');bad[0]['true_species_id']='missing'
        with self.assertRaisesRegex(ValueError,'existing candidate'):fit_identity_calibration(bad,rows('eval'))

    def test_temporal_gate_uses_latest_expert_label_from_both_splits(self):
        cal,ev=rows('fit'),rows('eval');ev[-1]['label_available_year']=2000
        artifact=fit_identity_calibration(cal,ev)
        self.assertEqual(artifact['available_year'],2000)
        with self.assertRaisesRegex(ValueError,'leak'):apply_identity_calibration(cal[0]['candidates'],artifact,1999)
        before=copy.deepcopy(cal[0]['candidates'])
        transformed=apply_identity_calibration(before,artifact,2000)
        self.assertEqual(before,cal[0]['candidates'])
        self.assertEqual([r['species_id'] for r in transformed],['A','__other__'])
        self.assertEqual(transformed[1]['source'],'unresolved option')
        self.assertAlmostEqual(sum(r['probability'] for r in transformed),1)

    def test_zero_probability_is_epsilon_explicit_and_other_not_dropped(self):
        artifact=fit_identity_calibration(rows('fit'),rows('eval'))
        candidates=[{'species_id':'A','probability':1.},{'species_id':'__other__','probability':0.}]
        transformed=apply_identity_calibration(candidates,artifact,2026)
        self.assertGreater(transformed[1]['probability'],0)
        self.assertIn('epsilon',artifact['zero_probability_policy'])

    def test_empty_thin_or_uniform_returns_pending(self):
        self.assertEqual(fit_identity_calibration([],[])['status'],'pending')
        self.assertEqual(fit_identity_calibration(rows('fit')[:2],rows('eval'))['status'],'pending')
        cal=rows('fit')
        for r in cal:
            for c in r['candidates']:c['probability']=.5
        self.assertEqual(fit_identity_calibration(cal,rows('eval'))['status'],'pending')
        with self.assertRaises(ValueError):apply_identity_calibration(rows('fit')[0]['candidates'],{'status':'pending'},2026)

if __name__=='__main__':unittest.main()
