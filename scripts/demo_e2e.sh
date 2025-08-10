#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
pip install -r requirements.txt
python scripts/canonicalize_and_hash.py data/samples/entity_project_apollo.json
python scripts/canonicalize_and_hash.py data/samples/activity_generate_readme.json
python scripts/build_manifest.py --dataset core --id dev-seed
python scripts/promote_channel.py --dataset core --channel prod --manifest dev-seed
python scripts/validate_repo.py
python scripts/rebuild_duckdb.py --dataset core --manifest dev-seed
echo "OK. Start API -> uvicorn api.main:app --reload ; Agent -> python -m agent.cli --dataset core --manifest dev-seed --view llm_min --repl"


