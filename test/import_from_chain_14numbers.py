#!/usr/bin/env python3
"""
Import on-chain 14Numbers solutions into the server.

For each game day from 0 to the current game day, calls getAllSolutions(uint256)
on the Numbers14 contract via the Immutable zkEVM RPC, then imports every
solution into the server via the solution.submitbypass RPC API.

Usage:
    python3 import_from_chain_14numbers.py [--base-url URL] [--rpc-url URL] [--dry-run] [--start-day N]

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

GAME_START      = 1733011200   # December 1, 2024 00:00:00 UTC
SECONDS_PER_DAY = 86400
PLUS_FOURTEEN   = 50400        # GMT+14 offset

CONTRACT_ADDRESS = "0xe2E762770156FfE253C49Da6E008b4bECCCf2812"

ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "_gameDay", "type": "uint256"}],
        "name": "getAllSolutions",
        "outputs": [
            {"internalType": "uint256", "name": "_points", "type": "uint256"},
            {
                "components": [
                    {"internalType": "bytes",   "name": "combinedSolution", "type": "bytes"},
                    {"internalType": "address", "name": "player",           "type": "address"},
                ],
                "internalType": "struct ExtraSolution[]",
                "name": "_solutions",
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
        f"{base_url}/14rpc",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def parse_combined_solution(combined: bytes) -> tuple[str, str, str]:
    decoded = combined.decode("utf-8")
    parts = decoded.split("=", 2)
    if len(parts) != 3:
        raise ValueError(f"expected 3 parts separated by '=', got {len(parts)}: {decoded!r}")
    return parts[0], parts[1], parts[2]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Import on-chain 14Numbers solutions")
    parser.add_argument("--base-url",  default=os.getenv("BASE_URL", "http://localhost:8000"))
    parser.add_argument("--rpc-url",   default=os.getenv("RPC_URL",  "https://rpc.immutable.com"))
    parser.add_argument("--start-day", type=int, default=0, help="First game day to fetch (default: 0)")
    parser.add_argument("--dry-run",   action="store_true", help="Fetch chain data but do not write to server")
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

    total_solutions = 0
    total_imported = 0
    total_skipped = 0
    total_errors = 0

    for day in range(args.start_day, max_day + 1):
        try:
            points, solutions = contract.functions.getAllSolutions(day).call()
        except Exception as e:
            print(f"  day {day:4d}  chain error: {e}")
            total_errors += 1
            continue

        if not solutions:
            print(f"  day {day:4d}  no solutions")
            continue

        print(f"  day {day:4d}  {len(solutions)} solution(s), best score {points}")

        for sol in solutions:
            combined_bytes, player = sol[0], sol[1]
            total_solutions += 1

            try:
                part1, part2, part3 = parse_combined_solution(combined_bytes)
            except ValueError as e:
                print(f"           parse error for {player}: {e}")
                total_errors += 1
                continue

            if args.dry_run:
                print(f"           [dry run] would import player={player} parts={part1!r}, {part2!r}, {part3!r}")
                continue

            try:
                result = server_rpc(args.base_url, "solution.submitbypass", {
                    "game_day": day,
                    "user_id": player,
                    "part1": part1,
                    "part2": part2,
                    "part3": part3,
                })
                if "error" in result:
                    print(f"           import error for {player}: {result['error']['message']}")
                    total_errors += 1
                elif result["result"]["status"] in ("duplicate", "not_competitive"):
                    total_skipped += 1
                else:
                    score = result["result"].get("score", "?")
                    print(f"           imported {player}  score={score}")
                    total_imported += 1
            except Exception as e:
                print(f"           server error for {player}: {e}")
                total_errors += 1

    print()
    if args.dry_run:
        print(f"Done (dry run).  {total_solutions} solution(s) found across days {args.start_day}–{max_day}.")
    else:
        print(f"Done.  imported: {total_imported}  skipped: {total_skipped}  errors: {total_errors}")


if __name__ == "__main__":
    main()
