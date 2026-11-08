"""Fit one dated scalar temperature to expert-labelled identity distributions.

No expert labels are shipped. Explicit unresolved/other candidates are preserved;
this calibration cannot discover candidates missing from the input distribution.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from statistics import mean

EPSILON=1e-12


def _candidates(candidates):
    if not isinstance(candidates,list) or not candidates:
        raise ValueError('candidates must be a nonempty list')
    ids=[]
    for c in candidates:
        if not isinstance(c,dict) or not isinstance(c.get('species_id'),str) or not c['species_id']:
            raise ValueError('Every candidate needs a nonempty species_id, including any explicit unresolved/other option.')
        p=c.get('probability')
        if isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1:
            raise ValueError('Candidate probabilities must be finite and lie in [0,1].')
        ids.append(c['species_id'])
    if len(ids)!=len(set(ids)) or not math.isclose(sum(c['probability'] for c in candidates),1.,abs_tol=1e-8):
        raise ValueError('Candidates need unique IDs and probabilities summing to one.')
    return candidates


def _year(value):
    if isinstance(value,bool) or not isinstance(value,int):
        raise ValueError('Label availability/as_of must be an integer year.')
    return value


def _rows(rows):
    if not isinstance(rows,list):raise ValueError('Expert rows must be an explicit list.')
    groups=set()
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Each expert row must be an object.')
        group=row.get('group_id')
        if not isinstance(group,str) or not group or group in groups:
            raise ValueError('Each split requires unique nonempty group_id; aggregate repeated expert votes before fitting.')
        groups.add(group)
        _candidates(row.get('candidates'))
        if row.get('true_species_id') not in {c['species_id'] for c in row['candidates']}:
            raise ValueError('Expert truth must identify an existing candidate, including an explicit unresolved/other option when appropriate.')
        _year(row.get('label_available_year'))
    return groups


def _scaled(candidates,temperature,epsilon):
    logits=[math.log(max(epsilon,c['probability']))/temperature for c in candidates]
    maximum=max(logits)
    weights=[math.exp(x-maximum) for x in logits]
    total=sum(weights)
    return [w/total for w in weights]


def _nll(rows,temperature,epsilon):
    return mean(-math.log(max(epsilon,_scaled(r['candidates'],temperature,epsilon)[next(i for i,c in enumerate(r['candidates']) if c['species_id']==r['true_species_id'])])) for r in rows)


def _metrics(rows,temperature,epsilon,bins=10):
    buckets=[[] for _ in range(bins)]
    squared=[]
    for row in rows:
        probabilities=_scaled(row['candidates'],temperature,epsilon)
        # Lexical tie-break makes evaluation independent of input ordering.
        index=min(range(len(probabilities)),key=lambda i:(-probabilities[i],row['candidates'][i]['species_id']))
        p=probabilities[index]
        correct=int(row['candidates'][index]['species_id']==row['true_species_id'])
        buckets[min(int(p*bins),bins-1)].append((p,correct))
        squared.append(sum((v-int(c['species_id']==row['true_species_id']))**2 for c,v in zip(row['candidates'],probabilities)))
    result=[]
    error=0.
    for i,bucket in enumerate(buckets):
        confidence=mean(p for p,y in bucket) if bucket else None
        accuracy=mean(y for p,y in bucket) if bucket else None
        if bucket:error+=len(bucket)*abs(confidence-accuracy)
        result.append({'lower':i/bins,'upper':(i+1)/bins,'n':len(bucket),'confidence':confidence,'accuracy':accuracy})
    return {'n':len(rows),'ece':error/len(rows),'multiclass_brier':mean(squared),
            'negative_log_likelihood':_nll(rows,temperature,epsilon),'bins':result}


def fit_identity_calibration(calibration_rows,evaluation_rows,min_rows=20):
    """Fit on explicitly designated groups, report on disjoint expert groups.

    This is temperature scaling, not a historical-name resolver or evidence of
    expert accuracy. Calibration rows and evaluation rows are never randomized.
    """
    cal_groups=_rows(calibration_rows)
    eval_groups=_rows(evaluation_rows)
    if cal_groups & eval_groups:
        raise ValueError('Calibration and evaluation groups overlap; independent group-separated gold data required.')
    if isinstance(min_rows,bool) or not isinstance(min_rows,int) or min_rows<2:
        raise ValueError('min_rows must be an integer >=2.')
    base={'schema_version':1,'method':'scalar_temperature','epsilon':EPSILON,
          'zero_probability_policy':'Floor zero or below-epsilon probabilities to the explicit epsilon before log scaling, then renormalize. Other/unresolved candidates are preserved.',
          'counts':{'calibration':len(calibration_rows),'evaluation':len(evaluation_rows)},
          'split':'Caller-supplied disjoint expert identity groups; no random split.',
          'limitations':['Temperature rescales supplied probabilities; it cannot resolve missing candidates or prove taxonomic identity.',
                         'Top-label ECE depends on binning and sample size; a held-out improvement is not guaranteed.',
                         'Expert label quality and applicability across languages/eras require a separate audit.']}
    if len(calibration_rows)<min_rows or len(evaluation_rows)<min_rows:
        return dict(base,status='pending',reason=f'Each disjoint expert split needs at least {min_rows} reviewed identity groups.')
    if not any(max(c['probability'] for c in row['candidates'])-min(c['probability'] for c in row['candidates'])>1e-8 for row in calibration_rows):
        return dict(base,status='pending',reason='Calibration distributions contain no informative probability differences.')
    # Bounded one-dimensional search in log-temperature; coarse grid followed
    # by a deterministic golden-section refinement. No external ML dependency.
    lower,upper=math.log(.05),math.log(20.)
    grid=[lower+(upper-lower)*i/80 for i in range(81)]
    best=min(range(len(grid)),key=lambda i:_nll(calibration_rows,math.exp(grid[i]),EPSILON))
    a,b=grid[max(0,best-1)],grid[min(80,best+1)]
    phi=(1+math.sqrt(5))/2
    for _ in range(70):
        x=b-(b-a)/phi;y=a+(b-a)/phi
        if _nll(calibration_rows,math.exp(x),EPSILON)<_nll(calibration_rows,math.exp(y),EPSILON):b=y
        else:a=x
    temperature=math.exp((a+b)/2)
    fit_year=max(r['label_available_year'] for r in calibration_rows)
    eval_year=max(r['label_available_year'] for r in evaluation_rows)
    return dict(base,status='fitted',temperature=temperature,temperature_bounds=[.05,20.],
                fit_available_year=fit_year,evaluation_available_year=eval_year,available_year=max(fit_year,eval_year),
                calibration_groups=sorted(cal_groups),evaluation_groups=sorted(eval_groups),
                evaluation={'before':_metrics(evaluation_rows,1.,EPSILON),'after':_metrics(evaluation_rows,temperature,EPSILON)},
                calibration={'before_nll':_nll(calibration_rows,1.,EPSILON),'after_nll':_nll(calibration_rows,temperature,EPSILON)})


def apply_identity_calibration(candidates,artifact,as_of_year):
    """Return metadata-preserving candidate copies, never mutate the input."""
    _candidates(candidates);_year(as_of_year)
    if not isinstance(artifact,dict) or artifact.get('status')!='fitted' or artifact.get('method')!='scalar_temperature':
        raise ValueError('A fitted scalar-temperature identity artifact is required.')
    available=_year(artifact.get('available_year'))
    if as_of_year<available:
        raise ValueError(f'Identity calibrator unavailable before {available}; historical application at {as_of_year} would leak future expert labels.')
    temperature=artifact.get('temperature');epsilon=artifact.get('epsilon')
    if isinstance(temperature,bool) or not isinstance(temperature,(int,float)) or not math.isfinite(temperature) or not .05<=temperature<=20.:
        raise ValueError('Invalid fitted temperature.')
    if isinstance(epsilon,bool) or not isinstance(epsilon,(int,float)) or not math.isfinite(epsilon) or not 0<epsilon<1e-3:
        raise ValueError('Invalid calibration epsilon.')
    probabilities=_scaled(candidates,temperature,epsilon)
    return [dict(c,probability=p,calibrated_available_year=available) for c,p in zip(candidates,probabilities)]


def main():
    p=argparse.ArgumentParser(description='Fit dated identity temperature calibration from disjoint expert groups')
    p.add_argument('input',type=Path,help='JSON object with calibration_rows and evaluation_rows')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--min-rows',type=int,default=20)
    args=p.parse_args();data=json.loads(args.input.read_text())
    artifact=fit_identity_calibration(data.get('calibration_rows',[]),data.get('evaluation_rows',[]),args.min_rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
