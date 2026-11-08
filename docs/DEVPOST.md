# Antikythera

## Tagline

A reproducible research workbench for testing Mediterranean medical traditions against later pharmacology.

## Inspiration

Medical texts preserve plant-use claims across centuries. Some connect to familiar drug discoveries. Those stories do not tell us how much traditional claims outperform suitable comparison groups. Famous plants attract research, later authors can repeat earlier sources, and historical identities remain uncertain. Antikythera makes those problems explicit.

## What it does

The software collects source records, proposes exact-span annotations and exposes them in a review workbench. Its analytical engine compares traditional claims with tested unclaimed pairs after a temporal freeze. Matching uses the same species, related species in the same family, or similar earlier research attention. Publication volume supplies an additional ranking baseline. Identity sampling and family resampling carry uncertainty into the comparisons.

The interactive workspace also presents source-linked discovery cases and hazard trails. It separates a selected historical story from an experimental confirmation or a qualified future research lead.

## Acquired data

The current collection includes four source layers: an 1850 Culpeper edition, Berendes' 1902 Dioscorides translation, Adams' 1847 Paul of Aegina volume III, and Pieroni and colleagues' 2014 Balkan medicinal table.

The pipeline produced **2,972 unreviewed annotation proposals** from **844 detected chapters and 91 table rows**. It retrieved **69 unique PubMed IDs in 75 species–category query records**, plus **30 annual publication counts** and **six modern taxonomy candidate sets**. These are acquisition counts, not validated historical claims or evidence grades. Every proposal remains outside the eligible scientific dataset until human review.

## How we built it

A deterministic extraction baseline keeps exact source sentences and separate chapter-title anchors. A German lexicon supports the Dioscorides OCR. The Paul adapter cuts entry text before explicit commentary markers. The licensed Balkan table adapter expands rowspans and exports selected taxon, part and use fields with original XML hashes.

Indication proposals use a word-and-character TF-IDF similarity baseline over twelve categories. A provider-neutral structured-model gateway supports explicitly enabled, capped extraction, grading and adjudication calls. No vendor credentials are configured and no paid model call has run.

Cached Europe PMC acquisition provides literature records without inventing an NCBI contact address. Abstract text stays in local ignored caches. GBIF supplies versioned modern-name candidates as a disclosed fallback to the intended WCVP/WFO backbone. Modern name-match scores never become historical identity probabilities automatically.

DuckDB storage and a local review API retain annotation decisions and provenance. The temporal engine implements matched comparisons, era and inherited-claim ablations, sensitivity analyses and family-bootstrap uncertainty. LightGBM fitting, sigmoid calibration and evaluation use separate calendar windows. Synthetic integration tests verify fitting, persistence and prediction. No synthetic fixture enters the empirical report.

## What is complete

The local software pipeline, acquired-source review queue, interactive workspace, reproducible analysis and ranking implementation are operational. The project includes an editable ten-slide presentation, a concise narration script and an AI-use disclosure.

## Scientific status

**Human-reviewed claims: 0. Human-reviewed evidence grades: 0.** The eligible empirical dataset is empty. A real-data model has not been fitted. No empirical risk ratio, validated precision at k, calibrated future probability or qualified prospective lead is available.

The planned 200-claim, 150-indication and 300-abstract audits remain outstanding. A capped acquisition sample cannot establish first-ever testing, first confirmation or never-tested status. Individual annual-count observations do not constitute complete research-effort histories. The four selected sources do not constitute an exhaustive corpus of Mediterranean medicine.

## What we learned

Source checking changed the proposed story. Colchicum podagra use predates Byzantium. The Pacific yew in paclitaxel discovery is distinct from Mediterranean European yew. The acquired Culpeper title page dates the edition to 1850 and includes later additions, so assigning every claim to 1653 would create false early evidence. Discovery of an isolated compound cannot automatically confirm a botanical preparation.

## Next steps

Independent reviewers must resolve source interpretation, historical dates, identities and experimental support. Complete synonym and search coverage, annotate independent audit samples and run the frozen comparisons. Release a result, including negative findings, before nominating laboratory candidates with domain experts.

## Responsible use and attribution

This project supports research prioritisation for laboratory testing. No prediction here is an established effect. It provides no dosing or treatment recommendations. Any future probability conditions on first testing within a future window. It does not estimate clinical efficacy or the chance that scientists will test a plant. Identity-and-family model ranges describe ensemble spread, not confidence intervals for an established effect.

Source licences remain specific to each edition or article. The Balkan source explicitly uses CC BY 2.0 and a data CC0 statement unless otherwise specified. Its exported table projection omits community indicators and keeps attribution. AI assisted implementation and research synthesis. No ETHCSTWIN aggregator integration or laboratory testing partnership has been completed or agreed.

## Selected sources

- [Culpeper edition catalog](https://www.gutenberg.org/ebooks/49513)
- [Berendes' Dioscorides edition](https://archive.org/details/despedaniosdios00pedagoog)
- [Adams' Paul of Aegina, volume III](https://archive.org/details/sevenbooksofpaul03pauluoft)
- [Licensed Balkan medicinal Table 2](https://europepmc.org/articles/PMC3998745)
- [Ancient Colchicum and podagra recipes](https://pubmed.ncbi.nlm.nih.gov/30557131/)
- [ANSES autumn-crocus warning](https://www.anses.fr/en/content/confusion-between-autumn-crocus-and-wild-garlic-can-lead-fatal-poisoning)
- [Metformin historical overview](https://doi.org/10.1007/s00125-017-4318-z)
- [NCI paclitaxel discovery account](https://www.cancer.gov/research/progress/discovery/taxol)

Team members, public demo URL, repository URL and video URL require actual submission details. This file is a draft. No Devpost submission has occurred.
