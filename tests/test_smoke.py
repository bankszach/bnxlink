import json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]

def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, shell=True, check=True, capture_output=True, text=True)

def test_objects_exist_after_manifest():
    if not (ROOT/"data/manifests/core/dev-seed.json").exists():
        run(". .venv/bin/activate && python scripts/build_manifest.py --dataset core --id dev-seed")
    m = json.loads((ROOT/"data/manifests/core/dev-seed.json").read_text())
    assert m["objects"], "manifest should contain objects"
    h = m["objects"][0]["hash"].split(":")[1]
    p = ROOT / f"data/objects/{h[:2]}/{h}.json"
    assert p.exists()

def test_validate_repo_passes():
    run(". .venv/bin/activate && python scripts/validate_repo.py")


