#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo Base URL: ${BASE_URL}

DAY="${1:-0}"

echo "Checking game day: $DAY"
curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"gameday.check\",\"params\":{\"day\":$DAY},\"id\":1}" \
  | python3 -m json.tool
