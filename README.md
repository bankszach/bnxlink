# BNX Link (Sprint 1 Scaffold)

Protocol-forward, domain-agnostic scaffold:
- Immutable, content-addressed JSON objects
- Refs → Manifests → Channels (prod/staging)
- CLI scripts for hash, manifest build, channel promote
- JSON Schemas for two generic types

## Quickstart
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/canonicalize_and_hash.py data/samples/entity_project_apollo.json
python scripts/canonicalize_and_hash.py data/samples/activity_generate_readme.json

python scripts/build_manifest.py --dataset core --id dev-seed
python scripts/promote_channel.py --dataset core --channel staging --manifest dev-seed
python scripts/promote_channel.py --dataset core --channel prod --manifest dev-seed

python scripts/validate_repo.py

## Quickstart
```bash
make demo
# in one terminal
make api
# in another
make agent
```

## Why BNX Link
BNX Link provides a minimal, pragmatic scaffold for content-addressed data, manifests, and promotion channels to bootstrap reproducible data workflows.

## Roadmap
- Policy engine integration (OPA/Cedar)
- Signed manifests and provenance
- Server-side redaction profiles

## Contributing
See `CONTRIBUTING.md`. Please also review `CODE_OF_CONDUCT.md` and `SECURITY.md`.
