"""`slotledger verify <bundle.zip | ledger.jsonl> [--trusted-key HEX]`

Exit code 0 when every supplied invariant holds, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slotledger.bundle import BundleInvalid, read_bundle, read_ledger_jsonl
from slotledger.verify import verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="slotledger")
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="verify a bundle or a bare ledger.jsonl")
    v.add_argument("path", type=Path)
    v.add_argument("--trusted-key", help="hospital's trusted public key (hex)")
    v.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    data = args.path.read_bytes()
    try:
        if args.path.suffix == ".jsonl":
            events, snapshots, head = read_ledger_jsonl(data.decode("utf-8")), None, None
        else:
            events, snapshots, head = read_bundle(data)
    except BundleInvalid as e:
        print(f"invalid: {e}", file=sys.stderr)
        return 2
    report = verify(events, snapshots, head, args.trusted_key)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(("PASS" if report.ok else "FAIL") + f"  {report.events} events")
        for name, c in report.checks.items():
            where = f" at #{c.seq}" if c.seq else ""
            print(f"  {c.status.upper():12} {name}{where}: {c.detail}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
