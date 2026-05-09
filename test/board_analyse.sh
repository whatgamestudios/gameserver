#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo Base URL: ${BASE_URL}

# 11x11 board with BOARD horizontal at centre row (row 5), CAD vertical through col 5.
# Returns words, in_dictionary flags, and calculated score.
BOARD="           "
BOARD+="           "
BOARD+="           "
BOARD+="     C     "
BOARD+="     A     "
BOARD+="   BOARD   "
BOARD+="     D     "
BOARD+="           "
BOARD+="           "
BOARD+="           "
BOARD+="           "

curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"board.analyse\",\"params\":{\"board\":\"$BOARD\"},\"id\":1}" \
  | python3 -m json.tool
