# Implementation references

Official documentation consulted while implementing library/API-dependent behavior:

- [DuckDB Python DB API](https://duckdb.org/docs/stable/clients/python/dbapi): file connections, parameterized queries and transactions.
- [DuckDB Parquet export](https://duckdb.org/docs/stable/guides/file_formats/parquet_export): typed data exports.
- [FastAPI middleware](https://fastapi.tiangolo.com/tutorial/middleware/) and [CORS](https://fastapi.tiangolo.com/tutorial/cors/): local request/origin handling.
- [Ollama chat API](https://docs.ollama.com/api/chat): non-streaming structured output requests with JSON format schemas.
- LightGBM official references and statistical implementation assumptions are recorded in `timemachine/README.md`.

Human/source review is a separate operation from independent gold audit. The database preserves the original proposal and a hash-chained decision trail. Audit predictions are read from the original proposal version, never from a corrected review. A proposal change invalidates its old paired audit. Review and analysis exports remain separate, and typed Parquet tables retain valid schemas even when no scientific records qualify.

Raw caches are intentionally absent from versioned/public output. A bundled proposal snapshot has its own checksums. An offline rebuild without raw caches preserves that snapshot; actual source review requires the raw file matching its recorded hash. No cache miss becomes a negative experimental outcome.
