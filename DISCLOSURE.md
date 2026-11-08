# Disclosure

## Software and AI use

This repository began empty. AI assistants generated the application, source adapters, statistical code, extraction/grading prompts, transparent offline baselines, schematic botanical illustrations, documentation, slides and narration text. The demonstration uses locally generated Apple Samantha speech. The original user brief is retained in `docs/PROJECT_BRIEF.md` as a specification, not evidence of completed research.

The build includes real, acquired source material and bibliographic records. The downloaded raw texts, original article XML, abstracts, private cache and DuckDB database remain local and ignored by Git. Public/static exports contain attributed source-derived proposals, bibliographic metadata, provenance and status, with no full abstract text. Generated source-span offsets are checked exactly, but that check does not establish semantic extraction accuracy.

The curated six-case catalogue is analysis-ineligible. The four-source corpus contains unreviewed proposals. The collected literature sample is capped and does not establish first-tested or never-tested status. Human-reviewed input files and independent gold audits remain empty at delivery. All synthetic outcome data used to exercise fitting and bootstrap routines stays in isolated tests.

## Local/offline processing

The user selected local/offline processing. Default builds do not make paid or remote model calls. Extraction uses deterministic English/German cue baselines, and harmonisation uses word/character TF–IDF cosine similarity. These are explicitly labelled baselines, with no measured semantic precision or recall. The offline abstract suggester keeps cue offsets, can abstain, and never creates a reviewed grade. Its current 75-record queue abstains on all verdicts while retaining provisional tier/scope cues.

Optional structured model processing supports a user-configured gateway or a separately installed local Ollama model. It requires an explicit enabled command. No model weights or private credentials are bundled. Model suggestions, corrected review decisions and independent gold labels are stored separately, so correcting a proposal cannot inflate the audit of its original prediction.

## Data and licences

The registry in `data/raw/sources.json` records source-specific edition, reuse and provenance metadata. The selected Culpeper edition is 1850 and includes later additions. Archive/Wellcome public-domain metadata was checked for the Berendes and Paul translation scans. Original ancient statements must still be separated from translator commentary, and unresolved historical dates remain null.

The selected Balkan article/table has its own recorded CC BY terms and attribution. Its public projection includes medicinal fields and omits community columns. No community-identifying details appear in the forward shortlist. Rights in traditional knowledge are not reduced to article copyright, and further collection should respect appropriate attribution, engagement and benefit sharing.

EuropePMC/PubMed access does not itself permit redistribution of all abstracts. Their text remains in the local cache. GBIF provides a disclosed, versioned modern-name candidate fallback. It does not substitute for WCVP/WFO historical name resolution. No MPNS or ChEMBL data is bundled. The exact WCVP/WFO backbone and optional ChEMBL integration remain additional data-source choices, rather than prerequisites to running the implemented collector.

The Lardos Figshare file 11 could not be retrieved and its licence remains unverified. The separately licensed CC BY 4.0 article Table 2 is included as a reference containing 141 candidate assessments across 50 names. Congruence grades remain native ordinal assessments, with null probabilities/truth labels. They are not independent identity gold or completed calibration. The external-reference manifest records this distinction and the retrieval blocker.

## Statistical limits

The temporal ranker and identity-temperature calibrator are implemented and have been exercised on synthetic integration fixtures. No real-data model is reported as fitted without eligible reviewed cohorts. Ranker probabilities condition on first testing in the following window and do not estimate whether testing will occur or whether a preparation is clinically effective.

Historical claim and prior-availability dates must precede the freeze. The primary effect conditions on later testing. Family bootstrap and identity draws quantify selected uncertainty, while a separate sensitivity refits matches after family resampling. Fixed-match estimates, publication selection, missing studies, OCR/translation mistakes and model error still limit interpretation. File-drawer grids are stated assumptions, not measured missing-study rates. Forward ensemble intervals are not confidence intervals for established medicinal effects.

The 2010 primary freeze cannot have a fully observed 20-year window until 2030. A shorter available-followup analysis is explicitly separate. No synthetic effect size or probability is substituted into the scientific report, presentation or shortlist.

## Reviews and storage

A person must supply their name, evidence note and explicit attestation for a review. Independent audit labels need a separate independence attestation. Revisions prevent stale overwrites. Proposal changes revoke old paired review/audit eligibility without erasing history. Acceptance of a source span cannot bypass historical dating, taxonomy, identity, licence and evidence gates.

The local FastAPI service binds to loopback and rejects review writes from unrelated web origins. It is a local research tool and is not configured as a public authenticated multi-user backend. The hosted Site is a private read-only snapshot. Raw abstracts and the local review database are not deployed.

## Code and dependencies

New application code is original to this build. Dependencies retain their own licences and are pinned in the Python/JavaScript lockfiles. No repository-wide licence is asserted over third-party text, data or traditional knowledge. A code redistribution licence remains the owner's choice. Fonts use Google Fonts with local system fallbacks; the app remains usable when font requests are unavailable.

## Medical framing

Research prioritisation for laboratory testing, not medical advice. No prediction here is an established effect. Do not use this project to identify, harvest, prepare, dose or consume plants. The hazard trail is not an exhaustive toxicology assessment. Botanical drawings are schematic illustrations, not identification aids.

## Review records (2026-11-08)

The records in `data/reviewed/` (21 claims, 4 identity distributions, 9 taxa, 40 evidence grades, 30 effort observations) were reviewed with AI assistance; each record names its reviewer. Notable calls: Dioscorides II.193 is *Cyclamen*, not *Colchicum*; the Cap. 84 gout line is Berendes' 1902 commentary and was excluded; English "periwinkle" is *Vinca*, not *Catharanthus*. The 200/150/300-item independent audits remain open, so the report status is `exploratory_analysis`.
