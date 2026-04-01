#!/usr/bin/env python3
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description="Backfill gate status to harness state")
    ap.add_argument("--state", required=True)
    ap.add_argument("--gate", required=True)
    ap.add_argument("--status", required=True, choices=["pass", "fail", "blocked", "skip"])
    ap.add_argument("--evidence", default="")
    args = ap.parse_args()

    p = Path(args.state)
    if p.exists():
        state = json.loads(p.read_text(encoding="utf-8"))
    else:
        state = {}

    state.setdefault("gates", {})[args.gate] = {
        "status": args.status,
        "evidence": args.evidence,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated {args.gate}={args.status} -> {args.state}")

if __name__ == "__main__":
    main()
