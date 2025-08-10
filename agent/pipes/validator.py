from __future__ import annotations
import json, pathlib
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMAS = {
    "EntityRecord": json.loads((ROOT/"schemas/EntityRecord.v1.json").read_text(encoding="utf-8")),
    "ActivityRecord": json.loads((ROOT/"schemas/ActivityRecord.v1.json").read_text(encoding="utf-8")),
}

def validate_object(obj: dict) -> None:
    kind = obj.get("envelope",{}).get("kind")
    if kind in SCHEMAS:
        Draft202012Validator(SCHEMAS[kind]).validate(obj.get("body",{}))


