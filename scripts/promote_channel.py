#!/usr/bin/env python
from __future__ import annotations
import argparse, json, pathlib, yaml
from common import now_iso

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser(description="Promote a manifest to a channel")
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--channel", required=True, choices=["prod","staging"])
    ap.add_argument("--manifest", required=True, help="manifest id (file name without .json)")
    args = ap.parse_args()

    manifest_path = ROOT / f"data/manifests/{args.dataset}/{args.manifest}.json"
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    channels_yml = ROOT / "data/channels.yaml"
    data = {}
    if channels_yml.exists():
        data = yaml.safe_load(channels_yml.read_text(encoding="utf-8")) or {}
    data.setdefault(args.dataset, {})
    data[args.dataset][args.channel] = args.manifest
    channels_yml.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")

    with (ROOT / "data/ledger.ndjson").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), "event":"channel.promote", "dataset": args.dataset, "channel": args.channel, "manifest": args.manifest}) + "\n")

    print(f"Promoted {args.dataset}@{args.channel} -> {args.manifest}")

if __name__ == "__main__":
    main()
