# Tests

Scripts that exercise the JSON RPC API. Shell scripts use `curl`; Python scripts use the standard library plus `web3` where noted.

All scripts read `BASE_URL` from the environment and fall back to `http://localhost:8000`.

## Prerequisites

The server must be running. To start it locally:

```bash
uvicorn api.index:app --reload
```

---

## Environment

| Variable  | Default                        | Description                        |
|-----------|--------------------------------|------------------------------------|
| `BASE_URL` | `http://localhost:8000`       | Target server for all scripts      |
| `RPC_URL`  | `https://rpc.immutable.com`   | Ethereum RPC (`import_from_chain.py` only) |

---

## Wordlist

### `add.sh`
Adds `apple`, `banana`, and `cherry` to the wordlist.
```bash
./test/add.sh
```

### `add1.sh`
Adds the single word `ok` to the wordlist.
```bash
./test/add1.sh
```

### `check.sh`
Checks whether `apple`, `fig`, and `banana` are in the wordlist.
```bash
./test/check.sh
```

### `load_wordlist.py`
Reads `game_words.txt` from the project root (one word per line) and loads every word into the wordlist in batches via the `add` method. Words are uppercased automatically. Safe to run multiple times — already-present words are reported but not duplicated.

```bash
python3 test/load_wordlist.py

# Target a deployed server
BASE_URL=https://your-app.vercel.app python3 test/load_wordlist.py

# Use a different file
python3 test/load_wordlist.py --file /path/to/words.txt

# Change batch size (default 200)
python3 test/load_wordlist.py --batch-size 100

# Preview without sending
python3 test/load_wordlist.py --dry-run
```

---

## Seed Words

### `seedwords_set.sh`
Sets seed words for days 1, 2, and 3 (`apple`, `banana`, `cherry`).
```bash
./test/seedwords_set.sh
```

### `seedwords_check.sh`
Checks the seed words for days 1, 2, 3, and 99 (day 99 should return `null`).
```bash
./test/seedwords_check.sh
```

### `load_seedwords.py`
Loads the full production seed word list (1 000 words) into the server via the `seedwords.set` method, starting at day 1 by default.

```bash
python3 test/load_seedwords.py

# Target a deployed server
BASE_URL=https://your-app.vercel.app python3 test/load_seedwords.py

# Start from a different day number
python3 test/load_seedwords.py --start-day 0

# Change batch size (default 50)
python3 test/load_seedwords.py --batch-size 100

# Preview first batch without sending
python3 test/load_seedwords.py --dry-run
```

---

## Game Day

### `gameday_current.sh`
Returns the current valid game-day range (min and max) across all timezones.
```bash
./test/gameday_current.sh
```

### `gameday_check.sh`
Checks whether a given day number is currently valid. Accepts the day as an argument (default: `0`).
```bash
./test/gameday_check.sh 42
```

---

## Board Analysis

### `analyse.sh`
Calls the `analyse` method (word discovery only) on a hardcoded test board containing `BOARD` and `CAD`.
```bash
./test/analyse.sh
```

### `score.sh`
Calls the `score` method with `APPLE` and `CAT` (in dictionary) and `ZORK` (not in dictionary). Expected score: 24.
```bash
./test/score.sh
```

### `board_analyse.sh`
Calls the `board.analyse` method — full pipeline: word discovery + dictionary lookup + score calculation — on a test board.
```bash
./test/board_analyse.sh
```

---

## Game Submissions

### `board_submit.sh`
Submits a board for a given game day. Requires a seed word to be configured for that day first (see `seedwords_set.sh` or `load_seedwords.py`).

Arguments (all optional): `game_day` (default: `1`), `player` (default: `testplayer`), `score` (default: `26`).

The board used has `CAT` centred on row 5, which matches a 3-letter seed word for day 1 when loaded via `load_seedwords.py`.

```bash
./test/board_submit.sh
./test/board_submit.sh 2 alice 24
```

### `board_results.sh`
Returns the best score and all best-scoring submissions for a game day. Accepts the game day as an argument (default: `1`).
```bash
./test/board_results.sh
./test/board_results.sh 5
```

---

## Check-In

### `checkin.sh`
Records a check-in for a player on a given game day. Arguments: `game_day` (default: `0`), `player` (default: `alice`).

A check-in increments the session count every call, and increments the unique-player count only the first time a player checks in on a given day.

```bash
./test/checkin.sh
./test/checkin.sh 3 bob
```

### `checkin_stats.sh`
Runs all five read methods in one script: `checkin.days_played`, `checkin.num_players`, `checkin.num_sessions`, `checkin.total_players`, and `checkin.players`.

Arguments: `player` (default: `alice`), `start_day` (default: `0`), `num_days` (default: `7`).

```bash
./test/checkin_stats.sh
./test/checkin_stats.sh bob 1 14
```

---

## Chain Import

### `import_from_chain.py`
Fetches all on-chain submissions from the WorcadianGameV4 contract (`0xBe3558861DE7BB699b9a929d1eA5503dCcb329cD`) via the Immutable zkEVM RPC, then imports each submission into the server using the `board.import` method.

Iterates game days from `--start-day` (default: `0`) up to the current maximum game day. Duplicate submissions (same day + player + board) are skipped automatically, so the script is safe to run multiple times.

Requires `web3` (`pip install web3`).

```bash
python3 test/import_from_chain.py

# Target a deployed server
BASE_URL=https://your-app.vercel.app python3 test/import_from_chain.py

# Use a different RPC endpoint
RPC_URL=https://rpc.immutable.com python3 test/import_from_chain.py

# Resume from a specific day
python3 test/import_from_chain.py --start-day 5

# Fetch chain data and print without writing to the server
python3 test/import_from_chain.py --dry-run
```
