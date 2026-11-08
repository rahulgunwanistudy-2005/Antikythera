# External historical-identity reference

The requested Figshare share is [the data link cited by Lardos and colleagues](https://figshare.com/s/2e0f64b5794892ed4679). On 7 November 2026 the page returned HTTP 403 through the retrieval tool and HTTP 202 with an empty body through an ordinary public request. Official public article search did not establish a matching dataset article ID or file ID. **Research data file 11 and its separate dataset licence remain unacquired and unverified.** No private API access, credentials or inferred file IDs were used.

A useful, separately licensed fallback is available in the [open article, Table 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC7615571/#T2), DOI [10.1016/j.jep.2023.117622](https://doi.org/10.1016/j.jep.2023.117622). The retrieved JATS explicitly carries CC BY 4.0. This article licence authorises this attributed table transformation. It does not establish the licence of the inaccessible Figshare files.

`candidate_reference.json` preserves 141 candidate records for 50 historical lemma tags. Botanical congruence categories reproduce the published totals: 37 strong, 51 moderate, 33 weak and 20 not assessed against the selected floras. Source names remain as published. The importer joins continuation rows while preserving source row and column provenance. One medicinal ordinal is absent from the XML for *Hyoscyamus aureus* and remains null. Botanical grade membership is explicit in its table column.

These are **botanical congruence assessments**, not confirmed historical identities or calibrated probabilities. The ordinal medicinal comparison is supplementary evidence, not a pharmacological support label. Using medicinal similarity to validate medicinal prediction could introduce circularity. The reference covers the paper's selected information-rich historical subset and does not represent every plant in the text.

All records explicitly retain null identity probabilities, null truth labels and null Antikythera predictions. They are not independent gold records and are not eligible for ECE. Acquiring this reference does not complete an Antikythera human audit. A qualified independent truth protocol and paired predictions are still required.

`manifest.json` records availability, licences, source hashes and the exact Figshare blocker. The original article XML and unsuccessful retrieval cache stay under ignored `data/raw/cache/identity_expert/`. Reproduce the public JSON transformation with:

```
python3 data/external/identity_expert/import_article_reference.py
```

Attribution: Andreas Lardos, Kristina Patmore, Robert Allkin, Rebecca Lazarou, Mark Nesbitt, Andrew C. Scott and Barbara Zipser (2024), *Journal of Ethnopharmacology* 322, 117622. Table 2 transformed to JSON by Antikythera under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No community or participant identifiers appear in the derived reference.
