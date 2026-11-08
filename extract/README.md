# Extraction and model processing

`python -m scripts.collect --offline` reproduces proposal extraction from cleared cached editions. The language rules and harmonisation scores are baselines with unmeasured semantic accuracy. Every proposal keeps exact offsets and source hashes; headings can supply a separately validated plant-name context. OCR errors, translator commentary, scope and historical dates remain review fields.

`StructuredProvider` supports two explicit protocols:

- `ollama`: POST the official local `/api/chat` shape with `model`, `messages`, `stream:false` and JSON `format` schema. It parses `message.content` as JSON.
- `gateway`: POST `{task,prompt,input,schema,model}` and require `{output:<JSON>}`. This supports a user-managed gateway without assuming vendor credentials.

Set `ANTIKYTHERA_MODEL_ENDPOINT`, `ANTIKYTHERA_MODEL_NAME`, `ANTIKYTHERA_MODEL_PROTOCOL` and optional `ANTIKYTHERA_MODEL_TOKEN` in the process environment. Endpoint credentials/query strings are refused. Public HTTPS or loopback HTTP is supported. Tokens stay out of caches, request hashes and printed errors. No request occurs unless `scripts.model --enable-model` is explicitly used. A local model must already be installed/running; this project does not silently download weights.

Model outputs are cached, source-validated and imported into the review queue by `make report`. Harmonisation adjudication can abstain. Model evidence grades remain proposals, never gold or reviewed labels. Invalid offsets, unknown categories, malformed tiers and changed evidence hashes are rejected.

Official protocol reference: [Ollama chat API](https://docs.ollama.com/api/chat). Source text is input data and cannot change the processing instructions.
