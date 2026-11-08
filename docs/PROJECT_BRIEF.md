# ANTIKYTHERA: a 2,000-year backtest of Mediterranean medicine

Paste this whole file into a fresh Claude Code session as the project bible. Every number below that comes from a source has its URL next to it. Anything marked VERIFY has to be confirmed before it goes on a slide.

---

## 0. Pitch (memorise it)

> "For 2,000 years, Mediterranean medicine wrote down which plant treats what. Nobody ever checked, across the whole record and against chance, whether those claims beat a coin flip once you account for scientists simply studying the famous plants. We froze the record at every century, let science happen, and scored the past. Then we pointed the same machine at the plants nobody has tested yet."

The one headline number: **relative confirmation rate of traditional claims versus matched unclaimed controls, with a 95% CI, by era layer** (Dioscorides → Byzantine → Renaissance → modern Balkan folk).

Track: **T1 Traditional Knowledge Mining**. The track text asks you to "link ancient knowledge to modern pharmacology" and map plant names across eras; this does both.
Awards to stack: **Best Scientific Rigor, Best AI Solution, Most Innovative Application** ("unexpected real-world problem"). Best Community Impact is a weak maybe.

---

## 1. Why this beats every earlier idea

- **It is ETHCSTWIN's own stated goal, delivered honestly.** The project promises two things: AI for data collection from manuscripts and folklore, and AI to predict promising Balkan and Mediterranean plant materials. Antikythera builds both, then makes the second prove itself against history.
- **The closest prior work is manual and covers one indication with no null.** Yarnell & Touwaide 2019 took Dioscorides' 105 diuretic plants and found 56 of the 67 studied genera confirmed (83.6%), with 38 never studied. They report no baseline: how many random plants would also "confirm" as diuretic? https://pubmed.ncbi.nlm.nih.gov/30403493/
- **The corpus problem is solved but locked.** Staub, Casu & Leonti 2016 hand-extracted 5,314 uses of 536 taxa from Dioscorides/Mattioli 1568 and said the text had "never been systematically assessed". Their full text is restricted. https://pubmed.ncbi.nlm.nih.gov/27444350/ , https://iris.unica.it/handle/11584/185752
- **Plant-level ML exists, but only with random cross-validation.** Kew 2023 used random CV on 282 species, with no temporal holdout. https://pmc.ncbi.nlm.nih.gov/articles/PMC10248027/
- **The one temporal-split repo does something different.** EthnoEvidence-Temporal-Audit ranks targets for TCM formulas and explicitly makes "no claim of predictive performance". https://github.com/xkrn321/EthnoEvidence-Temporal-Audit
- **The known confounder is research effort.** Souza 2018 shows that plants with more uses get more research. Antikythera's nulls are built to kill exactly this. https://pmc.ncbi.nlm.nih.gov/articles/PMC6019821
- **Real tension makes the result non-trivial.** Applequist 2017 found that traditional antimalarial use correlated poorly with bioassay results. https://pmc.ncbi.nlm.nih.gov/articles/PMC5677511 Gyllenhaal 2012's verdict flips with the counting unit (see the research notes). Leonti 2009 argues that Sardinian and Sicilian folk medicine is "De Materia Medica revisited", so uses are not independent. https://pubmed.ncbi.nlm.nih.gov/19038321/

Either outcome is a headline. If tradition beats the matched nulls, ETHCSTWIN's thesis gets its first quantified effect size. If it does not, that is the most rigorous negative result in the field. **Do not predict the answer in the pitch.**

---

## 2. Legends panel (demo gold: case studies, not evidence)

For each case, freeze the record the year before discovery and show where the ranker would have placed the plant for that indication.

| Case | Traditional trail | Discovery | Freeze | Source |
|---|---|---|---|---|
| Colchicum → gout | Dioscorides lists colchicum only as a poison. Byzantine physicians (Jacobus Psychrestes 5th c., Alexander of Tralles 6th c.) use "hermodactyl" for podagra | Colchicine isolated 1820 (VERIFY date) | 1800 | https://pubmed.ncbi.nlm.nih.gov/30557131/ ; https://mjrheum.org/june-2017/newsid792/76/showfulltext792/1 |
| Galanthus → cognition/nerve | Balkan folk use for "nerve" problems; Dioscorides' "moly" is possibly the snowdrop (contested identity) | Isolated by Paskov's team in Bulgaria, 1956; later developed for Alzheimer's | 1950 | https://www.mcgill.ca/oss/article/medical-history/odysseus-snowdrop-odyssey ; Heinrich & Teoh 2004 J Ethnopharmacol 92:147 |
| Galega → diabetes symptoms | Medieval European folk use; Hill 1772 for thirst and frequent urination | Guanidine lowers glucose 1918; metformin 1957 | 1900 | https://www.doi.org/10.1007/S00125-017-4318-Z |
| Papaver → pain | Dioscorides | Morphine 1804 (VERIFY) | 1800 | sanity check, should hit |
| **Honest miss:** Taxus → cancer | Texts treat yew as a poison | Found by the NCI random plant screen (bark collected 1962) | 1960 | https://stacks.cdc.gov/view/cdc/29914/cdc_29914_DS1.pdf |
| **Right plant, wrong reason:** Catharanthus | Folk use for diabetes; no hypoglycaemic effect confirmed | Anticancer vinca alkaloids found by accident, 1950s | 1950 | https://edu.rsc.org/feature/africas-gift-to-the-world/2000064.article |

The story beat for Bouras-Vallianatos (his current ETHCSTWIN work is translating and commenting on Alexander of Tralles' *Therapeutics*): **Dioscorides alone ranks Colchicum low for joint disease; add the Byzantine layer and it jumps.** This is the era-ablation result in miniature. VERIFY it on your own pipeline before claiming it; if it doesn't jump, show that honestly.

**Peril twin:** every lead carries its hazard trail. Colchicum is confused with wild garlic (Allium ursinum): ANSES recorded 28 such poisonings in France in 2020–22, including 2 deaths. https://www.anses.fr/en/content/confusion-between-autumn-crocus-and-wild-garlic-can-lead-fatal-poisoning
The machine that finds colchicine has to say out loud that colchicine kills.

---

## 3. Data (PD = public domain)

| Layer | Date | Source | Licence | Notes |
|---|---|---|---|---|
| Dioscorides | c. 60 CE | Berendes German translation, 1902 (archive.org) or Wellmann Greek edition 1906–14 | PD (Berendes d. 1914) VERIFY scan | Avoid Beck 2005 (copyright). Gunther/Goodyer 1934 is probably PD in the EU (Gunther d. 1940) but HathiTrust limits it in the US: avoid |
| Byzantine | 5th–7th c. | Paul of Aegina, Adams English translation 1844–47 (Book VII, simples); Alexander of Tralles, Puschmann 1878–79 Greek/German | PD VERIFY scans | Minimum: Paul of Aegina VII |
| Renaissance / early modern | 1653 | Culpeper's *Complete Herbal* (Project Gutenberg) | PD | English, easiest to extract |
| Modern Balkan folk | 1990–2026 | Supplementary tables of open-access Pieroni / Sõukand papers; EthnoBot Himara records if endpoint live | CC BY (per article) VERIFY | Each record dated by publication year |
| Identity backbone | n/a | WCVP via Catalogue of Life (CC BY); WFO | CC BY | MPNS licence unverified, so use it only for lookups and disclose |
| Confirmation evidence | dated | PubMed E-utilities (abstracts + year); ChEMBL document year | NCBI terms; ChEMBL CC BY-SA | Run from your own machine (the cloud sandbox proxy blocked NCBI) |
| Research-effort covariate | dated | PubMed hit count per species per year | n/a | Core of the null |
| Identity gold | n/a | Lardos et al. figshare labels | VERIFY licence | Calibrates the historical-name layer |

---

## 4. Pipeline

### 4.1 Claim extraction (ETHCSTWIN AI goal 1)
- Chunk each text by chapter. An LLM extracts `{plant_name_as_written, part, preparation, ailment_as_written, span_offsets}` with strict JSON output and the source span stored.
- **Indication harmonisation:** map ancient ailment strings ("dropsy", "podagra", "falling sickness") to ~12 organ-system categories (urinary, GI, skin/wound, respiratory, neuro/pain, joint/inflammation, cardiovascular, metabolic, gynaecological, infection, eye, antidote/poison). Do it as embedding nearest-neighbour plus LLM adjudication, scored against a 150-item hand-labelled gold set. This is Mehmet Can Ay's own research problem (semantic harmonisation, embeddings benchmarked against a gold standard), so say so.
- **Audit:** a stratified sample of 200 claims checked by hand. Report extraction precision and recall with Wilson CIs.
- **External check:** re-derive Yarnell & Touwaide's diuretic list from the Dioscorides layer and report the overlap. If the pipeline gets close to their 105 plants, that validates extraction.

### 4.2 Identity across eras (the old Taftótita, now a module)
- Each name resolves to a **distribution** over candidate species, never a single answer. Candidates come from WCVP/WFO synonymy, regional presence, and later-tradition continuity.
- Calibrate on the Lardos expert grades: report expected calibration error (ECE) and a reliability diagram.
- Showcase cards: **hermodactyl** (Colchicum autumnale vs C. variegatum vs other Colchicum candidates; see the debate at https://henriettes-herb.com/eclectic/pereira/hermodactylus.html) and **moly** (Galanthus nivalis? contested).
- Every downstream statistic is computed by **sampling identities from these distributions** (multiple imputation), so identity uncertainty widens the CIs instead of being hidden.

### 4.3 Dated confirmation ledger
- For each species × category pair: PubMed query on species name and synonyms × category MeSH terms × pharmacology filter. Store all PMIDs with year.
- An LLM grades each abstract into `{supports, refutes, irrelevant}` × evidence tier `{in vitro, in vivo, clinical}`. Hand-audit 300 abstracts and report grader precision with CI.
- **Label:** `confirmed_year` = first year with at least one in-vivo or clinical "supports" paper. Run a sensitivity analysis with in vitro allowed.
- Store `tested_year` (first relevant paper of any verdict) and `refuted`.

### 4.4 Time machine (ETHCSTWIN AI goal 2, honestly)
- Freeze years T ∈ {1900, 1950, 1980, 2000, 2010}. At T the model sees only claims dated ≤ T and evidence dated ≤ T.
- **Primary estimand, a conditional comparison:** among species × category pairs first tested after T, compare P(confirmed | traditionally claimed by T) with P(confirmed | not claimed).
- **Matched controls (the core of the rigour):**
  1. **Within-species:** the same species' unclaimed categories. This controls plant chemistry and species-level research effort.
  2. **Within-family:** the same category in a confamilial species without the claim. This is the phylogeny null.
  3. **Research-effort-matched:** species with similar PubMed counts before T. This is the Souza null.
  4. **Famous plant:** a ranking by pre-T publication volume alone.
- **Report:** risk ratio with 95% cluster-bootstrap CI (clustered by plant family) over identity imputations, for each era layer and each category.
- **Era ablation:** Dioscorides only → + Byzantine → + Culpeper → + Balkan folk. Does each layer add lift? This is the Bouras-Vallianatos slide.
- **Lineage correction:** flag a later-layer claim as "inherited" when the same species-category pair appears in an earlier layer. Score "novel in layer" claims separately. This answers Leonti's "De Materia Medica revisited" problem.
- **Ranker:** LightGBM on features as of T (claim count, number of independent layers, inherited flag, family confirmation rate as of T, pre-T research effort). Report precision@k against all four nulls, with bootstrap CIs and a reliability diagram. Never use a random split.
- **Publication-bias sensitivity:** repeat with `refuted` counted, and report how far the effect must shrink under a plausible file-drawer rate before the CI crosses 1.

### 4.5 Forward shortlist (2026)
- Species × category pairs with a traditional claim, never tested, in Balkan/Mediterranean flora. Rank them by calibrated P(confirmed within 20 years), with interval and hazard trail.
- **Framing (hard rule):** "research prioritisation for laboratory testing, not medical advice; no prediction here is an established effect." This is the 38-untested-diuretics idea from Yarnell, generalised to the whole record.

### 4.6 UI (the 60-second demo)
- **Time slider, 60 CE → 2026.** A grid of plants × categories. Cells light up when a claim is written and turn green when science confirms them. A running counter shows the risk ratio against the matched null, with its CI band.
- **Legends rail:** click "Colchicine" and the slider jumps to 1800, showing the rank with and without the Byzantine layer.
- **Identity cards:** a probability bar per candidate species, sources listed.
- **Shortlist tab:** each lead shows its interval and a red hazard strip.
- Stack: FastAPI + Postgres (or DuckDB) + SvelteKit or React. Use a static JSON export for the hosted demo.

---

## 5. Validation summary (one slide)
- **Ground truth:** dated PubMed confirmations (LLM-graded, 300 checked by hand) and Lardos expert identity grades.
- **Splits that cannot leak:** temporal freeze; evidence and claims both cut at T; identity priors learned only from pre-T layers.
- **Nulls:** within-species, within-family, research-effort-matched, famous-plant.
- **Metrics:** risk ratio and precision@k with cluster-bootstrap 95% CI; ECE for identity; extraction and grading precision with Wilson CIs.
- **Ablations:** by era layer; inherited vs novel claims; in-vitro labels allowed or not.
- **Failure analysis:** the Taxus and Catharanthus misses; categories where tradition underperforms the null; extraction errors by language.

---

## 6. Deck (10 slides)
1. The question: does 2,000 years of written medicine beat chance?
2. Why nobody could answer it: manual single-indication studies (Yarnell 83.6% with no null), research-effort bias, inherited claims, uncertain plant identity.
3. Data: four era layers, all public domain, dated; numbers of claims, species and categories.
4. AI for collection: extraction and harmonisation, with audited precision; identity distributions (the hermodactyl card).
5. Time machine design: freeze, matched nulls, why it cannot leak.
6. **The number:** risk ratio by era layer with CIs.
7. Legends: colchicine (Byzantine lift), galantamine, metformin. Misses: taxol, vinca.
8. Forward shortlist with intervals and hazard strips (research prioritisation only).
9. Limitations: publication bias bound, translation layers, LLM grading error, identity uncertainty.
10. What ETHCSTWIN gets: an open benchmark plus a plug-in for the Ecosystem Excellence Aggregator; next step is testing the top 10 in IESP's extract library.

**Video (≤10 min):** a 0:00–1:00 cold open on the slider running from 60 CE to 2026, ending on the CI band. Then the slides. Close with the shortlist.

---

## 7. Repo
```
antikythera/
  data/raw/ (download scripts only, no copyrighted text)   data/derived/ (claims.parquet, ledger.parquet)
  extract/ (chunkers, LLM prompts, schemas)   identity/ (candidates, calibration)
  ledger/ (pubmed fetch, abstract grader)   timemachine/ (freeze, nulls, bootstrap, ranker)
  audit/ (gold sets + scoring notebooks)   app/ (api + web)
  REPORT.md (all numbers regenerated by `make report`)   DISCLOSURE.md (AI use, pre-existing code, licences, TK note)
```
Reproduce with `make all`. Seeded. Every figure on a slide comes from `make report`.

---

## 8. Judge lines
- **Bouras-Vallianatos:** "Identity stays a distribution, every claim keeps its source span, and inherited claims are scored separately. Does the Byzantine layer add anything Dioscorides didn't? Here is the measured answer."
- **Aligiannis:** "Twenty untested Balkan leads with calibrated odds, ready for your extract library, and each one carries its hazard trail."
- **Gunopulos:** "A temporal freeze with four nulls and cluster-bootstrap CIs. No random splits anywhere."
- **Cheilari:** "Confirmation means in-vivo or clinical evidence, graded and hand-audited. In-vitro-only results are a sensitivity analysis, never the headline."
- **Ay:** "Ancient-to-modern indication harmonisation, with embeddings benchmarked against a hand-labelled gold set, the same protocol as your harmonisation work."

---

## 9. Risks and fallbacks
- **PubMed rate limits:** get an NCBI API key; restrict to about 600 species × 12 categories; cache everything.
- **Byzantine scans unusable:** keep Paul of Aegina VII only, or drop the Byzantine layer and present colchicine as a hand-coded case with its source citation.
- **Extraction too slow:** run Dioscorides and Culpeper only; the headline number still stands.
- **Null wins (no lift):** that is the result. Reframe slide 6 as "tradition's apparent success is research effort", which is still a Best Scientific Rigor story.
- **Traditional-knowledge ethics:** historical texts are public domain. For modern Balkan records, use only published open-access data with attribution; no community-identifying detail goes into the shortlist.

---

## 10. Build order (assumes about 30 working hours to the 8 Nov 10:00 CET deadline)
1. (2h) Repo skeleton, data download scripts, category schema, gold-set templates.
2. (6h) Extraction on Culpeper, then Dioscorides; hand-audit while it runs.
3. (5h) Identity distributions plus calibration on the Lardos labels.
4. (6h) PubMed ledger plus grader; audit 300.
5. (5h) Time machine, nulls, bootstrap, era ablation, legends.
6. (4h) UI slider plus shortlist; static export.
7. (2h) Deck, video, Devpost text, DISCLOSURE.md.
Parallelise steps 2–4 across teammates.