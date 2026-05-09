#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi
BASE_URL="${BASE_URL:-http://localhost:8000}"
echo Base URL: ${BASE_URL}

# 11x11 board (row-major, 121 chars).
# Centre cell is (5,5). Layout (. = space for readability):
#
#   row 0:  ...........
#   row 1:  ...........
#   row 2:  ...........
#   row 3:  .....C.....
#   row 4:  .....A.....
#   row 5:  ...BOARD...
#   row 6:  .....D.....
#   row 7:  ...........
#   row 8:  ...........
#   row 9:  ...........
#   row 10: ...........
#
# Expected: horizontal word "BOARD" (centre row), vertical word "CAD" (col 5)

BOARD="           "  # row 0
BOARD+="           "  # row 1
BOARD+="           "  # row 2
BOARD+="     C     "  # row 3
BOARD+="     A     "  # row 4
BOARD+="   BOARD   "  # row 5  (centre; O is at col 5)
BOARD+="     D     "  # row 6
BOARD+="           "  # row 7
BOARD+="           "  # row 8
BOARD+="           "  # row 9
BOARD+="           "  # row 10

curl -s -L -X POST "$BASE_URL/rpc" \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"analyse\",\"params\":{\"board\":\"$BOARD\"},\"id\":1}" \
  | python3 -m json.tool
