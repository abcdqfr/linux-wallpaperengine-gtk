#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thumbnail_scan import scan_workshop_root  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Scan a Wallpaper Engine Workshop library for thumbnail/preview inconsistencies (metadata only)."
    )
    ap.add_argument(
        "workshop_root", type=Path, help="Workshop content root (e.g. .../workshop/content/431960)"
    )
    ap.add_argument("--limit", type=int, default=None, help="Limit number of items scanned (debug)")
    ap.add_argument("--json", action="store_true", help="Emit full JSON results")
    args = ap.parse_args()

    results = scan_workshop_root(args.workshop_root, limit=args.limit)

    if args.json:
        payload = [
            {
                "id": r.item_id,
                "root_entries": r.root_entries,
                "preview_candidates": list(r.preview_candidates),
                "image_files": list(r.image_files),
                "suspicious": list(r.suspicious),
            }
            for r in results
        ]
        print(json.dumps(payload, indent=2))
        return 0

    summary = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    for r in results:
        for s in r.suspicious:
            summary[s] += 1
            if len(examples[s]) < 20:
                examples[s].append(r.item_id)

    print(f"scanned_items={len(results)}")
    for k, v in summary.most_common():
        print(f"{k}={v}")
    print("\nexamples:")
    for k in sorted(examples.keys()):
        print(f"{k}: {', '.join(examples[k])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
