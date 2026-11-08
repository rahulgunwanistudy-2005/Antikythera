"""Calendar-separated LightGBM training, calibration, evaluation and prioritization.

All probabilities condition on the pair being first tested in the following window.
They are not clinical efficacy, nor probability of being tested. No model is bundled.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from .engine import validate_dataset, calibration, _matches, _percentile

FEATURES = ['claim_count', 'layer_count', 'inherited', 'family_confirmation_rate', 'log_research_effort']
ESTIMAND = 'P(indexed in-vivo/clinical confirmation by T+20 | first relevant testing in (T,T+20])'


def _draw(claim, seed):
    key = f"{seed}:{claim['identity_group']}".encode()
    u = int.from_bytes(hashlib.sha256(key).digest()[:8], 'big') / 2**64
    cumulative = 0.
    for c in sorted(claim['candidates'], key=lambda c: c['species']):
        cumulative += c['probability']
        if u < cumulative:
            return c['species']
    return claim['candidates'][-1]['species']


def snapshot(data, freeze, seed=42, follow_up=20, candidates=None):
    """Return dated feature rows. Labels exist only for a fully mature tested cohort.

    candidates supplies explicit species/category pairs for forward inference;
    in that mode no future outcome or testing-date filtering is performed.
    """
    validate_dataset(data)
    taxa = {r['species']: r for r in data['taxa']}
    claim_rows = defaultdict(list)
    for c in data['claims']:
        if c['year'] <= freeze and c['identity_available_year'] <= freeze:
            claim_rows[(_draw(c, seed), c['category'])].append(c)
    effort = Counter()
    seen = set()
    for e in data['effort']:
        if e['year'] <= freeze:
            effort[e['species']] += e['count']
            seen.add(e['species'])
    family_tested, family_supports = Counter(), Counter()
    for row in data['ledger']:
        if row['tested_year'] <= freeze:
            family = taxa[row['species']]['family']
            family_tested[family] += 1
            if row.get('confirmed_year') is not None and row['confirmed_year'] <= freeze:
                family_supports[family] += 1
    ledger = {(r['species'], r['category']): r for r in data['ledger']}
    if candidates is None:
        if freeze + follow_up > data['observation_end']:
            return []
        pairs = [p for p, r in ledger.items() if freeze < r['tested_year'] <= freeze+follow_up]
    else:
        pairs = candidates
    result = []
    for species, category in sorted(set(pairs)):
        family = taxa[species]['family']
        claims = claim_rows[(species, category)]
        layers = {c['layer'] for c in claims}
        rate = family_supports[family] / family_tested[family] if family_tested[family] else None
        x = [len(claims), len(layers), int(len(layers) > 1), rate,
             math.log1p(effort[species]) if species in seen else None]
        row = {'species': species, 'category': category, 'family': family, 'features': x,
               'claimed': bool(claims), 'effort': effort[species] if species in seen else None}
        if candidates is None:
            date = ledger[(species, category)].get('confirmed_year')
            row['outcome'] = int(date is not None and date <= freeze+follow_up)
        result.append(row)
    return result


def _sigmoid(x):
    return 1 / (1 + math.exp(-max(-35, min(35, x))))


def _logit(p):
    p = max(1e-6, min(1-1e-6, float(p)))
    return math.log(p/(1-p))


def _calibrate_fit(predictions, labels):
    # Fixed-step ridge logistic calibration, fitted on calendar-separated data.
    # Nonnegative slope preserves rank order; an uninformative model can flatten.
    a, b = 1., 0.
    xs = [_logit(p) for p in predictions]
    for _ in range(600):
        errors = [_sigmoid(a*x+b)-y for x, y in zip(xs, labels)]
        a = max(0., a - .03 * (mean(e*x for e, x in zip(errors, xs)) + .01*a))
        b -= .03 * mean(errors)
    return {'slope': a, 'intercept': b, 'method': 'ridge_sigmoid_on_separate_calendar_window'}


def _apply(predictions, calibrator):
    return [_sigmoid(calibrator['slope']*_logit(p)+calibrator['intercept']) for p in predictions]


def _matrix(rows, np):
    return np.asarray([[float('nan') if x is None else x for x in r['features']] for r in rows], dtype=float)


def _ready(rows, minimum, min_families=5):
    return len(rows) >= minimum and len({r['outcome'] for r in rows}) == 2 and len({r['family'] for r in rows}) >= min_families


def _precision(rows, scores, k):
    ranked = sorted(range(len(rows)), key=lambda i: (-scores[i], rows[i]['species'], rows[i]['category']))[:k]
    return mean(rows[i]['outcome'] for i in ranked) if ranked else None


def _ranking_metrics(rows, score_draws, k, bootstrap, seed, row_draws=None):
    scores = [mean(draw[i] for draw in score_draws) for i in range(len(rows))]
    row_draws = row_draws or [rows]
    baseline = {'model': scores, 'claim_count': [mean(draw[i]['features'][0] for draw in row_draws) for i in range(len(rows))]}
    effort_indices = [i for i, r in enumerate(rows) if r['effort'] is not None]
    families = sorted({r['family'] for r in rows})
    rng = random.Random(seed)
    result = {}
    for name in ('model', 'claim_count', 'famous_plant'):
        indices = effort_indices if name == 'famous_plant' else list(range(len(rows)))
        rs = [rows[i] for i in indices]
        ss = [rows[i]['effort'] for i in indices] if name == 'famous_plant' else [baseline[name][i] for i in indices]
        values = []
        for _ in range(bootstrap):
            sampled = rng.choices(families, k=len(families))
            ii = [i for family in sampled for i in indices if rows[i]['family'] == family]
            if ii:
                draw_index = rng.randrange(len(score_draws))
                draw = score_draws[draw_index] if name == 'model' else ([r['features'][0] for r in row_draws[draw_index % len(row_draws)]] if name == 'claim_count' else None)
                bs = [draw[i] if draw is not None else (rows[i]['effort'] if name == 'famous_plant' else baseline[name][i]) for i in ii]
                values.append(_precision([rows[i] for i in ii], bs, k))
        result[name] = {'precision_at_k': _precision(rs, ss, k), 'k': min(k, len(rs)), 'n': len(rs),
                        'ci95': [_percentile(values,.025), _percentile(values,.975)]
                        if bootstrap >= 100 and len(families) >= 5 and len(values) == bootstrap else None}
    comparisons={}
    for name in ('claim_count','famous_plant'):
        indices=effort_indices if name=='famous_plant' else list(range(len(rows)))
        values=[]
        for _ in range(bootstrap):
            sampled=rng.choices(families,k=len(families))
            ii=[i for family in sampled for i in indices if rows[i]['family']==family]
            if not ii:continue
            draw_index=rng.randrange(len(score_draws))
            rs=[rows[i] for i in ii]
            model_score=[score_draws[draw_index][i] for i in ii]
            other=[rows[i]['effort'] if name=='famous_plant' else row_draws[draw_index % len(row_draws)][i]['features'][0] for i in ii]
            values.append(_precision(rs,model_score,k)-_precision(rs,other,k))
        rs=[rows[i] for i in indices]
        ms=[scores[i] for i in indices]
        bs=[rows[i]['effort'] if name=='famous_plant' else baseline[name][i] for i in indices]
        comparisons[name]={'model_minus_baseline':_precision(rs,ms,k)-_precision(rs,bs,k) if rs else None,
                           'ci95':[_percentile(values,.025),_percentile(values,.975)] if bootstrap>=100 and len(families)>=5 and len(values)==bootstrap else None,
                           'n':len(indices)}
    result['paired_differences']=comparisons
    return result


def _matched_benchmarks(rows, scores, k, bootstrap, seed):
    """Match top model-ranked claimed pairs against each tested unclaimed null."""
    families = {r['species']: r['family'] for r in rows}
    efforts = {r['species']: r['effort'] for r in rows if r['effort'] is not None}
    by_pair = {(r['species'],r['category']): r for r in rows}
    all_claims = {p for p,r in by_pair.items() if r['claimed']}
    ranked = sorted(range(len(rows)), key=lambda i: (-scores[i], rows[i]['species'],rows[i]['category']))
    # Preserve ranking top-k explicitly, then match without replacement.
    top_claims = set([(rows[i]['species'],rows[i]['category']) for i in ranked if rows[i]['claimed']][:k])
    cohort = {p:r for p,r in by_pair.items() if p not in all_claims or p in top_claims}
    result = {}
    for method in ('within_species','within_family','research_effort'):
        matches, _ = _matches(cohort, all_claims, families, efforts, method, .5)
        target = [by_pair[a] for a,b in matches]
        control = [by_pair[b] for a,b in matches]
        fams = sorted({r['family'] for r in target+control})
        rng=random.Random(seed)
        draws=[]
        differences=[]
        for _ in range(bootstrap):
            weights=Counter(rng.choices(fams,k=len(fams))) if fams else {}
            den=sum(weights[r['family']] for r in control)
            den_target=sum(weights[r['family']] for r in target)
            if den:
                control_rate=sum(weights[r['family']]*r['outcome'] for r in control)/den
                draws.append(control_rate)
                if den_target:
                    differences.append(sum(weights[r['family']]*r['outcome'] for r in target)/den_target-control_rate)
        result[method]={'matched_pairs':len(matches),'model_top_claimed_precision':mean(r['outcome'] for r in target) if target else None,
                        'control_precision':mean(r['outcome'] for r in control) if control else None,
                        'control_ci95':[_percentile(draws,.025),_percentile(draws,.975)] if len(fams)>=5 and bootstrap>=100 and len(draws)==bootstrap else None,
                        'precision_difference':(mean(r['outcome'] for r in target)-mean(r['outcome'] for r in control)) if target else None,
                        'difference_ci95':[_percentile(differences,.025),_percentile(differences,.975)] if len(fams)>=5 and bootstrap>=100 and len(differences)==bootstrap else None,
                        'interpretation':'Matched subset of model top-k claimed targets; not the full ranking cohort.'}
    return result



def _matched_ensemble(row_draws, score_draws, k, bootstrap, seed):
    draws=[_matched_benchmarks(rows,scores,k,bootstrap,seed+i) for i,(rows,scores) in enumerate(zip(row_draws,score_draws))]
    result={}
    for method in ('within_species','within_family','research_effort'):
        values=[d[method] for d in draws]
        ready=all(v['control_precision'] is not None for v in values)
        result[method]={'mean_matched_pairs':mean(v['matched_pairs'] for v in values),
                        'model_top_claimed_precision':mean(v['model_top_claimed_precision'] for v in values) if ready else None,
                        'control_precision':mean(v['control_precision'] for v in values) if ready else None,
                        'control_ci95':[min(v['control_ci95'][0] for v in values),max(v['control_ci95'][1] for v in values)]
                        if all(v['control_ci95'] is not None for v in values) else None,
                        'precision_difference':mean(v['precision_difference'] for v in values) if ready else None,
                        'difference_ci95':[min(v['difference_ci95'][0] for v in values),max(v['difference_ci95'][1] for v in values)] if all(v['difference_ci95'] is not None for v in values) else None,
                        'ci_method':'Envelope of family-bootstrap intervals over identity imputations; exploratory.',
                        'interpretation':'Matched subset of model top-k claimed targets; not the full ranking cohort.'}
    return result

def fit_temporal(data, train_freeze=1900, calibration_freeze=1950, evaluation_freeze=1980,
                 follow_up=20, ensembles=10, seed=42, bootstrap=300, top_k=10, min_rows=30):
    validate_dataset(data)
    if follow_up < 1 or train_freeze+follow_up > calibration_freeze or calibration_freeze+follow_up > evaluation_freeze:
        raise ValueError('Training/calibration/evaluation outcome windows must not overlap and labels must mature before later freezes.')
    if ensembles < 2 or min_rows < 10 or bootstrap < 0 or top_k < 1:
        raise ValueError('Need >=2 ensemble fits, min_rows>=10, bootstrap>=0 and top_k>=1.')
    config = dict(train_freeze=train_freeze,calibration_freeze=calibration_freeze,evaluation_freeze=evaluation_freeze,
                  follow_up=follow_up,ensembles=ensembles,seed=seed,features=FEATURES)
    base={'schema_version':1,'config':config,'estimand':ESTIMAND.replace('20',str(follow_up)),
          'limitations':['Probability is conditional on first testing and indexed publication, not unconditional efficacy or probability of testing.',
                         'Ensemble spread is not a frequentist confidence interval; held-out population shift remains possible.',
                         'No random train/test split; fixed hyperparameters; calibration uses only the middle calendar window.']}
    if evaluation_freeze+follow_up > data['observation_end']:
        return dict(base,status='pending',reason='Evaluation labels have not completed follow-up.')
    counts={}
    for name,t in [('train',train_freeze),('calibration',calibration_freeze),('evaluation',evaluation_freeze)]:
        rows=snapshot(data,t,seed,follow_up)
        counts[name]=len(rows)
        if not _ready(rows,min_rows):
            return dict(base,status='pending',reason=f'{name} needs >= {min_rows} rows, both outcomes and >=5 families.',counts=counts)
    try:
        import lightgbm as lgb
        import numpy as np
    except (ImportError,OSError) as exc:
        return dict(base,status='pending',reason='Optional LightGBM runtime unavailable.',detail=str(exc),counts=counts)
    models,calibrators,score_draws,evaluation_draws=[],[],[],[]
    rng=random.Random(seed)
    for j in range(ensembles):
        train=snapshot(data,train_freeze,seed+j,follow_up)
        cal=snapshot(data,calibration_freeze,seed+j,follow_up)
        test=snapshot(data,evaluation_freeze,seed+j,follow_up)
        fams=sorted({r['family'] for r in train})
        train_sample=[r for family in rng.choices(fams,k=len(fams)) for r in train if r['family']==family]
        if len({r['outcome'] for r in train_sample}) < 2:
            return dict(base,status='pending',reason='A family-bootstrap training draw lacked both classes; increase corpus diversity.',counts=counts)
        dataset=lgb.Dataset(_matrix(train_sample,np),label=[r['outcome'] for r in train_sample],feature_name=FEATURES)
        model=lgb.train({'objective':'binary','verbosity':-1,'seed':seed+j,'num_threads':1,
                         'deterministic':True,'force_col_wise':True,'num_leaves':7,'min_data_in_leaf':5,
                         'learning_rate':.05,'lambda_l2':1.},dataset,num_boost_round=60)
        calibrator=_calibrate_fit(model.predict(_matrix(cal,np)),[r['outcome'] for r in cal])
        scores=_apply(model.predict(_matrix(test,np)),calibrator)
        models.append(model.model_to_string())
        calibrators.append(calibrator)
        score_draws.append(scores)
        evaluation_draws.append(test)
    rows=evaluation_draws[0]
    predictions=[mean(s[i] for s in score_draws) for i in range(len(rows))]
    evaluation={'n':len(rows),'reliability':calibration(predictions,[r['outcome'] for r in rows]),
                'brier_score':mean((p-r['outcome'])**2 for p,r in zip(predictions,rows)),
                'ranking':_ranking_metrics(rows,score_draws,top_k,bootstrap,seed,evaluation_draws),
                'matched_benchmarks':_matched_ensemble(evaluation_draws,score_draws,top_k,bootstrap,seed),
                'predictions':[{'species':r['species'],'category':r['category'],'outcome':r['outcome'],
                                'probability':p} for r,p in zip(rows,predictions)]}
    return dict(base,status='fitted',counts=counts,model_strings=models,calibrators=calibrators,evaluation=evaluation,
                fitted_through_year=calibration_freeze+follow_up,lightgbm_version=lgb.__version__)


def rank_forward(data, artifact, as_of=2026, top_k=20):
    validate_dataset(data)
    base={'as_of':as_of,'estimand':artifact.get('estimand',ESTIMAND),
          'framing':'Research prioritisation for laboratory testing, not medical advice; no prediction here is an established effect.'}
    if artifact.get('status')!='fitted':
        return dict(base,status='pending',reason='A temporally trained and calibrated model is required.',leads=[])
    if as_of < artifact['fitted_through_year'] or as_of > data['observation_end']:
        raise ValueError('Forward as_of must follow all calibration labels and lie within observed coverage.')
    taxa={r['species']:r for r in data['taxa']}
    coverage_rows = data.get('test_coverage', [])
    if not coverage_rows and isinstance(data.get('coverage'), dict):
        coverage_rows = data['coverage'].get('pairs', [])
    coverage={(r['species'],r['category']) for r in coverage_rows if r.get('complete') is True and r.get('through_year',0)>=as_of}
    tested={(r['species'],r['category']) for r in data['ledger'] if r['tested_year']<=as_of}
    claimed=set()
    for c in data['claims']:
        if c['year']<=as_of and c['identity_available_year']<=as_of:
            claimed.update((x['species'],c['category']) for x in c['candidates'] if x['probability']>0)
    eligible=[p for p in claimed-tested if p in coverage and {'balkan','mediterranean'} & set(taxa[p[0]].get('regions',[])) and taxa[p[0]].get('hazard_trail')]
    if not eligible:
        return dict(base,status='pending',reason='No untested claimed pairs with complete search coverage, regional provenance and hazard trail.',leads=[])
    try:
        import lightgbm as lgb
        import numpy as np
    except (ImportError,OSError) as exc:
        return dict(base,status='pending',reason='Optional LightGBM runtime unavailable.',detail=str(exc),leads=[])
    seed=artifact['config']['seed']
    draws=[]
    for i,(text,cal) in enumerate(zip(artifact['model_strings'],artifact['calibrators'])):
        rows=snapshot(data,as_of,seed+i,candidates=eligible)
        draws.append(_apply(lgb.Booster(model_str=text).predict(_matrix(rows,np)),cal))
    leads=[]
    for j,row in enumerate(rows):
        values=[draw[j] for draw in draws]
        # Include imputation draws in which this candidate has no claim; this
        # avoids conditioning on the favorable identity assignment.
        leads.append({'species':row['species'],'category':row['category'],'probability_conditional_on_testing':mean(values),
                      'ensemble_interval95':[_percentile(values,.025),_percentile(values,.975)],
                      'interval_kind':'identity + family-bootstrap fit ensemble spread; not confidence interval',
                      'testing_status':'No relevant testing found within documented complete search coverage.',
                      'hazard_trail':taxa[row['species']]['hazard_trail']})
    return dict(base,status='ranked',leads=sorted(leads,key=lambda x:(-x['probability_conditional_on_testing'],x['species'],x['category']))[:top_k])


def main():
    p=argparse.ArgumentParser(description='Calendar-separated optional LightGBM ranker')
    p.add_argument('dataset',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model',type=Path);p.add_argument('--forward',action='store_true');p.add_argument('--as-of',type=int,default=2026)
    p.add_argument('--train-freeze',type=int,default=1900);p.add_argument('--calibration-freeze',type=int,default=1950)
    p.add_argument('--evaluation-freeze',type=int,default=1980);p.add_argument('--ensembles',type=int,default=10)
    args=p.parse_args();data=json.loads(args.dataset.read_text())
    if args.forward:
        if not args.model:p.error('--forward requires --model')
        result=rank_forward(data,json.loads(args.model.read_text()),as_of=args.as_of)
    else:
        result=fit_temporal(data,train_freeze=args.train_freeze,calibration_freeze=args.calibration_freeze,
                            evaluation_freeze=args.evaluation_freeze,ensembles=args.ensembles)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
