# Hosting

Live observatory: https://antikythera-unsg.onrender.com

The React build in `app/web` is deployed as a Render static site, configured in [`render.yaml`](../render.yaml). Render runs `npm ci && npm run build` in `app/web` and publishes `app/web/dist`. Pushes to `main` redeploy automatically.

The hosted build reads the committed static exports in `app/web/public/` (`catalog.json`, `report.json`, `workspace.json`). It includes the actual proposed corpus/evidence records, offline cue suggestions and report status. Full abstracts, private raw caches and the local DuckDB review database are excluded. Without the local API the interface runs read-only; review decisions can be exported as batches and applied locally.

Local review remains available through `make serve` at http://127.0.0.1:8000. To refresh the hosted data, run `make report`, commit the regenerated files in `app/web/public/`, and push.

Scientific results remain gated by independent reviews and data coverage. Publication of the software does not imply an audited empirical finding.
