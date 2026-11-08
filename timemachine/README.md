# Temporal analysis contract

This module runs with Python 3.10+ and no external packages. It contains no empirical results. All test fixtures are invented and are used only to verify statistical behavior.

```sh
python3 -m timemachine data/derived/dataset.json --freeze 1900 --ablation --output data/derived/analysis.json
python3 -m unittest discover -s tests -p test_timemachine.py
```

Input JSON:

```json
{
  "observation_end": 2026,
  "taxa": [{"species": "Accepted species", "family": "Family"}],
  "claims": [{
    "id": "source:chapter:claim",
    "identity_group": "historical-name:source",
    "year": 1653,
    "identity_available_year": 1800,
    "layer": "renaissance",
    "category": "urinary",
    "candidates": [{"species": "Accepted species", "probability": 1.0}]
  }],
  "ledger": [{
    "species": "Accepted species", "category": "urinary",
    "tested_year": 1905, "confirmed_year": null, "refuted_year": null,
    "in_vitro_confirmed_year": null
  }],
  "effort": [{"species": "Accepted species", "year": 1899, "count": 0}]
}
```

The text above is a schema illustration, not plant data. Ledger `confirmed_year` must be based on a manually audited in-vivo or clinical supports verdict, not a PubMed hit, isolation of a compound, or discovery date. `tested_year` is the first relevant study of any verdict; a missing row is unknown. The calling pipeline must store PMID-level provenance and aggregate its dated ledger before analysis. This engine validates event order but cannot validate scientific interpretations.

`year` is the historical date; `identity_available_year` is when the candidate prior became available. The identity availability date is mandatory; omitted dates are rejected so a modern reconstruction cannot silently masquerade as knowledge available at the historical freeze. All claims in an identity group use the same candidate distribution, and the engine samples that group once per imputation. If priors are revised, version groups and analyze only the pre-freeze version upstream. Probabilities must sum to one and all taxa must have known families. Identity calibration is calculated separately with `calibration(predictions, outcomes)`, never inferred from the priors themselves.

At freeze T, only claims and identity priors available by T are eligible. The outcome window is `(T, T + follow_up]`, with 20 years by default. The *whole* window must end by `observation_end`; a 2010 freeze therefore remains pending until a completed 2030 window, rather than quietly using a shorter horizon. Eligible pairs are first tested inside the window. Previously tested pairs, future testing, and absent ledger records are excluded. This estimates confirmation conditional on testing, **not** the effect of an intervention or the probability that an untested plant works.

Each claimed pair is matched to one tested unclaimed control, without replacement, separately for:

- the same species, any unclaimed category;
- the same family and category;
- the same category with absolute log(1 + cumulative pre-freeze effort) distance at most 0.5.

Matching is deterministic and uses lexical ties, never later outcomes. Effort counts are annual totals; future counts are ignored. Missing effort is excluded from effort matching rather than treated as zero. Zero counts must be explicitly supplied by the collector. The caller is responsible for complete synonym-aware effort coverage and taxonomy provenance.

The point estimate is a ratio of mean imputation-specific arm risks. Bootstrap replicates choose an identity draw and then resample plant families, using the same family weights in both arms. Original family membership is retained for controls even when effort matching crosses families. Matching is fixed within each imputation, so intervals do not incorporate instability from refitting the match in resampled populations. This limitation is returned in the JSON. Intervals use the 2.5th and 97.5th percentiles. They are suppressed below five families, below 100 replicates, or when any replicate has an undefined ratio (undefined draws are never silently discarded). A zero-risk control arm returns `null`, never a made-up finite ratio. If any identity imputation has no matched pairs, the point estimate and interval are suppressed to avoid selection on match availability. Counts under 20 matched pairs carry a warning. These are conservative display guardrails, not guarantees of adequate power; the final analysis needs a statistician's review.

`era_ablation` adds `dioscorides`, `byzantine`, `renaissance`, then `balkan`. The year cut remains active in every layer. Repeated species/category claims are deduplicated; later records are flagged inherited. `novel_in_layer='byzantine'` restricts target claims to pairs first seen in that layer, while keeping other traditionally claimed pairs out of controls. `category='urinary'` restricts the entire cohort.

`allow_in_vitro=True` is a sensitivity run. `count_refuted_as_failure=True` treats a pair with both supports and refutes during the window as failure rather than ignoring conflicting evidence. `publication_bias_bound` gives an assumption-labelled differential positive-ascertainment tipping factor when a valid interval lies wholly above one. It is not a measured file-drawer rate; a plausible missing-study model still needs domain input.

The core `analyze()` ranking output implements only two transparent baselines: binary traditional claim and pre-freeze publication volume. It explicitly labels alphabetical ties and does not claim fitted LightGBM performance, ranking intervals, calibration, or forward probabilities. The optional `timemachine.ranker` described below implements learned fitting and ranking intervals. Real-data temporal validation, externally audited identity priors, and qualified prospective leads remain required for the full research protocol. `wilson_interval` and `calibration` support audited extraction/grading and reliability plots, with empty samples returning null.

## Optional learned temporal ranker

`timemachine.ranker` implements the learned model rather than emitting simulated predictions. Install the project's optional research dependencies and run with its virtual environment:

```sh
.venv/bin/python -m timemachine.ranker data/derived/dataset.json --output data/derived/ranker.json
.venv/bin/python -m timemachine.ranker data/derived/dataset.json --forward --model data/derived/ranker.json --output data/derived/shortlist.json
```

Default calendar windows are training 1900–1920, calibration 1950–1970, and held-out evaluation 1980–2000. The first-tested inclusion boundaries are `(freeze, freeze + 20]`; features are available at or before the freeze. Training labels must mature before the calibration freeze and calibration labels before the evaluation freeze. Overlapping windows raise a clear error, and incomplete evaluation follow-up returns pending. Thin windows also return pending: each window needs at least 30 tested pairs, both binary outcomes and five families by default. These are implementation guardrails, not a power calculation or an assurance of scientific validity.

Each fit samples historical identities consistently by group and bootstraps training families, then trains deterministic, single-threaded CPU LightGBM with fixed hyperparameters (60 rounds; seven leaves; L2 penalty 1). Features are claim count, number of layers, inherited flag, pre-freeze family confirmation proportion, and log(1 + pre-freeze species publication count). Missing effort and family outcomes remain missing values. An identity group's draw is derived from its seed and group ID, so adding future identity groups cannot perturb earlier draws. Later claims, identity priors, effort, testing, or confirmations cannot alter a frozen feature snapshot.

Sigmoid calibration is fitted on the separate middle calendar window using a ridge-regularized logistic mapping with a nonnegative slope. It never sees evaluation outcomes. The held-out output includes reliability bins/ECE, Brier score, precision@k and family-bootstrap intervals for the model, claim-count ranking and famous-plant ranking. Paired model-minus-baseline precision differences use shared family resamples. Ranking resamples repeat the ranking rather than holding top-k membership fixed. Famous-plant comparisons use only rows with known effort and disclose their smaller eligible sample. Matched-null benchmarks compare the model's top-k claimed targets with tested, unclaimed controls using the three matching rules. They disclose matched subset size; their intervals envelope family-bootstrap intervals across identity draws and are labeled exploratory. These are conditional-on-testing comparisons, not causal effects.

The fitted artifact is JSON containing LightGBM text model strings, numeric sigmoid parameters, calendar settings and held-out evaluation. No pickle is written or loaded. A synthetic-only integration test actually fits, serializes, reloads and predicts with LightGBM. No synthetic fixture enters report or application data.

Forward ranking requires a fitted model, a claim available by the ranking date, no testing dated by that date, explicit complete pair search coverage, a `balkan` or `mediterranean` regional tag, and a nonempty hazard trail:

```json
{
  "test_coverage": [
    {"species": "Accepted species", "category": "urinary", "complete": true, "through_year": 2026}
  ],
  "taxa": [
    {"species": "Accepted species", "family": "Family", "regions": ["mediterranean"], "hazard_trail": ["Reviewed hazard source and finding"]}
  ]
}
```

These are additional fields in the dataset, not a separate data file. A dataset-wide `coverage` dictionary may coexist; `coverage.pairs` is accepted as an alternate pair coverage list. No missing record is called untested without complete declared coverage. The output says **probability of indexed confirmation conditional on first testing within the next 20 years**. It does not estimate the probability a plant is tested, unconditional confirmation within 20 years, or clinical efficacy. Applying calibration from tested pairs to untested pairs relies on an unverified transportability assumption. Reported 95% ensemble ranges combine identity and training-family fit variation; they are explicitly **not confidence intervals**. All leads carry their hazard trail and the research-only framing.

The default empty reviewed dataset returns structured pending statuses from both fitting and forward ranking. Supply real reviewed longitudinal evidence to fit the model; there is no fallback fabricated model.

Official APIs were checked against [LightGBM train](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.train.html) and [Booster prediction/text persistence](https://lightgbm.readthedocs.io/en/stable/pythonapi/lightgbm.Booster.html), currently documenting 4.7.0. The tested local runtime is LightGBM 4.7.0.

## Rematching and publication-bias analyses

`analyze(..., resample_matching=True)` resamples entire eligible plant families, replicates their species/category records, and refits one-to-one matching inside each bootstrap draw. This includes matching instability that the default fixed-match bootstrap omits. The choice is returned in `ci_method` and limitations. Repeated claims, unseen ledger pairs and unknown effort follow the same rules in the resampled analysis.

`file_drawer_sensitivity(...)` varies assumed missing-negative pairs independently in the claimed and control arms. With fractions `(0, .1, .25, .5, 1, 2)`, it emits a 36-cell grid per null. Fraction `f` adds `f` hypothetical unreported negative pairs per observed pair, reducing the arm's observed risk by `1/(1+f)`. These are assumptions, not estimated missing-study counts; no confidence intervals are invented for unknown data. A separate lower-CI ascertainment tipping factor remains available on primary effects whose interval is wholly above one.

`analysis_slices(data, freeze_year=..., categories=[...], resample_matching=True)` returns cumulative era ablations, category analyses, and novel-in-layer analyses using the same dated cohort and null machinery.
