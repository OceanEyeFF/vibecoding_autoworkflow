#!/usr/bin/env python3
import argparse, json, subprocess, sys
from pathlib import Path

def load_changed(base: str, head: str):
    out = subprocess.check_output(["git", "diff", "--name-only", f"{base}...{head}"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]

def match(path: str, patterns):
    p = Path(path)
    for raw in patterns:
        pat = raw.strip()
        if not pat:
            continue
        if pat.endswith("/") and path.startswith(pat):
            return True
        if pat in path:
            return True
        if p.match(pat):
            return True
    return False

def main():
    ap = argparse.ArgumentParser(description="Harness Scope Gate checker")
    ap.add_argument("--contract", required=True)
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()

    data = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    in_scope = data.get("scope", {}).get("in_scope", [])
    out_scope = data.get("scope", {}).get("out_of_scope", [])

    changed = load_changed(args.base, args.head)
    violations = []
    for f in changed:
        if out_scope and match(f, out_scope):
            violations.append((f, "out_of_scope"))
            continue
        if in_scope and not match(f, in_scope):
            violations.append((f, "not_in_scope"))

    print(json.dumps({"changed_files": changed, "violations": violations}, ensure_ascii=False, indent=2))
    return 1 if violations else 0

if __name__ == "__main__":
    sys.exit(main())
