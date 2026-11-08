"""Identity distributions and audit metrics, without fabricated priors."""
import math, random

def validate_candidates(candidates):
    if not candidates: raise ValueError('At least one candidate required')
    names=[c['species_id'] for c in candidates]
    if len(names)!=len(set(names)): raise ValueError('Duplicate species')
    values=[c['probability'] for c in candidates]
    if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in values): raise ValueError('Unreviewed/null probability cannot enter analysis')
    if not math.isclose(sum(values),1,abs_tol=1e-8): raise ValueError('Probabilities must sum to one')
    return candidates

def sample(candidates, rng=None):
    validate_candidates(candidates); rng=rng or random.Random(1729)
    return rng.choices([c['species_id'] for c in candidates],[c['probability'] for c in candidates])[0]

def reliability(predictions, labels, bins=10):
    """Top-label ECE: labels are 0/1 correctness for the top candidate."""
    if len(predictions)!=len(labels) or not predictions: raise ValueError('Equal, nonempty audit vectors required')
    if type(bins) is not int or bins<1: raise ValueError('Positive bins required')
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in predictions): raise ValueError('Invalid confidence')
    if any(type(v) is not int or v not in (0,1) for v in labels): raise ValueError('Binary correctness required')
    rows=[];ece=0
    for i in range(bins):
        ix=[j for j,v in enumerate(predictions) if min(int(v*bins),bins-1)==i]
        confidence=sum(predictions[j] for j in ix)/len(ix) if ix else None
        accuracy=sum(labels[j] for j in ix)/len(ix) if ix else None
        if ix: ece+=len(ix)/len(labels)*abs(confidence-accuracy)
        rows.append({'lower':i/bins,'upper':(i+1)/bins,'n':len(ix),'confidence':confidence,'accuracy':accuracy})
    return {'n':len(labels),'ece':ece,'bins':rows}
