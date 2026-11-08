# Antikythera

A local research workbench and private hosted observatory for a 2,000-year backtest of Mediterranean medicine.

The complete software workflow now covers source acquisition, span-grounded extraction, indication mapping, taxonomy candidates, dated literature retrieval, offline evidence cues, human review, identity calibration, temporal matched analyses, LightGBM training/evaluation, research prioritisation and reproducible exports. **The software build is complete; the empirical study still needs independent human audits.**

The bundled data contains 2,972 unreviewed claim proposals from four acquired source layers, 69 unique PubMed records across 75 species/category search matches, 30 annual research-effort observations and six modern taxonomy candidate sets. No proposal is automatically a validated historical claim or experimental outcome. There is no released headline effect size or laboratory recommendation.

## Start the local workspace

Python 3.11+ and Node 20.19+ or 22.12+ are required. The installed environment has been verified on this Mac.

```sh
make setup
make all
make serve
```

Open http://127.0.0.1:8000. The FastAPI service and React interface run together, including persistent review decisions. API documentation is at `/docs`. `make all` is offline: it uses cached sources where present, otherwise preserves the checksummed bundled proposal snapshot. Raw text and abstracts are not committed. Fetch them before reviewing source files locally.

The [private hosted snapshot](https://antikythera-medicine-observatory.rahulgunwani-study.chatgpt.site) requires ChatGPT sign-in. It supports exploration and review-batch export. Saved reviews and original abstracts remain in the local workspace.

## Workflow

1. **Inspect the corpus.** Use Corpus & review to search exact source spans, source headings, edition dates and table-row provenance. Four sources are acquired: the selected Culpeper edition, Berendes' Dioscorides translation, Paul of Aegina Book VII and a licensed Balkan medicinal table. Ancient dates remain unresolved when translator commentary or edition additions prevent a safe assignment.
2. **Review source annotations.** A person enters their name, decision, reason and explicit attestation. Historical dating, licence review and identity linkage have separate gates. A reviewed span alone cannot create an analysis claim.
3. **Resolve identities.** Review versioned taxonomy candidates, create an expert identity draft, assign a distribution with a source and prior-availability date, then review it separately. Numeric priors are not evidence of calibration. The dated temperature-calibration module requires disjoint expert-labelled groups and reports held-out reliability.
4. **Review evidence.** Retrieved study metadata and locally cached abstracts remain separate from supporting/refuting grades. Offline cue suggestions preserve exact offsets and can abstain. Compound-only papers cannot automatically confirm botanical preparations. Only reviewed original botanical studies enter the ledger.
5. **Complete independent audits.** `make sample-audit` prepares real-record samples. Add genuinely independent gold labels in `data/reviewed/audits.json` or use the local audit API. Empty templates and personal span reviews do not count as the 200-claim, 150-mapping or 300-abstract audits. Extraction recall requires complete-passage annotation.
6. **Rebuild.** Use Rebuild exports in the interface, or `make report`. Promotion includes only fully qualified reviewed records. The report runs matched nulls, era/category/novel-claim analyses, identity draws, family bootstrap, rematching and publication-bias assumptions. It also fits/calibrates/evaluates LightGBM when the mature calendar cohorts are sufficiently large.
7. **Inspect research results.** The atlas turns green only from the eligible dated evidence ledger. Backtest results show actual intervals, reliability and ranking comparisons when available. The shortlist requires documented testing coverage, regional provenance and a hazard trail. Scores condition on a future test occurring and are not clinical efficacy estimates.

## Collection and local models

```sh
make collect                         # explicit network acquisition, bounded and cached
make report                          # offline reviewed-data rebuild
make sample-audit                    # unfilled samples, never fabricated gold
make test                            # Python invariants and frontend data boundaries
```

The supplied literature sample is capped, not an exhaustive first-tested ledger. Expand the collector with explicit species, category and date settings before any completeness claim. Annual snapshots are not complete publication histories. NCBI bulk retrieval requires your actual `NCBI_EMAIL`; EuropePMC works without an invented contact address.

Offline extraction uses transparent language/indication rules and nearest-neighbour TF–IDF vectors. The conservative abstract baseline supplies cues and abstains when linkage is ambiguous. Neither has measured semantic accuracy until audited. No paid or remote model call happens in `make all`.

An optional locally running Ollama model can perform schema-constrained extraction, grading and indication adjudication. Configure `ANTIKYTHERA_MODEL_PROTOCOL=ollama`, `ANTIKYTHERA_MODEL_ENDPOINT=http://127.0.0.1:11434/api/chat` and your installed model name, then explicitly run:

```sh
.venv/bin/python -m scripts.model extract --enable-model --limit 1
.venv/bin/python -m scripts.model grade --enable-model --limit 1
.venv/bin/python -m scripts.model harmonise --enable-model --limit 1
make report
```

The provider also supports an explicit structured gateway. See `.env.example` and [the provider protocol](extract/README.md). No model weights or credentials are bundled. Model outputs remain unreviewed; original and corrected predictions stay separate during audit scoring.

## Review batches

Hosted review exports can be validated and applied locally:

```sh
.venv/bin/python -m scripts.import_reviews path/to/review.json
.venv/bin/python -m scripts.import_reviews path/to/review.json --apply
make report
```

Revisions prevent stale overwrites. Changed proposals invalidate their old review and audit state without erasing history. DuckDB holds local records, jobs and the append-only review trail. The service binds to loopback and rejects review requests from unrelated web origins. Use one local writer process.

## Outputs

- [REPORT.md](REPORT.md): regenerated counts, audit state and scientific results.
- `data/derived/claims.parquet`, `ledger.parquet`: typed eligible-cohort tables, with valid empty schemas when no records qualify.
- `data/derived/parquet/`: proposal/review exports with provenance.
- `data/derived/ranker.json`, `identity_calibration.json`, `shortlist.json`: fitted artifacts or explicit pending reasons.
- `app/web/public/workspace.json`: private hosted snapshot, excluding abstract text.
- [Ten-slide deck](docs/deck/Antikythera.pptx), [narrated demo](docs/video/Antikythera-demo.mp4), [transcript](docs/video/TRANSCRIPT.md) and [Devpost draft](docs/DEVPOST.md).

See [analysis methods](timemachine/README.md), [reviewed-input schemas](data/reviewed/README.md), [source and licence registry](data/raw/sources.json), [expert-reference caveat](data/external/identity_expert/README.md), and [disclosures](DISCLOSURE.md).

Research prioritisation for laboratory testing, not medical advice. No prediction here is an established effect. Illustrations are schematic and must not be used for plant identification.
