"""A conservative baseline analysis; no empirical performance is bundled.

The estimand is conditional on first testing during a completely observed post-freeze
window. A missing ledger row is never treated as a negative experimental result.
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from statistics import mean

LAYERS = ('dioscorides', 'byzantine', 'renaissance', 'balkan')
METHODS = ('within_species', 'within_family', 'research_effort')


def _year(value, field):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f'{field} must be an integer year')


def validate_dataset(data):
    """Validate identifiers, dates, first events and normalized identity priors."""
    if not isinstance(data, dict):
        raise ValueError('dataset must be an object')
    for key in ('claims', 'ledger', 'taxa', 'effort'):
        if not isinstance(data.get(key), list):
            raise ValueError(f'{key} must be a list')
    _year(data.get('observation_end'), 'observation_end')
    taxa = {}
    for taxon in data['taxa']:
        species, family = taxon.get('species'), taxon.get('family')
        if not isinstance(species, str) or not species or not isinstance(family, str) or not family:
            raise ValueError('each taxon needs nonempty species and family')
        if species in taxa:
            raise ValueError('duplicate taxon: ' + species)
        taxa[species] = family
    seen, groups = set(), {}
    for claim in data['claims']:
        if not isinstance(claim.get('id'), str) or not claim['id'] or claim['id'] in seen:
            raise ValueError('claim id must be unique and nonempty')
        seen.add(claim['id'])
        _year(claim.get('year'), 'claim.year')
        if claim['year'] > data['observation_end']:
            raise ValueError('claim dated after observation_end')
        if not claim.get('category') or not claim.get('layer') or not claim.get('identity_group'):
            raise ValueError('claim needs category, layer, identity_group')
        candidates = claim.get('candidates')
        if not isinstance(candidates, list) or not candidates:
            raise ValueError('claim candidates must be a nonempty list')
        probs = []
        for c in candidates:
            if c.get('species') not in taxa:
                raise ValueError('candidate species missing from taxa')
            p = c.get('probability')
            if isinstance(p, bool) or not isinstance(p, (float, int)) or not math.isfinite(p) or p < 0:
                raise ValueError('candidate probabilities must be finite and nonnegative')
            probs.append(p)
        if len({c['species'] for c in candidates}) != len(candidates) or not math.isclose(sum(probs), 1., abs_tol=1e-8):
            raise ValueError('candidate distribution needs unique taxa and probabilities summing to one')
        prior_year = claim.get('identity_available_year')
        _year(prior_year, 'identity_available_year')
        signature = tuple(sorted((c['species'], c['probability']) for c in candidates))
        group = claim['identity_group']
        if group in groups and groups[group] != signature:
            raise ValueError('identity_group must share one distribution; version changed priors as separate groups')
        groups[group] = signature
    pairs = set()
    for row in data['ledger']:
        pair = (row.get('species'), row.get('category'))
        if pair[0] not in taxa or not pair[1] or pair in pairs:
            raise ValueError('ledger requires unique species/category and known taxa')
        pairs.add(pair)
        tested = row.get('tested_year')
        _year(tested, 'tested_year')
        if tested > data['observation_end']:
            raise ValueError('tested_year after observation_end')
        for field in ('confirmed_year', 'refuted_year', 'in_vitro_confirmed_year'):
            value = row.get(field)
            if value is not None:
                _year(value, field)
                if value < tested or value > data['observation_end']:
                    raise ValueError(field + ' must lie between tested_year and observation_end')
    effort_keys = set()
    for row in data['effort']:
        _year(row.get('year'), 'effort.year')
        key = (row.get('species'), row['year'])
        n = row.get('count')
        if key[0] not in taxa or key in effort_keys or isinstance(n, bool) or not isinstance(n, int) or n < 0:
            raise ValueError('effort needs known species, unique species/year, nonnegative integer count')
        effort_keys.add(key)
    return data


def wilson_interval(successes, total, z=1.959963984540054):
    if not isinstance(successes, int) or not isinstance(total, int) or total < 0 or not 0 <= successes <= total:
        raise ValueError('invalid binomial counts')
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + z*z / total
    center = (p + z*z / (2*total)) / denominator
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return [max(0., center-half), min(1., center+half)]


def calibration(predictions, outcomes, bins=10):
    """Equal-width reliability bins, ECE, and Wilson intervals. No fitted model."""
    if len(predictions) != len(outcomes) or bins < 1:
        raise ValueError('predictions/outcomes lengths must match and bins must be positive')
    buckets = [[] for _ in range(bins)]
    for p, y in zip(predictions, outcomes):
        if not math.isfinite(p) or not 0 <= p <= 1 or y not in (0, 1):
            raise ValueError('invalid probability or binary outcome')
        buckets[min(int(p*bins), bins-1)].append((p, y))
    rows, error = [], 0.
    for i, bucket in enumerate(buckets):
        if bucket:
            predicted, observed = mean(p for p, _ in bucket), mean(y for _, y in bucket)
            error += len(bucket) * abs(predicted-observed)
            rows.append({'lower': i/bins, 'upper': (i+1)/bins, 'n': len(bucket), 'predicted': predicted,
                         'observed': observed, 'observed_ci95': wilson_interval(sum(y for _, y in bucket), len(bucket))})
    return {'n': len(predictions), 'ece': error / len(predictions) if predictions else None, 'bins': rows}


def _claims_at(data, freeze, layers, rng):
    draws, pairs = {}, set()
    inherited, first_layer = {}, {}
    order = {name: i for i, name in enumerate(LAYERS)}
    claims = sorted(data['claims'], key=lambda c: (c['year'], order.get(c['layer'], 99), c['id']))
    for claim in claims:
        if claim['year'] > freeze or claim['identity_available_year'] > freeze:
            continue
        if layers is not None and claim['layer'] not in layers:
            continue
        group = claim['identity_group']
        if group not in draws:
            candidates = claim['candidates']
            draws[group] = rng.choices([c['species'] for c in candidates], [c['probability'] for c in candidates])[0]
        pair = (draws[group], claim['category'])
        inherited[claim['id']] = pair in first_layer and first_layer[pair] != claim['layer']
        first_layer.setdefault(pair, claim['layer'])
        pairs.add(pair)
    return pairs, inherited, first_layer


def _cohort(data, freeze, horizon, allow_in_vitro):
    result = {}
    for row in data['ledger']:
        if freeze < row['tested_year'] <= horizon:
            dates = [row.get('confirmed_year')]
            if allow_in_vitro:
                dates.append(row.get('in_vitro_confirmed_year'))
            result[(row['species'], row['category'])] = {
                'supports': any(d is not None and d <= horizon for d in dates),
                'refuted': row.get('refuted_year') is not None and row['refuted_year'] <= horizon,
            }
    return result


def _matches(cohort, claimed, families, efforts, method, caliper):
    targets = sorted(set(cohort) & claimed)
    controls = sorted(set(cohort) - claimed)
    matched = []
    # Controls are never treated as untested negatives. Matching is one-to-one
    # without replacement, deterministic and uses pre-freeze covariates only.
    used = set()
    for target in targets:
        options = []
        for control in controls:
            if control in used:
                continue
            if method == 'within_species' and target[0] != control[0]:
                continue
            if method == 'within_family' and (target[1] != control[1] or families[target[0]] != families[control[0]]):
                continue
            if method == 'research_effort':
                if target[1] != control[1] or target[0] not in efforts or control[0] not in efforts:
                    continue
                distance = abs(math.log1p(efforts[target[0]]) - math.log1p(efforts[control[0]]))
                if distance > caliper:
                    continue
            else:
                distance = 0.
            options.append((distance, control))
        if options:
            _, control = min(options)
            used.add(control)
            matched.append((target, control))
    return matched, len(targets)


def _risks(matches, cohort, families, weights=None, exclude_refuted=False):
    denominators, numerators = [0., 0.], [0., 0.]
    for match in matches:
        for arm, pair in enumerate(match):
            weight = weights.get(families[pair[0]], 0) if weights is not None else 1
            denominators[arm] += weight
            outcome = cohort[pair]['supports'] and not (exclude_refuted and cohort[pair]['refuted'])
            numerators[arm] += weight * outcome
    risks = [n/d if d else None for n, d in zip(numerators, denominators)]
    return risks


def _ratio(risks):
    a, b = risks
    if a is None or b is None or b == 0:
        return None
    return a/b


def _percentile(values, fraction):
    values = sorted(values)
    x = (len(values)-1)*fraction
    a = int(x)
    return values[a] + (values[min(a+1, len(values)-1)]-values[a])*(x-a)



def _rematched_ratio(cohort, claimed, families, efforts, method, caliper, rng, exclude_refuted):
    """Resample entire eligible families then re-establish one-to-one matches."""
    family_names=sorted({families[p[0]] for p in cohort})
    if not family_names:return None
    sampled=rng.choices(family_names,k=len(family_names))
    expanded, expanded_claimed, expanded_families, expanded_efforts = {}, set(), {}, {}
    for occurrence,family in enumerate(sampled):
        for pair,row in cohort.items():
            species,category=pair
            if families[species]!=family:continue
            # JSON gives an unambiguous internal identifier for cloned taxa.
            clone=repr((occurrence,species))
            p=(clone,category)
            expanded[p]=row
            expanded_families[clone]=family
            if species in efforts:expanded_efforts[clone]=efforts[species]
            if pair in claimed:expanded_claimed.add(p)
    matched,_=_matches(expanded,expanded_claimed,expanded_families,expanded_efforts,method,caliper)
    return _ratio(_risks(matched,expanded,expanded_families,exclude_refuted=exclude_refuted))

def _summarize(samples, cohort, families, method, targets, bootstrap, rng, exclude_refuted, rematch_contexts=None):
    risks = [_risks(matches, cohort, families, exclude_refuted=exclude_refuted) for matches in samples]
    finite = [r for r in risks if all(x is not None for x in r)]
    pooled = [mean(r[i] for r in finite) for i in (0, 1)] if finite else [None, None]
    estimates = []
    undefined = 0
    family_names = sorted({families[p[0]] for matches in samples for match in matches for p in match})
    if family_names:
        for _ in range(bootstrap):
            draw_index = rng.randrange(len(samples))
            if rematch_contexts is not None:
                raw_cohort, raw_claimed, raw_efforts, caliper = rematch_contexts[draw_index]
                r = _rematched_ratio(raw_cohort, raw_claimed, families, raw_efforts, method, caliper, rng, exclude_refuted)
            else:
                matches = samples[draw_index]
                weights = Counter(rng.choices(family_names, k=len(family_names)))
                r = _ratio(_risks(matches, cohort, families, weights, exclude_refuted))
            if r is None:
                undefined += 1
            else:
                estimates.append(r)
    ci = None
    # A percentile interval that silently discards undefined resamples would be
    # misleading. Suppress the interval if any replicate is undefined.
    if bootstrap >= 100 and len(family_names) >= 5 and undefined == 0 and len(estimates) == bootstrap:
        ci = [_percentile(estimates, .025), _percentile(estimates, .975)]
    warnings = []
    if not finite:
        warnings.append('No matched tested pairs; no effect estimate is available.')
    elif len(finite) != len(samples):
        warnings.append('Some identity imputations had no matched pairs; effect estimate suppressed rather than conditioning on match availability.')
        pooled = [None, None]
        ci = None
    if len(family_names) < 5:
        warnings.append('Fewer than five plant families; confidence interval suppressed.')
    if pooled[1] == 0:
        warnings.append('No confirmations in matched controls; risk ratio is undefined, not zero.')
    if undefined:
        warnings.append(f'{undefined}/{bootstrap} bootstrap draws had an undefined risk ratio.')
    if bootstrap < 100:
        warnings.append('Fewer than 100 bootstrap replicates; confidence interval suppressed.')
    if any(len(m) < 20 for m in samples):
        warnings.append('Fewer than 20 matched pairs in at least one identity draw; treat estimates as exploratory.')
    return {'method': method, 'risk_ratio': _ratio(pooled), 'ci95': ci,
            'claimed_confirmation_risk': pooled[0], 'control_confirmation_risk': pooled[1],
            'identity_draws_with_matches': len(finite),
            'mean_matched_pairs': mean(len(m) for m in samples), 'mean_eligible_claimed_pairs': mean(targets),
            'family_clusters': len(family_names), 'bootstrap_replicates': bootstrap,
            'undefined_bootstrap_replicates': undefined,
            'publication_bias_bound': ({'model': 'true RR = observed RR / differential positive-ascertainment factor',
                                        'factor_to_move_lower_ci_to_one': ci[0],
                                        'fractional_shrinkage_to_move_lower_ci_to_one': 1 - 1/ci[0]}
                                       if ci is not None and ci[0] > 1 else None),
            'warnings': warnings}


def analyze(data, freeze_year=2000, follow_up=20, seed=42, bootstrap=300,
            imputations=20, layers=None, effort_caliper=.5, allow_in_vitro=False,
            count_refuted_as_failure=False, category=None, novel_in_layer=None, top_k=10,
            resample_matching=False):
    """Compute matched temporal risks with family resampling over identity draws.

    No learned probability or clinical effect is inferred from an abstract count.
    count_refuted_as_failure makes a conflicting supports/refutes pair a failure.
    Missing effort is excluded from effort matching rather than imputed as zero.
    """
    validate_dataset(data)
    _year(freeze_year, 'freeze_year')
    if follow_up < 1 or bootstrap < 0 or imputations < 1 or effort_caliper < 0 or top_k < 1:
        raise ValueError('invalid analysis settings')
    horizon = freeze_year + follow_up
    base = {'freeze_year': freeze_year, 'follow_up_years': follow_up, 'horizon_year': horizon,
            'seed': seed, 'identity_imputations': imputations, 'layers': list(layers) if layers is not None else list(LAYERS),
            'category': category, 'novel_in_layer': novel_in_layer,
            'evidence_tiers': ['in_vivo', 'clinical'] + (['in_vitro'] if allow_in_vitro else []),
            'estimand': 'Confirmation by horizon, conditional on first testing after freeze and by horizon.',
            'ci_method': ('Percentile family-cluster bootstrap with rematching in each resample, pooled over identity imputations.' if resample_matching else 'Percentile family-cluster bootstrap of fixed matched observations, pooled over identity imputations.'),
            'limitations': ['Conditional on testing and indexed publication; does not estimate efficacy or remove publication bias.',
                            ('Matching uses category, taxonomy and pre-freeze effort and is refitted inside each family bootstrap.' if resample_matching else 'Fixed matching uncertainty is not resampled; matching uses only category, taxonomy, and pre-freeze effort.'),
                            'No calibrated forward probabilities: a validated temporal model has not been fitted.']}
    if horizon > data['observation_end']:
        return dict(base, status='pending', reason='Complete follow-up is unavailable at this freeze.', methods=[], ranking=None)
    cohort = _cohort(data, freeze_year, horizon, allow_in_vitro)
    if category is not None:
        cohort = {p: row for p, row in cohort.items() if p[1] == category}
    if not cohort:
        return dict(base, status='pending', reason='No species/category pairs first tested inside this window.', methods=[], ranking=None)
    families = {r['species']: r['family'] for r in data['taxa']}
    efforts, effort_seen = Counter(), set()
    for row in data['effort']:
        if row['year'] <= freeze_year:
            efforts[row['species']] += row['count']
            effort_seen.add(row['species'])
    efforts = {species: efforts[species] for species in effort_seen}
    rng = random.Random(seed)
    samples = {method: [] for method in METHODS}
    target_counts = {method: [] for method in METHODS}
    inheritance = []
    claim_sets = []
    rematch_contexts = []
    for _ in range(imputations):
        claimed, inherited, first_layer = _claims_at(data, freeze_year, layers, rng)
        inheritance.append(sum(inherited.values()))
        # Restrict targets to claims novel in this layer while keeping *all*
        # traditional claims out of the control pool.
        target_claims = claimed if novel_in_layer is None else {p for p in claimed if first_layer[p] == novel_in_layer}
        target_cohort = {p: row for p, row in cohort.items() if p not in claimed or p in target_claims}
        claim_sets.append(target_claims)
        rematch_contexts.append((target_cohort, claimed, efforts, effort_caliper))
        for method in METHODS:
            matches, n_targets = _matches(target_cohort, claimed, families, efforts, method, effort_caliper)
            samples[method].append(matches)
            target_counts[method].append(n_targets)
    methods = [_summarize(samples[m], cohort, families, m, target_counts[m], bootstrap, rng,
                          count_refuted_as_failure, rematch_contexts if resample_matching else None) for m in METHODS]
    # Transparent claim-indicator ranking, not a substitute for trained LightGBM.
    k = min(top_k, len(cohort))
    eligible_effort = [p for p in cohort if p[0] in efforts]
    famous = sorted(eligible_effort, key=lambda p: (-efforts[p[0]], p))[:k]
    def precision(pairs):
        return mean(int(cohort[p]['supports'] and not (count_refuted_as_failure and cohort[p]['refuted'])) for p in pairs) if pairs else None
    traditional = []
    for claimed in claim_sets:
        ranked = sorted(cohort, key=lambda p: (p not in claimed, p))[:k]
        traditional.append(precision(ranked))
    ranking = {'model': 'claim_indicator_only', 'tie_break': 'lexical species/category; exploratory baseline', 'k': k,
               'claim_indicator_precision_at_k': mean(traditional), 'famous_plant_precision_at_k': precision(famous),
               'famous_plant_n': len(famous), 'ci95': None,
               'status': 'baseline_only; calibrated temporal ranker and ranking bootstrap pending'}
    return dict(base, status='computed', eligible_tested_pairs=len(cohort),
                mean_inherited_claim_records=mean(inheritance), methods=methods, ranking=ranking)


def era_ablation(data, **kwargs):
    """Cumulative era layers, with later sources excluded at each freeze."""
    kwargs.pop('layers', None)
    return [{'added_layer': layer, 'analysis': analyze(data, layers=LAYERS[:i+1], **kwargs)} for i, layer in enumerate(LAYERS)]


def file_drawer_sensitivity(data, freeze_year=2000, follow_up=20, seed=42,
                            imputations=20, missing_negative_fractions=(0, .1, .25, .5, 1., 2.),
                            layers=None, category=None):
    """Assumption grid, not an estimated bias correction.

    A fraction f adds f hypothetical unreported negative pairs per observed
    pair to that arm's denominator, leaving its positive count unchanged.
    Arms vary independently. No intervals are manufactured for unseen studies.
    """
    validate_dataset(data)
    if any(not isinstance(f,(int,float)) or not math.isfinite(f) or f<0 for f in missing_negative_fractions):
        raise ValueError('Missing-negative fractions must be finite and nonnegative.')
    if imputations<1 or follow_up<1:
        raise ValueError('Positive imputations and follow_up required.')
    horizon=freeze_year+follow_up
    if horizon>data['observation_end']:
        return {'status':'pending','reason':'Complete follow-up unavailable.','methods':[]}
    cohort=_cohort(data,freeze_year,horizon,False)
    if category is not None:cohort={p:r for p,r in cohort.items() if p[1]==category}
    families={r['species']:r['family'] for r in data['taxa']}
    efforts=Counter();seen=set()
    for row in data['effort']:
        if row['year']<=freeze_year:
            efforts[row['species']]+=row['count'];seen.add(row['species'])
    efforts={s:efforts[s] for s in seen};rng=random.Random(seed)
    risks={m:[] for m in METHODS}
    for _ in range(imputations):
        claimed,_,_=_claims_at(data,freeze_year,layers,rng)
        for method in METHODS:
            matches,_=_matches(cohort,claimed,families,efforts,method,.5)
            risks[method].append(_risks(matches,cohort,families))
    result=[]
    for method,draws in risks.items():
        if any(any(r is None for r in draw) for draw in draws):
            result.append({'method':method,'status':'pending','grid':[]});continue
        a,b=[mean(r[i] for r in draws) for i in (0,1)]
        grid=[]
        for fc in missing_negative_fractions:
            for fn in missing_negative_fractions:
                adjusted=[a/(1+fc),b/(1+fn)]
                grid.append({'claimed_missing_negatives_per_observed_pair':fc,'control_missing_negatives_per_observed_pair':fn,
                             'adjusted_risk_ratio':_ratio(adjusted),'ci95':None})
        result.append({'method':method,'status':'assumptive','grid':grid})
    return {'status':'assumptive' if cohort else 'pending','freeze_year':freeze_year,'horizon_year':horizon,
            'model':'Add hypothetical unreported negative pairs to denominators; counts are assumed, not observed.',
            'limitations':'Does not estimate publication probability, missing positive studies, or uncertainty of assumed counts.',
            'methods':result}


def analysis_slices(data, freeze_year=2000, categories=None, **kwargs):
    """One explicit entry point for era, category and novel-in-layer results."""
    return {'era':era_ablation(data,freeze_year=freeze_year,**kwargs),
            'category':{c:analyze(data,freeze_year=freeze_year,category=c,**kwargs)
                        for c in (categories or sorted({r['category'] for r in data['ledger']}))},
            'novel_in_layer':{layer:analyze(data,freeze_year=freeze_year,novel_in_layer=layer,**kwargs) for layer in LAYERS}}
