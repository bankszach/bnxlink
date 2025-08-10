from __future__ import annotations
import argparse, json, pathlib
from rich.console import Console
from agent.pipes.validator import validate_object
from agent.pipes.redactor import apply_llm_min
from agent.pipes.summarizer import summarize

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

console = Console()

def resolve_manifest(dataset: str, manifest: str | None) -> dict:
    if manifest:
        path = DATA / f"manifests/{dataset}/{manifest}.json"
    else:
        import yaml
        ch = yaml.safe_load((DATA/"channels.yaml").read_text(encoding="utf-8")) or {}
        mid = ch.get(dataset, {}).get("prod")
        if not mid: raise SystemExit("no prod channel set")
        path = DATA / f"manifests/{dataset}/{mid}.json"
    return json.loads(path.read_text(encoding="utf-8"))

def load_object(hash_str: str) -> dict:
    assert hash_str.startswith("sha256:")
    h = hash_str.split(":",1)[1]
    path = DATA / f"objects/{h[:2]}/{h}.json"
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser(description="BNX Link Agent (console)")
    ap.add_argument("--dataset", default="core")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--view", default="llm_min", choices=["llm_min","full"])
    ap.add_argument("--repl", action="store_true", help="enter simple REPL after summary")
    args = ap.parse_args()

    m = resolve_manifest(args.dataset, args.manifest)
    objs = []
    items = []
    if "objects" in m:
        items = [(it["hash"]) for it in m["objects"]]
    elif "entries" in m:
        items = [(it["object"]) for it in m["entries"]]
    else:
        raise SystemExit("manifest missing 'objects' or 'entries'")
    for h in items:
        o = load_object(h)
        validate_object(o)  # throws on invalid
        if args.view == "llm_min":
            o = apply_llm_min(o)
        objs.append(o)

    summary = summarize(objs)
    console.rule("[bold]Context summary")
    for line in summary["lines"]:
        console.print(f"- {line}")

    if not args.repl:
        return

    console.rule("[bold]REPL")
    console.print("[dim]type 'list', 'show <n>', 'quit'[/dim]")
    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if cmd in ("quit","exit"): break
        if cmd == "list":
            for i, o in enumerate(objs):
                k = o.get("envelope",{}).get("kind")
                ident = o.get("body",{}).get("entity_id") or o.get("body",{}).get("activity_id")
                console.print(f"[{i}] {k} :: {ident}")
            continue
        if cmd.startswith("show "):
            try:
                idx = int(cmd.split()[1])
                console.print_json(data=objs[idx])
            except Exception as e:
                console.print(f"[red]bad index[/red]: {e}")
            continue
        if cmd:
            console.print("[yellow]echo[/yellow]: this is a scaffold. add LLM later.")
    console.print("[green]bye[/green]")

if __name__ == "__main__":
    main()


