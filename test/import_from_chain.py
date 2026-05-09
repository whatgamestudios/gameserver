#!/usr/bin/env python3
"""
Import on-chain Worcadian game submissions into the server.

For each game day from 0 to the current game day, calls getResults(uint32)
on the WorcadianGameV4 contract via the Immutable zkEVM RPC, then imports
every submission into the server via the board.import RPC API.

Usage:
    python3 import_from_chain.py [--base-url URL] [--rpc-url URL] [--dry-run] [--start-day N]

Environment:
    BASE_URL  Server base URL (default: http://localhost:8000)
    RPC_URL   Ethereum RPC URL (default: https://rpc.immutable.com)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from web3 import Web3

# ── Constants (mirror api/index.py) ──────────────────────────────────────────

GAME_START     = 1774828800   # GMT Monday March 30, 2026 00:00:00 UTC
SECONDS_PER_DAY = 86400
PLUS_FOURTEEN  = 50400        # GMT+14 offset
MINUS_TWELVE   = 43200        # GMT-12 offset

CONTRACT_ADDRESS = "0xBe3558861DE7BB699b9a929d1eA5503dCcb329cD"

ABI = [
    {
        "inputs": [{"internalType": "uint32", "name": "_gameDay", "type": "uint32"}],
        "name": "getResults",
        "outputs": [
            {"internalType": "uint256", "name": "numSubmissions", "type": "uint256"},
            {"internalType": "uint256", "name": "bestScore",      "type": "uint256"},
            {
                "components": [
                    {"internalType": "address", "name": "player", "type": "address"},
                    {"internalType": "string",  "name": "board",  "type": "string"},
                ],
                "internalType": "struct WorcadianGameV4.Submission[]",
                "name": "submissions",
                "type": "tuple[]",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def current_max_game_day() -> int:
    now = int(time.time())
    return (now + PLUS_FOURTEEN - GAME_START) // SECONDS_PER_DAY


def server_rpc(base_url: str, method: str, params: dict) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(
        f"{base_url}/rpc",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import on-chain Worcadian submissions")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://localhost:8000"))
    parser.add_argument("--rpc-url",  default=os.getenv("RPC_URL",  "https://rpc.immutable.com"))
    parser.add_argument("--start-day", type=int, default=0, help="First game day to fetch (default: 0)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch chain data but do not write to server")
    args = parser.parse_args()

    w3 = Web3(Web3.HTTPProvider(args.rpc_url))
    if not w3.is_connected():
        print(f"Error: cannot connect to {args.rpc_url}", file=sys.stderr)
        sys.exit(1)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=ABI,
    )

    max_day = current_max_game_day()
    print(f"Server     : {args.base_url}")
    print(f"Chain RPC  : {args.rpc_url}")
    print(f"Contract   : {CONTRACT_ADDRESS}")
    print(f"Days       : {args.start_day} – {max_day}")
    if args.dry_run:
        print("Mode       : DRY RUN (no writes)")
    print()

    total_submissions = 0
    total_imported = 0
    total_duplicates = 0
    total_errors = 0

    for day in range(args.start_day, max_day + 1):
        try:
            num_submissions, best_score, subs = contract.functions.getResults(day).call()
        except Exception as e:
            print(f"  day {day:4d}  chain error: {e}")
            total_errors += 1
            continue

        if num_submissions == 0:
            print(f"  day {day:4d}  no submissions")
            continue

        print(f"  day {day:4d}  {num_submissions} submission(s), best score {best_score}")

        for sub in subs:
            player, board = sub[0], sub[1]
            total_submissions += 1

            if args.dry_run:
                print(f"           [dry run] would import player={player} board={board[:20]}…")
                continue

            try:
                result = server_rpc(args.base_url, "board.import", {
                    "game_day": day,
                    "board": board,
                    "player": player,
                })
                if "error" in result:
                    print(f"           import error for {player}: {result['error']['message']}")
                    total_errors += 1
                elif result["result"]["status"] == "duplicate":
                    total_duplicates += 1
                else:
                    score = result["result"].get("calculated_score", "?")
                    print(f"           imported {player}  score={score}")
                    total_imported += 1
            except Exception as e:
                print(f"           server error for {player}: {e}")
                total_errors += 1

    print()
    if args.dry_run:
        print(f"Done (dry run).  {total_submissions} submission(s) found across days {args.start_day}–{max_day}.")
    else:
        print(f"Done.  imported: {total_imported}  duplicates skipped: {total_duplicates}  errors: {total_errors}")


if __name__ == "__main__":
    main()
