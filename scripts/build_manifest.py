#!/usr/bin/env python
from __future__ import annotations
import argparse, json, pathlib
from datetime import datetime
from common import now_iso, read_json, write_text

ROOT = pathlib.Path(__file__).resolve().parents[1]


def select_latest_date_file(dir_path: pathlib.Path) -> tuple[str, pathlib.Path] | None:
    if not dir_path.exists():
        return None
    candidates = [p for p in dir_path.iterdir() if p.is_file() and p.suffix == '.json']
    if not candidates:
        return None
    # Filenames are YYYY-MM-DD.json
    def key(p: pathlib.Path) -> str:
        return p.stem
    latest = max(candidates, key=key)
    return latest.stem, latest


def collect_entries() -> list[dict]:
    entries: list[dict] = []
    mapping = {
        'entity': 'EntityRecord',
        'activity': 'ActivityRecord',
    }
    for ref_kind, kind_title in mapping.items():
        base = ROOT / 'data' / 'refs' / ref_kind
        if not base.exists():
            continue
        for logical_dir in sorted([p for p in base.iterdir() if p.is_dir()]):
            sel = select_latest_date_file(logical_dir)
            if not sel:
                continue
            date, ref_file = sel
            ref = read_json(str(ref_file))
            obj_hash = ref.get('object')
            entries.append({
                'kind': kind_title,
                'logical_id': logical_dir.name,
                'date': date,
                'object': obj_hash,
            })
    return entries


def main():
    ap = argparse.ArgumentParser(description='Build a dataset manifest from refs')
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--id', required=True, dest='manifest_id')
    args = ap.parse_args()

    entries = collect_entries()

    # Back-compat: include both detailed 'entries' and flat 'objects' lists
    objects = [{ 'hash': e['object'] } for e in entries]

    manifest = {
        'manifest_id': args.manifest_id,
        'dataset': args.dataset,
        'created_at': now_iso(),
        'entries': entries,
        'objects': objects,
    }

    out_path = ROOT / 'data' / 'manifests' / args.dataset / f"{args.manifest_id}.json"
    write_text(str(out_path), json.dumps(manifest, indent=2))
    print(f"Wrote manifest: {out_path}")

if __name__ == '__main__':
    main()
