# Indication harmonisation

The default baseline tokenises historical ailment phrases into words and character trigrams. It computes TF-IDF vectors against the versioned twelve-category lexicon, then ranks by cosine similarity. Scores measure textual similarity, not medical correctness or calibrated probabilities. The baseline supplies alternatives to a human reviewer. It has no measured accuracy until the independent 150-item gold set exists.

The extraction baseline uses explicit therapeutic cues and ailment terms in the chapter's government-and-virtues passage. It can miss paraphrases, mistake negation and overcount repeated claims. A proposal is a source-grounded annotation candidate, not a validation result. Every row retains the exact source sentence and a separately validated chapter-title span.

Optional structured model adjudication runs only through `python -m scripts.model harmonise --enable-model --limit 1`. Configure the provider-neutral gateway described in `extract/README.md`. It never marks human review complete. An external embedding service may be attached through the same adapter, but embeddings are not the implemented default and are not claimed to have run.
