#!/usr/bin/env python
from __future__ import annotations
import json, pathlib, sys
from jsonschema import Draft202012Validator
from common import canonical_json, sha256_hex, read_json

ROOT = pathlib.Path(__file__).resolve().parents[1]


def validate_object_hash(obj: dict) -> tuple[bool, str]:
    env = obj.get('envelope', {})
    integrity = env.get('integrity', {})
    claimed = integrity.get('sha256')
    if not isinstance(claimed, str) or not claimed.startswith('sha256:'):
        return False, 'Missing or invalid envelope.integrity.sha256'
    # recompute by setting sha to None
    original = integrity.get('sha256')
    integrity['sha256'] = None
    h = sha256_hex(canonical_json(obj))
    integrity['sha256'] = original
    if claimed != f'sha256:{h}':
        return False, f'Hash mismatch: claimed={claimed} computed=sha256:{h}'
    return True, ''


def get_schema_for_kind(kind: str) -> dict | None:
    schema_dir = ROOT / 'schemas'
    if kind == 'EntityRecord':
        return read_json(str(schema_dir / 'EntityRecord.v1.json'))
    if kind == 'ActivityRecord':
        return read_json(str(schema_dir / 'ActivityRecord.v1.json'))
    return None


def validate_body_against_schema(kind: str, body: dict) -> tuple[bool, str]:
    schema = get_schema_for_kind(kind)
    if not schema:
        return True, ''  # Unknown kinds are not validated here
    try:
        Draft202012Validator(schema).validate(body)
        return True, ''
    except Exception as e:
        return False, f'Schema validation failed for {kind}: {getattr(e, "message", str(e))}'


def main() -> int:
    objects_dir = ROOT / 'data' / 'objects'
    refs_dir = ROOT / 'data' / 'refs'
    ok = True
    obj_count = 0
    for shard in objects_dir.glob('*'):
        if not shard.is_dir():
            continue
        for f in shard.glob('*.json'):
            obj = read_json(str(f))
            obj_count += 1
            # hash check
            hv, msg = validate_object_hash(obj)
            if not hv:
                print(f"[HASH] {f}: {msg}")
                ok = False
            # schema check
            kind = obj.get('envelope', {}).get('kind')
            body = obj.get('body', {})
            sv, smsg = validate_body_against_schema(kind, body)
            if not sv:
                print(f"[SCHEMA] {f}: {smsg}")
                ok = False

    # refs point to objects
    ref_count = 0
    for cat in ['entity','activity']:
        base = refs_dir / cat
        if not base.exists():
            continue
        for logical in base.glob('*'):
            for f in logical.glob('*.json'):
                ref_count += 1
                ref = read_json(str(f))
                objhash = ref.get('object', '')
                if not isinstance(objhash, str) or not objhash.startswith('sha256:'):
                    print(f"[REF] {f}: invalid object field {objhash!r}")
                    ok = False
                else:
                    h = objhash.split(':',1)[1]
                    obj_path = ROOT / 'data' / 'objects' / h[:2] / f"{h}.json"
                    if not obj_path.exists():
                        print(f"[REF] {f}: object not found at {obj_path}")
                        ok = False

    if ok:
        print(f"Validation OK: {obj_count} objects, {ref_count} refs")
        return 0
    else:
        print("Validation FAILED")
        return 2

if __name__ == '__main__':
    sys.exit(main())
