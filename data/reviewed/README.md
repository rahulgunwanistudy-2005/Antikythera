# Human-reviewed inputs

All five record files are empty JSON arrays at delivery. The coverage manifest explicitly states that no complete evidence search exists. Do not copy demo narratives into this folder as empirical records.

`claims.json`: extraction schema in `extract/claims.py`, plus `reviewed: true`, `reviewer`, `historical_date_reviewed: true`, `licence_reviewed: true`, `source_text_path` (project-relative), `source_sha256` (raw UTF-8 file hash), `source_url`, and `identity_id`. Preserve exact source_span and offsets. Separate original text from translator commentary and date later additions correctly.

`identities.json`: `{id, reviewed: true, reviewer, available_year, source_url, candidates: [{species_id, probability}]}`. Probabilities sum to 1. A prior's availability date is when its historically usable evidence was available, not when the claim was written. A shared identity ID enforces correlated sampling across uses. Do not manufacture numeric confidence from editorial uncertainty.

`taxa.json`: `{species_id, family, reviewed: true, backbone_version, source_url}`. Resolve accepted names and synonymy with licensed versioned backbone provenance.

`grades.json`: schema in `ledger/grades.py`, plus `reviewer`, `study_type: "original"` and `record_path` (project-relative) plus `record_sha256` for the retrieved abstract/metadata file. Mark `preparation_scope: "botanical"`, `"compound_only"`, or `"unclear"`. The ledger counts only reviewed botanical original studies. `reviewed` means an actual human decision, not an LLM assertion. Store independent model and gold decisions in audit material.

`effort.json`: `{species_id, year, count, query, synonym_version, coverage_reviewed: true}`. `count` is an annual publication count, not a present-day cumulative total. Zero requires a completed query. Missing coverage stays unknown.

`coverage.json`: the prespecified observation_end plus search/synonym/effort coverage declarations. Completing this manifest does not substitute for independent extraction, harmonisation, abstract-grading, and identity audits.

`python3 -m scripts.build_dataset` validates these inputs and writes the engine adapter. It rejects missing review, uncalibrated identities, changed source files, escaped paths and unreviewed historical dates. It cannot establish that a reviewer made a scientifically correct judgement. Independent audit and provenance inspection are still required.
