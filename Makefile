VENV=.venv
PY=python3

.PHONY: venv install objects manifest promote validate api token db agent demo

venv:
	$(PY) -m venv $(VENV)

install:
	. $(VENV)/bin/activate && pip install -r requirements.txt

objects:
	. $(VENV)/bin/activate && \
	$(PY) scripts/canonicalize_and_hash.py data/samples/entity_project_apollo.json && \
	$(PY) scripts/canonicalize_and_hash.py data/samples/activity_generate_readme.json

manifest:
	. $(VENV)/bin/activate && $(PY) scripts/build_manifest.py --dataset core --id dev-seed

promote:
	. $(VENV)/bin/activate && \
	$(PY) scripts/promote_channel.py --dataset core --channel staging --manifest dev-seed && \
	$(PY) scripts/promote_channel.py --dataset core --channel prod --manifest dev-seed

validate:
	. $(VENV)/bin/activate && $(PY) scripts/validate_repo.py

api:
	. $(VENV)/bin/activate && uvicorn api.main:app --reload --port 8000

token:
	. $(VENV)/bin/activate && $(PY) scripts/dev_token.py > /tmp/token.txt && echo "TOKEN ready → /tmp/token.txt"

db:
	. $(VENV)/bin/activate && $(PY) scripts/rebuild_duckdb.py --dataset core --manifest dev-seed

agent:
	. $(VENV)/bin/activate && $(PY) -m agent.cli --dataset core --manifest dev-seed --view llm_min --repl

demo: install objects manifest promote validate db
	@echo "Run API: make api  | Agent: make agent"


