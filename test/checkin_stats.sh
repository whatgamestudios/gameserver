#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo Base URL: ${BASE_URL}

PLAYER="${1:-alice}"
START_DAY="${2:-0}"
NUM_DAYS="${3:-7}"

echo "=== Days played by '$PLAYER' ==="
curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"checkin.days_played\",\"params\":{\"player\":\"$PLAYER\"},\"id\":1}" \
  | python3 -m json.tool

echo ""
echo "=== Daily stats: days $START_DAY to $((START_DAY + NUM_DAYS - 1)) ==="
curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"checkin.num_players\",\"params\":{\"start_game_day\":$START_DAY,\"num_days\":$NUM_DAYS},\"id\":2}" \
  | python3 -m json.tool

curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"checkin.num_sessions\",\"params\":{\"start_game_day\":$START_DAY,\"num_days\":$NUM_DAYS},\"id\":3}" \
  | python3 -m json.tool

echo ""
echo "=== Total unique players ==="
curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"checkin.total_players\",\"params\":{},\"id\":4}" \
  | python3 -m json.tool

echo ""
echo "=== Player list (first 20) ==="
curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"checkin.players\",\"params\":{\"start_index\":0,\"count\":20},\"id\":5}" \
  | python3 -m json.tool
