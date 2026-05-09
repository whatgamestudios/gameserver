#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo Base URL: ${BASE_URL}

# Requires a seed word to be set for the game day first (see seedwords_set.sh).
# The seed word for game_day 1 must be centred on row 5 of the board.
# For a 3-letter seed word: startX = (11-3)/2 = 4, so cols 4-6 of row 5.
# Board below has "CAT" at cols 4-6 of row 5 (centre).
GAME_DAY="${1:-1}"
PLAYER="${2:-testplayer}"
SCORE="${3:-26}"

BOARD="           "
BOARD+="           "
BOARD+="           "
BOARD+="           "
BOARD+="           "
BOARD+="    CAT    "
BOARD+="           "
BOARD+="           "
BOARD+="           "
BOARD+="           "
BOARD+="           "

curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"board.submit\",\"params\":{\"game_day\":$GAME_DAY,\"score\":$SCORE,\"board\":\"$BOARD\",\"player\":\"$PLAYER\"},\"id\":1}" \
  | python3 -m json.tool
