#!/usr/bin/env python3
"""
Load words from game_words.txt into the server via the wordlist add RPC API.

Usage:
    python3 load_wordlist.py [--base-url URL] [--file PATH] [--batch-size N] [--dry-run]

Environment:
    BASE_URL  Server base URL (default: http://localhost:8000)
"""

import json
import os
import sys
import urllib.request
import argparse
from pathlib import Path


def rpc_call(base_url: str, method: str, params: dict) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(
        f"{base_url}/rpc",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    project_root = Path(__file__).resolve().parent.parent
    default_file = project_root / "game_words.txt"

    parser = argparse.ArgumentParser(description="Load word list into the server")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://localhost:8000"))
    parser.add_argument("--file", default=str(default_file), help=f"Path to word list file (default: {default_file})")
    parser.add_argument("--batch-size", type=int, default=200, help="Words per request (default: 200)")
    parser.add_argument("--dry-run", action="store_true", help="Print stats and first batch without sending")
    args = parser.parse_args()

    word_file = Path(args.file)
    if not word_file.exists():
        print(f"Error: file not found: {word_file}", file=sys.stderr)
        sys.exit(1)

    words = [
        line.strip().upper()
        for line in word_file.read_text().splitlines()
        if line.strip()
    ]

    if not words:
        print("Error: no words found in file", file=sys.stderr)
        sys.exit(1)

    batches = [words[i:i + args.batch_size] for i in range(0, len(words), args.batch_size)]

    print(f"Base URL   : {args.base_url}")
    print(f"File       : {word_file}")
    print(f"Words      : {len(words)}")
    print(f"Batches    : {len(batches)} × up to {args.batch_size}")

    if args.dry_run:
        print(f"\n-- dry run, first batch ({len(batches[0])} words) --")
        print(", ".join(batches[0][:10]) + (" …" if len(batches[0]) > 10 else ""))
        return

    print()
    total_added = 0
    total_existing = 0

    for i, batch in enumerate(batches, 1):
        try:
            result = rpc_call(args.base_url, "add", {"words": batch})
            if "error" in result:
                print(f"  batch {i}/{len(batches)}  ERROR: {result['error']['message']}")
                sys.exit(1)
            added = len(result["result"]["added"])
            existing = len(result["result"]["already_exists"])
            total_added += added
            total_existing += existing
            print(f"  batch {i}/{len(batches)}  added: {added}  already existed: {existing}")
        except Exception as e:
            print(f"  batch {i}/{len(batches)}  FAILED: {e}")
            sys.exit(1)

    print(f"\nDone.  added: {total_added}  already existed: {total_existing}  total: {len(words)}")


if __name__ == "__main__":
    main()
