"""Invented fixtures verify calendar separation and fit mechanics, never biology."""
import copy
import importlib.util
import json
import unittest
from timemachine.ranker import snapshot, fit_temporal, rank_forward
from timemachine import file_drawer_sensitivity


def synthetic_history():
    data={'observation_end':2026,'claims':[],'taxa':[],'ledger':[],'effort':[],'test_coverage':[]}
    for window,freeze in enumerate((1900,1950,1980)):
        for family in range(8):
            for variant in ('a','b'):
                species=f'Synthetic {window}-{family}-{variant}'
                data['taxa'].append({'species':species,'family':f'Family {family}',
                                     'regions':['mediterranean'],'hazard_trail':['Synthetic hazard; not a real plant.']})
                data['effort'].append({'species':species,'year':1890,'count':family+3})
                for category in ('urinary','skin'):
                    success=(variant=='a')==(category=='urinary')
                    data['ledger'].append({'species':species,'category':category,'tested_year':freeze+5,
                                           'confirmed_year':freeze+8 if success else None})
                    if success:
                        data['claims'].append({'id':f'{species}:{category}','identity_group':species,
                                               'year':60,'identity_available_year':60,'layer':'dioscorides',
                                               'category':category,'candidates':[{'species':species,'probability':1.}]})
    return data


class RankerTests(unittest.TestCase):
    def test_snapshot_never_uses_future_claim_effort_or_support(self):
        data=synthetic_history();before=snapshot(data,1900)
        c=copy.deepcopy(data['claims'][0]);c.update(id='future',identity_group='future',year=1901,identity_available_year=1901)
        data['claims'].append(c)
        data['effort'].append({'species':data['taxa'][0]['species'],'year':1901,'count':99999})
        self.assertEqual(before,snapshot(data,1900))
        for row in before:
            self.assertIsNone(row['features'][3])

    def test_prior_available_date_is_enforced_at_feature_snapshot(self):
        data=synthetic_history()
        for c in data['claims']:c['identity_available_year']=1901
        self.assertTrue(all(r['features'][0]==0 for r in snapshot(data,1900)))

    def test_calendar_cohorts_disjoint(self):
        data=synthetic_history()
        cohorts=[{(r['species'],r['category']) for r in snapshot(data,t)} for t in (1900,1950,1980)]
        self.assertFalse(cohorts[0]&cohorts[1]);self.assertFalse(cohorts[1]&cohorts[2])
        with self.assertRaisesRegex(ValueError,'overlap'):
            fit_temporal(data,train_freeze=1900,calibration_freeze=1910)

    def test_empty_is_pending_not_fitted(self):
        data={'claims':[],'ledger':[],'effort':[],'taxa':[],'observation_end':2026}
        self.assertEqual(fit_temporal(data)['status'],'pending')
        self.assertEqual(rank_forward(data,{'status':'pending'})['leads'],[])

    def test_incomplete_evaluation_pending(self):
        self.assertEqual(fit_temporal(synthetic_history(),evaluation_freeze=2010)['status'],'pending')

    def test_missing_negative_grid_is_explicit_assumption(self):
        result=file_drawer_sensitivity(synthetic_history(),freeze_year=1900,missing_negative_fractions=(0,1),imputations=2)
        self.assertEqual(result['status'],'assumptive')
        self.assertTrue(all(r['ci95'] is None for m in result['methods'] for r in m['grid']))

    @unittest.skipUnless(importlib.util.find_spec('lightgbm'),'Optional LightGBM runtime absent')
    def test_actual_temporal_fit_persistence_and_coverage_gate(self):
        data=synthetic_history()
        artifact=fit_temporal(data,ensembles=2,bootstrap=100)
        self.assertEqual(artifact['status'],'fitted')
        self.assertEqual(artifact['counts'],{'train':32,'calibration':32,'evaluation':32})
        self.assertEqual(artifact['fitted_through_year'],1970)
        self.assertEqual(artifact['evaluation']['reliability']['n'],32)
        self.assertEqual(len(artifact['model_strings']),2)
        json.dumps(artifact,allow_nan=False)
        # A claimed pair outside the ledger is unknown until complete search
        # coverage is explicitly supplied. Missing search records are not nulls.
        species='Synthetic forward'
        data['taxa'].append({'species':species,'family':'Family 0','regions':['balkan'],
                             'hazard_trail':['Synthetic-only toxicity unknown.']})
        data['claims'].append({'id':'forward','identity_group':'forward','year':1653,
                               'identity_available_year':1700,'layer':'renaissance','category':'urinary',
                               'candidates':[{'species':species,'probability':1.}]})
        self.assertEqual(rank_forward(data,artifact)['status'],'pending')
        data['test_coverage'].append({'species':species,'category':'urinary','complete':True,'through_year':2026})
        result=rank_forward(data,json.loads(json.dumps(artifact)))
        self.assertEqual(result['status'],'ranked')
        self.assertEqual(result['leads'][0]['species'],species)
        self.assertIn('conditional_on_testing',list(result['leads'][0].keys())[2])
        self.assertTrue(0<=result['leads'][0]['probability_conditional_on_testing']<=1)
        self.assertIn('not confidence interval',result['leads'][0]['interval_kind'])
        data['taxa'][-1]['hazard_trail']=[]
        self.assertEqual(rank_forward(data,artifact)['status'],'pending')

if __name__=='__main__':unittest.main()
