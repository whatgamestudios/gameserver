#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo Base URL: ${BASE_URL}

# APPLE (dict): A,P,L,E = 4 new letters → score 26-4=22
# CAT (dict):   C,T = 2 new letters (A already used) → score 22-2=20
# ZORK (not dict): 4 letters → score 20+4=24
curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"score","params":{"words":["APPLE","CAT","ZORK"],"in_dictionary":[true,true,false]},"id":1}' \
  | python3 -m json.tool
