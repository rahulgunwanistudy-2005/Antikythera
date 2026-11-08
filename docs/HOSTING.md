# Private demo hosting

Private demo: https://antikythera-medicine-observatory.rahulgunwani-study.chatgpt.site

The static React build uses `app/web/.openai/hosting.json`. The final application source commit is `528afa728ee71c7a3f955bea6d0b81782a6ac04b`. It includes the seven-view research workspace, actual proposed corpus/evidence records, offline cue suggestions and report status. Full abstracts, private raw caches and the local DuckDB review database are excluded.

The hosting checkout lives separately from the research repository. Updates use the same project ID, synchronize the intended app source, verify/build it, then publish the exact pushed commit. The private audience is preserved; the service requires ChatGPT sign-in. Local review remains available through `make serve` at http://127.0.0.1:8000.

Scientific results remain gated by independent reviews and data coverage. Publication of the software does not imply an audited empirical finding.
