#!/usr/bin/env python
from __future__ import annotations
import argparse, json, pathlib, duckdb, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DBDIR = ROOT / "db"
DBPATH = DBDIR / "bnxlink.duckdb"

def load_manifest(dataset: str, manifest_id: str | None) -> dict:
    if manifest_id is None:
        ch = yaml.safe_load((DATA/"channels.yaml").read_text(encoding="utf-8")) or {}
        manifest_id = ch.get(dataset, {}).get("prod")
        if not manifest_id:
            raise SystemExit(f"No prod channel set for dataset '{dataset}'.")
    mpath = DATA / f"manifests/{dataset}/{manifest_id}.json"
    if not mpath.exists():
        raise SystemExit(f"Manifest not found: {mpath}")
    return json.loads(mpath.read_text(encoding="utf-8"))

def object_path_for_hash(h: str) -> pathlib.Path:
    assert h.startswith("sha256:")
    hexh = h.split(":",1)[1]
    return DATA / f"objects/{hexh[:2]}/{hexh}.json"

def main():
    ap = argparse.ArgumentParser(description="Rebuild DuckDB projection from manifest")
    ap.add_argument("--dataset", default="core")
    ap.add_argument("--manifest", default=None, help="manifest id; default: channels.yaml prod")
    args = ap.parse_args()

    manifest = load_manifest(args.dataset, args.manifest)
    DBDIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DBPATH))
    con.execute("PRAGMA threads=4")

    # fresh schema
    con.execute("""
      DROP TABLE IF EXISTS object_store;
      CREATE TABLE object_store(
        hash TEXT PRIMARY KEY,
        kind TEXT,
        classification TEXT,
        created_at TIMESTAMP,
        doc JSON
      );
    """)

    # load objects (support manifests with either 'objects' or 'entries')
    rows = []
    items = []
    if "objects" in manifest:
        items = [(it["hash"]) for it in manifest["objects"]]
    elif "entries" in manifest:
        items = [(it["object"]) for it in manifest["entries"]]
    else:
        raise SystemExit("Manifest missing 'objects' or 'entries' array")
    for h in items:
        p = object_path_for_hash(h)
        doc = json.loads(p.read_text(encoding="utf-8"))
        rows.append((
            h,
            doc.get("envelope",{}).get("kind"),
            doc.get("envelope",{}).get("privacy",{}).get("classification","internal"),
            doc.get("envelope",{}).get("created_at"),
            json.dumps(doc)
        ))
    con.executemany("INSERT INTO object_store VALUES (?,?,?,?,?)", rows)

    # views
    con.execute("DROP VIEW IF EXISTS v_entity_record")
    con.execute("""
      CREATE VIEW v_entity_record AS
      SELECT
        hash,
        json_extract_string(doc, '$.body.entity_id') AS entity_id,
        json_extract_string(doc, '$.body.entity_type') AS entity_type,
        json_extract_string(doc, '$.context.snapshot_as_of') AS snapshot_as_of,
        json_extract(doc, '$.body.labels') AS labels
      FROM object_store
      WHERE kind='EntityRecord';
    """)
    con.execute("DROP VIEW IF EXISTS v_activity_record")
    con.execute("""
      CREATE VIEW v_activity_record AS
      SELECT
        hash,
        json_extract_string(doc, '$.body.activity_id') AS activity_id,
        json_extract_string(doc, '$.body.activity_type') AS activity_type,
        json_extract_string(doc, '$.body.status') AS status,
        json_extract_string(doc, '$.body.scheduling.due_date') AS due_date,
        json_extract(doc, '$.body.subject_refs') AS subject_refs
      FROM object_store
      WHERE kind='ActivityRecord';
    """)

    print(f"[OK] DuckDB rebuilt at {DBPATH} using manifest {manifest['manifest_id']}.")
    con.close()

if __name__ == "__main__":
    main()


