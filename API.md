# Worcadian Game Server — API Reference

All game logic is exposed over JSON-RPC 2.0 endpoints. Static pages and an admin page are served at fixed HTTP routes.

---

## Transport

### HTTP Routes

| Method | Path          | Description                        |
|--------|---------------|------------------------------------|
| GET    | `/`           | Whatgame Studios home page         |
| GET    | `/worcadian`  | Worcadian game UI                  |
| GET    | `/14numbers`  | 14 Numbers game UI                 |
| GET    | `/admin`      | Admin page (static)                |
| POST   | `/rpc`        | Worcadian JSON-RPC 2.0 endpoint    |
| POST   | `/14rpc`      | 14 Numbers JSON-RPC 2.0 endpoint   |

### JSON-RPC 2.0

**Request format**
```json
{
  "jsonrpc": "2.0",
  "method": "<method-name>",
  "params": { },
  "id": 1
}
```

**Success response**
```json
{
  "jsonrpc": "2.0",
  "result": { },
  "id": 1
}
```

**Error response**
```json
{
  "jsonrpc": "2.0",
  "error": { "code": -32602, "message": "human-readable description" },
  "id": 1
}
```

Standard error codes:

| Code    | Meaning             |
|---------|---------------------|
| -32600  | Invalid Request     |
| -32601  | Method not found    |
| -32602  | Invalid params      |
| -32603  | Internal error      |

---

## Constants

### Worcadian

These values mirror the on-chain Solidity constants and are used in Worcadian game logic.

| Name                    | Value        | Description                                    |
|-------------------------|--------------|------------------------------------------------|
| `BOARD_SIZE`            | `11`         | Board is 11 × 11 = 121 characters             |
| `UNIX_TIME_GAME_START`  | `1774828800` | Monday 30 March 2026 00:00:00 UTC              |
| `SECONDS_PER_DAY`       | `86400`      |                                                |
| `PLUS_FOURTEEN`         | `50400`      | GMT+14 offset (Kiribati, Line Islands)         |
| `MINUS_TWELVE`          | `43200`      | GMT-12 offset (Baker and Howard Island)        |
| `LETTERS_IN_ALPHABET`   | `26`         | Starting score value                           |

### 14 Numbers

| Name                       | Value        | Description                             |
|----------------------------|--------------|-----------------------------------------|
| `UNIX_TIME_GAME_START`     | `1733011200` | Sunday 1 December 2024 00:00:00 UTC     |
| `SECONDS_PER_DAY`          | `86400`      |                                         |
| `PLUS_FOURTEEN`            | `50400`      | GMT+14 offset                           |
| `MINUS_TWELVE`             | `43200`      | GMT-12 offset                           |
| `MIN_TARGET_VALUE`         | `250`        | Minimum target number                   |
| `MAX_TARGET_VALUE`         | `1000`       | Upper bound for target generation (exclusive of 1000) |
| `MAX_NUMBERS`              | `5`          | Maximum numbers per expression          |
| `MAX_BRACKETS`             | `5`          | Maximum bracket pairs per expression    |

---

## Board Format

The board is a flat 121-character string, row-major (cell `(x, y)` is at index `y × 11 + x`).

- Occupied cells hold an uppercase letter `A`–`Z`.
- Empty cells hold a space (`0x20`).
- The centre cell is `(5, 5)` (index 60).
- Analysis starts at the centre and discovers all connected words via BFS.

**Seed word placement** — the seed word for a game day is always placed on the centre row (row 5), horizontally centred:
```
startX = (BOARD_SIZE - len(seed_word)) // 2
```

---

## Game Day Calculation

The current valid game day range accounts for the fact that different timezones see different calendar dates simultaneously.

```
max_day = (unix_now + PLUS_FOURTEEN  - GAME_START) // SECONDS_PER_DAY
min_day = (unix_now - MINUS_TWELVE   - GAME_START) // SECONDS_PER_DAY
```

A game day is **valid** if `min_day ≤ day ≤ max_day`.

---

## Scoring Algorithm

Mirrors the Solidity `ScoreV4.score()` function.

1. Start with `score = 26`.
2. For each word:
   - If the word is **not in the dictionary**: `score += 1` for every letter.
   - If the word **is in the dictionary**: for each letter `A`–`Z`, if that letter has not been seen before in any dictionary word, `score -= 1` and mark it used.
3. Return `score`. Lower is better; 0 is optimal.

---

## Methods

---

### Wordlist

#### `check`
Check whether words are in the wordlist. Words are uppercased before lookup.

**Params**
```json
{ "words": ["apple", "fig"] }
```

**Result**
```json
{ "APPLE": true, "FIG": false }
```

---

#### `add`
Add words to the wordlist. Words are uppercased before storage. Idempotent — existing words are reported but not duplicated.

**Params**
```json
{ "words": ["apple", "banana"] }
```

**Result**
```json
{ "added": ["APPLE", "BANANA"], "already_exists": [] }
```

---

### Seed Words

#### `seedwords.check`
Return the seed word for each requested game day. Returns `null` for days with no configured seed word.

**Params**
```json
{ "days": [1, 2, 99] }
```

**Result**
```json
{ "1": "GIPSY", "2": "PILES", "99": null }
```

---

### Game Day

#### `gameday.current`
Return the current valid game day range.

**Params** — `{}` (empty)

**Result**
```json
{ "min_day": 39, "max_day": 41 }
```

---

#### `gameday.check`
Check whether a specific game day is currently valid.

**Params**
```json
{ "day": 40 }
```

**Result**
```json
{ "valid": true, "requested_day": 40, "min_day": 39, "max_day": 41 }
```

---

### Board Analysis

#### `analyse`
Discover all connected words on a board starting from the centre cell. Returns word strings only — does not check the dictionary or calculate a score.

**Params**
```json
{ "board": "<121-character string>" }
```

**Result**
```json
{ "words": ["BOARD", "CAD"] }
```

Returns `{ "words": [] }` when the centre cell is empty.

---

#### `board.analyse`
Full analysis pipeline: word discovery + dictionary lookup + score calculation. Mirrors the Solidity `analyseBoard()` view function.

**Params**
```json
{ "board": "<121-character string>" }
```

**Result**
```json
{
  "score": 18,
  "words": ["BOARD", "CAD"],
  "in_dictionary": [true, false]
}
```

---

#### `score`
Calculate the score for an already-known word list and dictionary flags. Does not touch the board or database.

**Params**
```json
{
  "words": ["APPLE", "CAT", "ZORK"],
  "in_dictionary": [true, true, false]
}
```

**Result**
```json
{ "score": 24 }
```

---

### Game Submissions

#### `board.submit`
Submit a completed board for a game day. Mirrors the Solidity `submitBoard()` function.

**Validation steps (in order):**
1. `game_day` must be within the current valid range (`gameday.check`).
2. Board must be exactly 121 characters.
3. The seed word for `game_day` must be present at the correct position (centre row, horizontally centred).
4. Board is analysed, words checked against the dictionary, and score calculated.
5. If `score` is worse than the current best for the day, the submission is rejected as not competitive.
6. `score` is compared against the server-calculated score. A mismatch is recorded but does not block storage unless it is also not competitive.
7. Submission is stored.

**Lower score is better. 0 is optimal.**

**Params**
```json
{
  "game_day": 40,
  "score": 18,
  "board": "<121-character string>",
  "player": "alice"
}
```

**Result**
```json
{
  "status": "submitted",
  "submitted_score": 18,
  "calculated_score": 18,
  "words": ["GIPSY", "..."],
  "in_dictionary": [true, "..."]
}
```

**`status` values**

| Value                          | Meaning                                                                 |
|-------------------------------|-------------------------------------------------------------------------|
| `submitted`                   | Stored successfully                                                     |
| `not_competitive`             | `score` is worse than the current best; not stored                      |
| `seed_word_not_found`         | Seed word is not at the expected position; not stored                   |
| `score_mismatch`              | Client score ≠ server score, but stored using the server-calculated score |
| `score_mismatch_not_competitive` | Client score ≠ server score and not competitive; not stored          |

---

#### `board.import`
Import a historical submission without validating the game day range or seed word position. Used to backfill on-chain data. Idempotent — the same `(game_day, player, board)` triple is only stored once.

**Params**
```json
{
  "game_day": 3,
  "board": "<121-character string>",
  "player": "0xAbCd..."
}
```

**Result**
```json
{
  "status": "imported",
  "game_day": 3,
  "player": "0xAbCd...",
  "calculated_score": 22,
  "words": ["POSED", "..."],
  "in_dictionary": [true, "..."]
}
```

Returns `{ "status": "duplicate", "game_day": 3, "player": "0xAbCd..." }` if the record already exists.

---

#### `board.results`
Return the total submission count, best score, and all submissions at the best score for a game day. Mirrors the Solidity `getResults()` function.

**Params**
```json
{ "game_day": 40 }
```

**Result**
```json
{
  "num_submissions": 5,
  "best_score": 18,
  "submissions": [
    { "player": "alice", "board": "<121-character string>" }
  ]
}
```

Returns `{ "num_submissions": 0, "best_score": null, "submissions": [] }` when no submissions exist.

---

#### `board.submissions`
Return a paginated slice of submissions at a specific score tier. Mirrors the Solidity `getSubmissions()` function.

**Params**
```json
{
  "game_day": 40,
  "score": 18,
  "start_index": 0,
  "count": 20
}
```

**Result**
```json
{
  "total": 3,
  "submissions": [
    { "player": "alice", "board": "<121-character string>" }
  ]
}
```

---

### Check-In

#### `checkin.checkin`
Record a player session. Mirrors the Solidity `WorcadianCheckInV2.checkIn()`.

- `game_day` must be within the current valid range.
- The session counter (`num_sessions`) increments on every call.
- The unique-player counter (`num_players`) and `days_played` increment only the **first** time a player checks in on a given day.

**Params**
```json
{ "game_day": 40, "player": "alice" }
```

**Result**
```json
{
  "game_day": 40,
  "player": "alice",
  "days_played": 7,
  "is_new_day": true
}
```

`is_new_day: true` means this was the player's first session of the day (unique player count was incremented).

---

#### `checkin.days_played`
Return the total number of unique days a player has checked in. Mirrors `getDaysPlayed()`.

**Params**
```json
{ "player": "alice" }
```

**Result**
```json
{ "player": "alice", "days_played": 7 }
```

Returns `0` for unknown players.

---

#### `checkin.num_players`
Return the unique player count for a range of consecutive game days. Mirrors `getNumPlayers()`. Capped at 1 826 days.

**Params**
```json
{ "start_game_day": 38, "num_days": 5 }
```

**Result**
```json
{ "players": [12, 18, 21, 19, 15] }
```

Array is indexed from `start_game_day`; days with no check-ins return `0`.

---

#### `checkin.num_sessions`
Return the session count for a range of consecutive game days. Mirrors `getNumSessions()`. Capped at 1 826 days.

**Params**
```json
{ "start_game_day": 38, "num_days": 5 }
```

**Result**
```json
{ "sessions": [34, 52, 60, 48, 41] }
```

---

#### `checkin.total_players`
Return the total number of unique players who have ever checked in. Mirrors `getTotalPlayers()`.

**Params** — `{}` (empty)

**Result**
```json
{ "total": 142 }
```

---

#### `checkin.players`
Return a paginated slice of all-time players in order of first check-in. Mirrors `getPlayers()`.

**Params**
```json
{ "start_index": 0, "count": 20 }
```

**Result**
```json
{
  "total": 142,
  "players": ["alice", "bob", "0xAbCd..."]
}
```

---

---

# 14 Numbers — `/14rpc`

The `/14rpc` endpoint uses the same JSON-RPC 2.0 transport as `/rpc`. The same request/response envelope and error codes apply (see [Transport](#transport) above).

---

## 14 Numbers Game Rules

Players submit three arithmetic expressions. Each expression uses a subset of the allowed numbers (1–10, 25, 50, 75, 100) combined with `+`, `-`, `*`, `/`, and optional brackets. A number may not appear more than once within a single expression, and **no number may be shared across the three parts**. The score for each part is how close the result is to the target number for the day.

### Valid Numbers

`1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `25`, `50`, `75`, `100`

### Expression Rules

- Max 5 numbers per expression (`MAX_NUMBERS = 5`)
- Max 5 bracket pairs per expression (`MAX_BRACKETS = 5`)
- Intermediate and final results must be non-negative integers
- Division must produce a whole number
- Division by zero is rejected

### Scoring

```
points_single(target, result):
  if result == target: return 70
  diff = abs(target - result)
  if diff > 50: return 0
  return 50 - diff          # range: 1–49

total_score = points_single(target, result1)
            + points_single(target, result2)
            + points_single(target, result3)
```

Maximum possible score per submission: **210** (all three parts exactly equal the target).

### Target Number Generation

The target is deterministically derived from the game day using SHA-256 (mirrors the Solidity `getTargetValue` function):

```
seed   = sha256(big_endian_uint32(game_day) ++ uint32(0) ++ uint32(0))
count  = 0
loop:
  val = unpack_big_endian_uint32(sha256(seed ++ big_endian_uint32(count))[-4:]) % MAX_TARGET_VALUE
  count += 1
  if val >= MIN_TARGET_VALUE: return val
```

Target is always in the range **[250, 999]**.

---

## 14 Numbers Methods

---

### Game Day

#### `gameday.current`
Return the current valid game day range for 14 Numbers (game origin: 1 December 2024).

**Params** — `{}` (empty)

**Result**
```json
{ "min_day": 165, "max_day": 167 }
```

---

#### `gameday.check`
Check whether a specific 14 Numbers game day is currently valid.

**Params**
```json
{ "day": 166 }
```

**Result**
```json
{ "valid": true, "requested_day": 166, "min_day": 165, "max_day": 167 }
```

---

### Target

#### `target.get`
Return the target number for a given game day.

**Params**
```json
{ "game_day": 166 }
```

**Result**
```json
{ "target": 743 }
```

---

### Solutions

#### `solution.submit`
Submit a three-part solution for a game day.

**Validation steps (in order):**
1. `game_day` must be within the current valid range.
2. Each of `part1`, `part2`, `part3` is evaluated; any parse or arithmetic error is rejected.
3. No number may appear in more than one part.
4. Score is calculated. If it is lower than the current best score for the day, the submission is rejected as not competitive.
5. If the exact same `(part1, part2, part3)` triple already exists for the day it is returned as a duplicate (not stored again).
6. Submission is stored.

**Higher score is better. 210 is optimal.**

**Params**
```json
{
  "game_day": 166,
  "user_id": "alice",
  "part1": "7*100",
  "part2": "50+25",
  "part3": "9-1"
}
```

**Result**
```json
{
  "status": "submitted",
  "score": 185,
  "best_score": 185,
  "result1": 700,
  "result2": 75,
  "result3": 8
}
```

**`status` values**

| Value             | Meaning                                                              |
|-------------------|----------------------------------------------------------------------|
| `submitted`       | Stored successfully                                                  |
| `not_competitive` | Score is lower than the current best for the day; not stored         |
| `duplicate`       | Identical `(part1, part2, part3)` already exists; not stored again  |

---

#### `solution.results`
Return the best score and all submissions at that score for a game day (up to 20).

**Params**
```json
{ "game_day": 166 }
```

**Result**
```json
{
  "game_day": 166,
  "best_score": 185,
  "solutions": [
    {
      "user_id": "alice",
      "part1": "7*100", "part2": "50+25", "part3": "9-1",
      "result1": 700, "result2": 75, "result3": 8,
      "score": 185
    }
  ]
}
```

Returns `{ "game_day": 166, "best_score": null, "solutions": [] }` when no submissions exist.

---

### Check-In (14 Numbers)

The check-in methods on `/14rpc` are identical in behaviour to those on `/rpc` but track 14 Numbers players and sessions separately using the 14 Numbers game origin date.

#### `checkin.checkin`

**Params**
```json
{ "game_day": 166, "player": "alice" }
```

**Result**
```json
{ "game_day": 166, "player": "alice", "days_played": 3, "is_new_day": true }
```

---

#### `checkin.days_played`

**Params**
```json
{ "player": "alice" }
```

**Result**
```json
{ "player": "alice", "days_played": 3 }
```

---

#### `checkin.num_players`

**Params**
```json
{ "start_game_day": 164, "num_days": 3 }
```

**Result**
```json
{ "players": [8, 12, 10] }
```

---

#### `checkin.num_sessions`

**Params**
```json
{ "start_game_day": 164, "num_days": 3 }
```

**Result**
```json
{ "sessions": [20, 35, 28] }
```

---

#### `checkin.total_players`

**Params** — `{}` (empty)

**Result**
```json
{ "total": 47 }
```

---

#### `checkin.players`

**Params**
```json
{ "start_index": 0, "count": 20 }
```

**Result**
```json
{ "total": 47, "players": ["alice", "bob"] }
```
