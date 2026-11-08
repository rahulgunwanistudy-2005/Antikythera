PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
.PHONY: all setup test data report web install dev serve api collect sample-audit models video verify-sources clean
all: data test web

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.lock.txt

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m unittest audit.test_pipeline -v
	node --test tests/frontend_model.mjs

data:
	$(PYTHON) -m scripts.pipeline

report:
	$(PYTHON) -m scripts.pipeline --skip-collection

install:
	npm ci --prefix app/web --no-audit --no-fund

web:
	@test -f app/web/public/workspace.json || $(MAKE) report
	@test -d app/web/node_modules || $(MAKE) install
	npm run build --prefix app/web

dev:
	npm run dev --prefix app/web -- --port 5186 --strictPort

serve: web
	$(PYTHON) -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000

api:
	$(PYTHON) -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000

collect:
	$(PYTHON) -m scripts.collect --fetch

sample-audit:
	$(PYTHON) -m audit.scoring --sample

models:
	$(PYTHON) -m timemachine.ranker data/derived/dataset.json --train-freeze 1950 --calibration-freeze 1980 --evaluation-freeze 2000 --output data/derived/ranker.json

video:
	$(PYTHON) -m scripts.build_video

verify-sources:
	$(PYTHON) scripts/verify_sources.py

clean:
	rm -rf app/web/dist
