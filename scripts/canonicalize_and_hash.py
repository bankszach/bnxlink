#!/usr/bin/env python
from __future__ import annotations
import argparse, json, pathlib
from common import canonical_json, sha256_hex, write_text, read_json, now_iso

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser(description="Canonicalize an object, compute sha256, store content-addressed, write ref")
    ap.add_argument("source_json", help="Path to source JSON (unhashed)")
    ap.add_argument("--date", default=None, help="Ref date (YYYY-MM-DD). Defaults to context date or today.")
    args = ap.parse_args()

    src = pathlib.Path(args.source_json)
    obj = read_json(src)

    obj.setdefault("envelope", {})
    obj["envelope"].setdefault("integrity", {"sha256": None})

    # hash with sha set to None
    obj["envelope"]["integrity"]["sha256"] = None
    data = canonical_json(obj)
    h = sha256_hex(data)

    # set the real hash and write object
    obj["envelope"]["integrity"]["sha256"] = f"sha256:{h}"
    data2 = canonical_json(obj)
    prefix = h[:2]
    obj_path = ROOT / f"data/objects/{prefix}/{h}.json"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    obj_path.write_bytes(data2)

    # write a ref (human pointer)
    kind = obj.get("envelope", {}).get("kind", "Object")
    date = args.date or obj.get("context", {}).get("snapshot_as_of")
    if not date:
        from datetime import date as _date
        date = _date.today().isoformat()

    body = obj.get("body", {})
    if kind == "EntityRecord":
        logical_id = body.get("entity_id","entity")
        ref_path = ROOT / f"data/refs/entity/{logical_id}/{date}.json"
    elif kind == "ActivityRecord":
        logical_id = body.get("activity_id","activity")
        ref_path = ROOT / f"data/refs/activity/{logical_id}/{date}.json"
    else:
        logical_id = "object"
        ref_path = ROOT / f"data/refs/object/{logical_id}/{date}.json"

    write_text(str(ref_path), json.dumps({"object": f"sha256:{h}"}, indent=2))

    # ledger append
    with (ROOT / "data/ledger.ndjson").open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "ts": now_iso(),
                    "event": "object.write",
                    "hash": f"sha256:{h}",
                    "ref": str(ref_path.relative_to(ROOT)),
                }
            )
            + "\n"
        )

    print(f"Wrote object: {obj_path}")
    print(f"Wrote ref:    {ref_path}")
    print(f"Hash:         sha256:{h}")

if __name__ == "__main__":
    main()
