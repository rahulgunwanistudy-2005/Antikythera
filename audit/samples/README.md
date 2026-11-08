# Independent audit work packets

`make sample-audit` samples actual proposed records with a fixed seed, stratified by source era, category and language. The files are unfilled annotation packets. Their size is not an audited count.

Annotators must independently read the source and set gold labels, name, personal attestation and independent annotation flag. Preserve the original `prediction` while writing gold. To protect the denominator, extraction recall also needs a complete independent passage annotation with its unique `passage_id`, `complete_passage_annotation:true` and nonnegative `missed_claims`. A short extracted quote alone does not give the total number of missed claims.

For abstracts, retrieve/read the locally hashed record and original study. A null prediction or abstention is not a supporting verdict. Report coverage of abstentions separately from precision on assigned verdicts. For harmonisation, label the organ category from source context. For identity, use an independent truth protocol, not the ordinal congruence categories from the Lardos article. Numeric confidence and accepted labels are required for ECE.

Place adjudicated records in `data/reviewed/audits.json` and run `make report`. The local `/api/audits/{kind}/{id}` endpoint also records attested gold against the original proposal version. Changed proposals invalidate old paired predictions without erasing their history. The 300-abstract target is larger than the present bounded queue; acquire additional records before claiming that audit complete.
