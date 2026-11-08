# Identity uncertainty

`calibration.validate_candidates` accepts `{species_id, probability}` records only when all probabilities are finite, between zero and one, sum to one and species IDs are unique. Null/unreviewed seed candidates fail closed. Include an unresolved candidate if licensed expert review cannot identify a taxon; never silently renormalise away unresolved identity mass. Keep candidate generation, regional evidence, source layer, expert grades and availability dates so temporal freezes cannot use later synonym or historical-continuity evidence unnoticed.

`reliability` computes top-label ECE and reliability bins on paired confidence and binary correctness vectors. It does not estimate probabilities, perform taxonomy resolution, or establish calibration without a real gold set. Lardos label access/licence remains pending. Candidate distributions supplied to the analysis engine must be frozen as of the selected year.

## Dated expert calibration

`calibrate_prior.py` fits a single scalar temperature on explicitly designated expert identity groups and evaluates it on a separate, non-overlapping group list. It never randomizes the split or fabricates gold labels.

```sh
.venv/bin/python -m identity.calibrate_prior data/reviewed/identity_calibration.json --output data/derived/identity_calibration.json
```

Input is `{ "calibration_rows": [...], "evaluation_rows": [...] }`. Each row needs `group_id`, `label_available_year`, `true_species_id`, and `candidates: [{"species_id": "...", "probability": 0.7}, ...]`. Both arrays need at least 20 groups by default. Repeated groups within a split or overlap across splits are rejected; aggregate repeated expert votes before input. Uninformative uniform priors and empty/thin gold data return `status: pending`.

Candidates may include an explicit unresolved or other option such as `species_id: "__other__"`. It is preserved like every other candidate, including its metadata. Expert truth must refer to an existing candidate; a missing identity cannot silently disappear during scoring. The optimization floors zero or tiny probabilities to an explicit epsilon of `1e-12`, scales their logs by a temperature in `[0.05, 20]`, and renormalizes. A deterministic bounded search fits only the calibration rows' negative log likelihood. Held-out top-label reliability/ECE, multiclass Brier score and negative log likelihood are reported before and after scaling; improvement is not guaranteed.

`apply_identity_calibration(candidates, artifact, as_of_year)` returns transformed copies and preserves all candidate options. It requires a fitted artifact and refuses dates earlier than the maximum expert-label availability year across fitting and evaluation. `fit_available_year`, `evaluation_available_year`, and the conservative combined `available_year` are stored separately. Applying a modern expert calibration to an earlier historical freeze is prohibited. An empty optional input artifact must remain pending; no expert audit or calibrated probabilities are implied until real labels are supplied.
