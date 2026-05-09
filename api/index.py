import os
import time
from typing import Any, Dict, List, Optional, Union

import sqlalchemy as sa
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = sa.create_engine(DATABASE_URL, connect_args=_connect_args)

BOARD_SIZE = 11

# ── Board analysis (mirrors AnalyseBoard.sol / AnalyseBoard.cs) ───────────────

class _WordPos:
    __slots__ = ("start_x", "start_y", "end_x", "end_y")
    def __init__(self, start_x, start_y, end_x, end_y):
        self.start_x = start_x; self.start_y = start_y
        self.end_x = end_x;     self.end_y = end_y


def _cell_occupied(b: str, x: int, y: int) -> bool:
    return 'A' <= b[y * BOARD_SIZE + x] <= 'Z'


def _find_horizontal_word(b: str, x: int, y: int, analysed_h: list) -> _WordPos:
    while x > 0 and _cell_occupied(b, x - 1, y):
        x -= 1
    start_x = x
    while x < BOARD_SIZE - 1 and _cell_occupied(b, x + 1, y):
        x += 1
    end_x = x
    for i in range(start_x, end_x + 1):
        analysed_h[i][y] = True
    return _WordPos(start_x, y, end_x, y)


def _find_vertical_word(b: str, x: int, y: int, analysed_v: list) -> _WordPos:
    while y > 0 and _cell_occupied(b, x, y - 1):
        y -= 1
    start_y = y
    while y < BOARD_SIZE - 1 and _cell_occupied(b, x, y + 1):
        y += 1
    end_y = y
    for i in range(start_y, end_y + 1):
        analysed_v[x][i] = True
    return _WordPos(x, start_y, x, end_y)


def _extract_word(b: str, pos: _WordPos) -> str:
    if pos.start_y == pos.end_y:  # horizontal
        return b[pos.start_y * BOARD_SIZE + pos.start_x:
                 pos.start_y * BOARD_SIZE + pos.end_x + 1]
    # vertical
    return ''.join(b[(pos.start_y + i) * BOARD_SIZE + pos.start_x]
                   for i in range(pos.end_y - pos.start_y + 1))


def _analyse_board(board: str) -> list:
    """BFS word discovery mirroring AnalyseBoard.analyse()."""
    center = BOARD_SIZE // 2  # 5

    if not _cell_occupied(board, center, center):
        return []

    # analysed_h[x][y], analysed_v[x][y]
    analysed_h = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    analysed_v = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    pending_h: list[_WordPos] = []
    pending_v: list[_WordPos] = []
    found_words: list[str] = []

    first = _find_horizontal_word(board, center, center, analysed_h)
    found_words.append(_extract_word(board, first))
    pending_h.append(first)

    h_idx = v_idx = 0

    while h_idx < len(pending_h) or v_idx < len(pending_v):
        # findVerticalWords: for every column of each horizontal word,
        # branch into any unanalysed vertical neighbour above or below.
        while h_idx < len(pending_h):
            hw = pending_h[h_idx]; h_idx += 1
            for i in range(hw.end_x - hw.start_x + 1):
                x, y = hw.start_x + i, hw.start_y
                exists = (y > 0 and _cell_occupied(board, x, y - 1) and not analysed_v[x][y - 1]) or \
                         (y < BOARD_SIZE - 1 and _cell_occupied(board, x, y + 1) and not analysed_v[x][y + 1])
                if exists:
                    vw = _find_vertical_word(board, x, y, analysed_v)
                    found_words.append(_extract_word(board, vw))
                    pending_v.append(vw)

        # findHorizontalWords: for every row of each vertical word,
        # branch into any unanalysed horizontal neighbour left or right.
        while v_idx < len(pending_v):
            vw = pending_v[v_idx]; v_idx += 1
            for i in range(vw.end_y - vw.start_y + 1):
                x, y = vw.start_x, vw.start_y + i
                exists = (x > 0 and _cell_occupied(board, x - 1, y) and not analysed_h[x - 1][y]) or \
                         (x < BOARD_SIZE - 1 and _cell_occupied(board, x + 1, y) and not analysed_h[x + 1][y])
                if exists:
                    hw = _find_horizontal_word(board, x, y, analysed_h)
                    found_words.append(_extract_word(board, hw))
                    pending_h.append(hw)

    return found_words


# GMT Monday March 30, 2026 00:00:00 UTC — mirrors Solidity UNIX_TIME_GAME_START
_GAME_START = 1774828800
_SECONDS_PER_DAY = 86400
_PLUS_FOURTEEN = 50400   # GMT+14: Kiribati Line Islands
_MINUS_TWELVE = 43200    # GMT-12: Baker and Howard Island


def _calculate_score(words: list, in_dictionary: list) -> int:
    """Mirror of Solidity score(): starts at 26, unique dict letters decrement, non-dict letters increment."""
    used = [False] * 26
    current_score = 26
    for word, in_dic in zip(words, in_dictionary):
        for ch in word:
            if not in_dic:
                current_score += 1
            else:
                code = ord(ch)
                if 0x41 <= code <= 0x5A:  # uppercase A-Z
                    idx = code - 0x41
                    if not used[idx]:
                        current_score -= 1
                        used[idx] = True
    return current_score


def _is_seed_word_on_board(board: str, seed_word: str) -> bool:
    """Mirror of Solidity _isSeedWordOnBoard(): seed word must sit on centre row, horizontally centred."""
    word_len = len(seed_word)
    if word_len == 0 or word_len > BOARD_SIZE:
        return False
    start_x = (BOARD_SIZE - word_len) // 2
    row = BOARD_SIZE // 2
    for i, ch in enumerate(seed_word):
        if board[row * BOARD_SIZE + start_x + i] != ch:
            return False
    return True


def _check_words_in_db(words: list) -> list:
    """Bulk dictionary lookup, mirrors Solidity _checkWords() / IWorcadianWordList.inWordListBulk()."""
    if not words:
        return []
    with engine.connect() as conn:
        rows = conn.execute(
            sa.select(wordlist.c.word).where(wordlist.c.word.in_(words))
        ).fetchall()
    found = {row[0] for row in rows}
    return [w in found for w in words]


def _current_game_days() -> tuple[int, int]:
    """Return (min_day, max_day) for the current moment, matching determineCurrentGameDays()."""
    now = int(time.time())
    max_day = (now + _PLUS_FOURTEEN - _GAME_START) // _SECONDS_PER_DAY
    min_day = (now - _MINUS_TWELVE - _GAME_START) // _SECONDS_PER_DAY
    return min_day, max_day


metadata = sa.MetaData()
wordlist = sa.Table(
    "wordlist",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("word", sa.String, unique=True, nullable=False),
)
seedwords = sa.Table(
    "seedwords",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("day", sa.Integer, unique=True, nullable=False),
    sa.Column("word", sa.String, nullable=False),
)
submissions = sa.Table(
    "submissions",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("game_day", sa.Integer, nullable=False),
    sa.Column("score", sa.Integer, nullable=False),
    sa.Column("player", sa.String, nullable=False),
    sa.Column("board", sa.String, nullable=False),
)
player_stats = sa.Table(
    "player_stats",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),  # insertion order = allPlayers order
    sa.Column("player", sa.String, unique=True, nullable=False),
    sa.Column("most_recent_game_day", sa.Integer, nullable=False),
    sa.Column("days_played", sa.Integer, nullable=False),
)
daily_stats = sa.Table(
    "daily_stats",
    metadata,
    sa.Column("game_day", sa.Integer, primary_key=True),
    sa.Column("num_players", sa.Integer, nullable=False, default=0),
    sa.Column("num_sessions", sa.Integer, nullable=False, default=0),
)
metadata.create_all(engine)

_FIVE_YEARS_OF_DAYS = 1826  # mirrors Solidity FIVE_YEARS_OF_DAYS

app = FastAPI()


class RpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


def _error(code: int, message: str, req_id: Any = None) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": req_id})


def _result(result: Any, req_id: Any = None) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "result": result, "id": req_id})


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Whatgame Studios</title>
</head>
<body>
  <h1>Whatgame Studios</h1>
  <a href="/worcadian">Worcadian</a>
</body>
</html>"""


@app.get("/worcadian", response_class=HTMLResponse)
def worcadian():
    return HTML


@app.post("/rpc")
def rpc(req: RpcRequest):
    try:
        return _rpc(req)
    except Exception as exc:
        return _error(-32603, f"Internal error: {exc}", req.id)


def _rpc(req: RpcRequest):
    if req.jsonrpc != "2.0":
        return _error(-32600, "Invalid Request", req.id)

    if req.method == "check":
        words = (req.params or {}).get("words")
        if not isinstance(words, list) or not words:
            return _error(-32602, "params.words must be a non-empty list of strings", req.id)
        words = [w.upper() for w in words]

        with engine.connect() as conn:
            rows = conn.execute(
                sa.select(wordlist.c.word).where(wordlist.c.word.in_(words))
            ).fetchall()
        found = {row[0] for row in rows}
        return _result({w: (w in found) for w in words}, req.id)

    elif req.method == "add":
        words = (req.params or {}).get("words")
        if not isinstance(words, list) or not words:
            return _error(-32602, "params.words must be a non-empty list of strings", req.id)
        words = [w.upper() for w in words]

        with engine.begin() as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    sa.select(wordlist.c.word).where(wordlist.c.word.in_(words))
                ).fetchall()
            }
            new_words = [w for w in words if w not in existing]
            if new_words:
                conn.execute(wordlist.insert(), [{"word": w} for w in new_words])

        already_exists = [w for w in words if w in existing]
        return _result({"added": new_words, "already_exists": already_exists}, req.id)

    elif req.method == "seedwords.set":
        entries = (req.params or {}).get("entries")
        if not isinstance(entries, list) or not entries:
            return _error(-32602, "params.entries must be a non-empty list of {day, word} objects", req.id)
        for e in entries:
            if not isinstance(e.get("day"), int) or not isinstance(e.get("word"), str):
                return _error(-32602, "each entry must have an integer 'day' and a string 'word'", req.id)
        entries = [{"day": e["day"], "word": e["word"].upper()} for e in entries]

        with engine.begin() as conn:
            existing_days = {
                row[0]
                for row in conn.execute(
                    sa.select(seedwords.c.day).where(seedwords.c.day.in_([e["day"] for e in entries]))
                ).fetchall()
            }
            for e in entries:
                if e["day"] in existing_days:
                    conn.execute(
                        seedwords.update().where(seedwords.c.day == e["day"]).values(word=e["word"])
                    )
                else:
                    conn.execute(seedwords.insert().values(day=e["day"], word=e["word"]))

        return _result({"set": [e["day"] for e in entries]}, req.id)

    elif req.method == "analyse":
        board = (req.params or {}).get("board")
        if not isinstance(board, str):
            return _error(-32602, "params.board must be a string", req.id)
        if len(board) != BOARD_SIZE * BOARD_SIZE:
            return _error(-32602, f"params.board must be exactly {BOARD_SIZE * BOARD_SIZE} characters", req.id)
        return _result({"words": _analyse_board(board)}, req.id)

    elif req.method == "score":
        words = (req.params or {}).get("words")
        in_dictionary = (req.params or {}).get("in_dictionary")
        if not isinstance(words, list) or not isinstance(in_dictionary, list):
            return _error(-32602, "params.words and params.in_dictionary must be arrays", req.id)
        if len(words) != len(in_dictionary):
            return _error(-32602, "params.words and params.in_dictionary must have the same length", req.id)
        if not all(isinstance(w, str) for w in words):
            return _error(-32602, "all values in params.words must be strings", req.id)
        if not all(isinstance(v, bool) for v in in_dictionary):
            return _error(-32602, "all values in params.in_dictionary must be booleans", req.id)
        return _result({"score": _calculate_score(words, in_dictionary)}, req.id)

    elif req.method == "gameday.current":
        min_day, max_day = _current_game_days()
        return _result({"min_day": min_day, "max_day": max_day}, req.id)

    elif req.method == "gameday.check":
        day = (req.params or {}).get("day")
        if not isinstance(day, int):
            return _error(-32602, "params.day must be an integer", req.id)
        min_day, max_day = _current_game_days()
        valid = min_day <= day <= max_day
        return _result({"valid": valid, "requested_day": day, "min_day": min_day, "max_day": max_day}, req.id)

    elif req.method == "seedwords.check":
        days = (req.params or {}).get("days")
        if not isinstance(days, list) or not days:
            return _error(-32602, "params.days must be a non-empty list of integers", req.id)
        if not all(isinstance(d, int) for d in days):
            return _error(-32602, "all values in params.days must be integers", req.id)

        with engine.connect() as conn:
            rows = conn.execute(
                sa.select(seedwords.c.day, seedwords.c.word).where(seedwords.c.day.in_(days))
            ).fetchall()
        found = {row[0]: row[1] for row in rows}
        return _result({d: found.get(d) for d in days}, req.id)

    elif req.method == "board.analyse":
        board = (req.params or {}).get("board")
        if not isinstance(board, str):
            return _error(-32602, "params.board must be a string", req.id)
        if len(board) != BOARD_SIZE * BOARD_SIZE:
            return _error(-32602, f"params.board must be exactly {BOARD_SIZE * BOARD_SIZE} characters", req.id)
        words = _analyse_board(board)
        in_dictionary = _check_words_in_db(words)
        calculated_score = _calculate_score(words, in_dictionary)
        return _result({"score": calculated_score, "words": words, "in_dictionary": in_dictionary}, req.id)

    elif req.method == "board.submit":
        params = req.params or {}
        game_day = params.get("game_day")
        submitted_score = params.get("score")
        board = params.get("board")
        player = params.get("player")
        if not isinstance(game_day, int):
            return _error(-32602, "params.game_day must be an integer", req.id)
        if not isinstance(submitted_score, int):
            return _error(-32602, "params.score must be an integer", req.id)
        if not isinstance(board, str):
            return _error(-32602, "params.board must be a string", req.id)
        if not isinstance(player, str) or not player.strip():
            return _error(-32602, "params.player must be a non-empty string", req.id)
        if len(board) != BOARD_SIZE * BOARD_SIZE:
            return _error(-32602, f"params.board must be exactly {BOARD_SIZE * BOARD_SIZE} characters", req.id)

        # Mirror checkGameDay()
        min_day, max_day = _current_game_days()
        if not (min_day <= game_day <= max_day):
            return _error(-32602, f"game_day {game_day} is not valid (valid range: {min_day}–{max_day})", req.id)

        # Mirror getSeedWord() + _isSeedWordOnBoard()
        with engine.connect() as conn:
            seed_row = conn.execute(
                sa.select(seedwords.c.word).where(seedwords.c.day == game_day)
            ).fetchone()
        if seed_row is None:
            return _error(-32602, f"No seed word configured for game day {game_day}", req.id)
        seed_word = seed_row[0]
        if not _is_seed_word_on_board(board, seed_word):
            return _result({"status": "seed_word_not_found", "seed_word": seed_word}, req.id)

        # Mirror analyse() + _checkWords() + score()
        words = _analyse_board(board)
        in_dictionary = _check_words_in_db(words)
        calculated_score = _calculate_score(words, in_dictionary)

        # Mirror early competitiveness check (lower score is better)
        with engine.connect() as conn:
            day_count = conn.execute(
                sa.select(sa.func.count()).select_from(submissions).where(submissions.c.game_day == game_day)
            ).scalar() or 0
            best_score = conn.execute(
                sa.select(sa.func.min(submissions.c.score)).where(submissions.c.game_day == game_day)
            ).scalar()

        if day_count > 0 and submitted_score > best_score:
            return _result({"status": "not_competitive", "submitted_score": submitted_score,
                            "best_score": best_score, "calculated_score": calculated_score,
                            "words": words, "in_dictionary": in_dictionary}, req.id)

        score_mismatch = calculated_score != submitted_score
        if score_mismatch and day_count > 0 and calculated_score > best_score:
            return _result({"status": "score_mismatch_not_competitive", "submitted_score": submitted_score,
                            "calculated_score": calculated_score, "best_score": best_score,
                            "words": words, "in_dictionary": in_dictionary}, req.id)

        with engine.begin() as conn:
            conn.execute(submissions.insert().values(
                game_day=game_day, score=calculated_score,
                player=player.strip(), board=board,
            ))

        status = "score_mismatch" if score_mismatch else "submitted"
        return _result({"status": status, "submitted_score": submitted_score,
                        "calculated_score": calculated_score,
                        "words": words, "in_dictionary": in_dictionary}, req.id)

    elif req.method == "board.results":
        game_day = (req.params or {}).get("game_day")
        if not isinstance(game_day, int):
            return _error(-32602, "params.game_day must be an integer", req.id)
        with engine.connect() as conn:
            day_count = conn.execute(
                sa.select(sa.func.count()).select_from(submissions).where(submissions.c.game_day == game_day)
            ).scalar() or 0
            if day_count == 0:
                return _result({"num_submissions": 0, "best_score": None, "submissions": []}, req.id)
            best_score = conn.execute(
                sa.select(sa.func.min(submissions.c.score)).where(submissions.c.game_day == game_day)
            ).scalar()
            rows = conn.execute(
                sa.select(submissions.c.player, submissions.c.board)
                .where(submissions.c.game_day == game_day)
                .where(submissions.c.score == best_score)
            ).fetchall()
        return _result({"num_submissions": day_count, "best_score": best_score,
                        "submissions": [{"player": r[0], "board": r[1]} for r in rows]}, req.id)

    elif req.method == "board.submissions":
        params = req.params or {}
        game_day = params.get("game_day")
        score_tier = params.get("score")
        start_index = params.get("start_index", 0)
        count = params.get("count", 20)
        if not isinstance(game_day, int) or not isinstance(score_tier, int):
            return _error(-32602, "params.game_day and params.score must be integers", req.id)
        with engine.connect() as conn:
            total = conn.execute(
                sa.select(sa.func.count()).select_from(submissions)
                .where(submissions.c.game_day == game_day)
                .where(submissions.c.score == score_tier)
            ).scalar() or 0
            rows = conn.execute(
                sa.select(submissions.c.player, submissions.c.board)
                .where(submissions.c.game_day == game_day)
                .where(submissions.c.score == score_tier)
                .offset(start_index).limit(count)
            ).fetchall()
        return _result({"total": total,
                        "submissions": [{"player": r[0], "board": r[1]} for r in rows]}, req.id)

    elif req.method == "checkin.checkin":
        params = req.params or {}
        game_day = params.get("game_day")
        player = params.get("player")
        if not isinstance(game_day, int):
            return _error(-32602, "params.game_day must be an integer", req.id)
        if not isinstance(player, str) or not player.strip():
            return _error(-32602, "params.player must be a non-empty string", req.id)
        player = player.strip()

        min_day, max_day = _current_game_days()
        if not (min_day <= game_day <= max_day):
            return _error(-32602, f"game_day {game_day} is not valid (valid range: {min_day}–{max_day})", req.id)

        with engine.begin() as conn:
            # Ensure daily_stats row exists, then atomically increment sessions
            if not conn.execute(
                sa.select(sa.func.count()).select_from(daily_stats)
                .where(daily_stats.c.game_day == game_day)
            ).scalar():
                conn.execute(daily_stats.insert().values(game_day=game_day, num_players=0, num_sessions=0))
            conn.execute(
                daily_stats.update().where(daily_stats.c.game_day == game_day)
                .values(num_sessions=daily_stats.c.num_sessions + 1)
            )

            stats = conn.execute(
                sa.select(player_stats).where(player_stats.c.player == player)
            ).fetchone()

            current_days = stats[3] if stats else 0        # days_played
            current_recent = stats[2] if stats else 0      # most_recent_game_day
            is_new_day = (current_days == 0 or game_day > current_recent)

            if is_new_day:
                conn.execute(
                    daily_stats.update().where(daily_stats.c.game_day == game_day)
                    .values(num_players=daily_stats.c.num_players + 1)
                )
                new_days = current_days + 1
                if stats is None:
                    conn.execute(player_stats.insert().values(
                        player=player, most_recent_game_day=game_day, days_played=new_days
                    ))
                else:
                    conn.execute(
                        player_stats.update().where(player_stats.c.player == player)
                        .values(most_recent_game_day=game_day, days_played=new_days)
                    )
                days_played_result = new_days
            else:
                days_played_result = current_days

        return _result({"game_day": game_day, "player": player,
                        "days_played": days_played_result, "is_new_day": is_new_day}, req.id)

    elif req.method == "checkin.days_played":
        player = (req.params or {}).get("player")
        if not isinstance(player, str) or not player.strip():
            return _error(-32602, "params.player must be a non-empty string", req.id)
        with engine.connect() as conn:
            row = conn.execute(
                sa.select(player_stats.c.days_played).where(player_stats.c.player == player.strip())
            ).fetchone()
        return _result({"player": player.strip(), "days_played": row[0] if row else 0}, req.id)

    elif req.method == "checkin.num_players":
        params = req.params or {}
        start_day = params.get("start_game_day")
        num_days = params.get("num_days")
        if not isinstance(start_day, int) or not isinstance(num_days, int) or num_days < 1:
            return _error(-32602, "params.start_game_day and params.num_days must be positive integers", req.id)
        num_days = min(num_days, _FIVE_YEARS_OF_DAYS)
        days = list(range(start_day, start_day + num_days))
        with engine.connect() as conn:
            rows = conn.execute(
                sa.select(daily_stats.c.game_day, daily_stats.c.num_players)
                .where(daily_stats.c.game_day.in_(days))
            ).fetchall()
        day_map = {r[0]: r[1] for r in rows}
        return _result({"players": [day_map.get(d, 0) for d in days]}, req.id)

    elif req.method == "checkin.num_sessions":
        params = req.params or {}
        start_day = params.get("start_game_day")
        num_days = params.get("num_days")
        if not isinstance(start_day, int) or not isinstance(num_days, int) or num_days < 1:
            return _error(-32602, "params.start_game_day and params.num_days must be positive integers", req.id)
        num_days = min(num_days, _FIVE_YEARS_OF_DAYS)
        days = list(range(start_day, start_day + num_days))
        with engine.connect() as conn:
            rows = conn.execute(
                sa.select(daily_stats.c.game_day, daily_stats.c.num_sessions)
                .where(daily_stats.c.game_day.in_(days))
            ).fetchall()
        day_map = {r[0]: r[1] for r in rows}
        return _result({"sessions": [day_map.get(d, 0) for d in days]}, req.id)

    elif req.method == "checkin.total_players":
        with engine.connect() as conn:
            total = conn.execute(sa.select(sa.func.count()).select_from(player_stats)).scalar() or 0
        return _result({"total": total}, req.id)

    elif req.method == "checkin.players":
        params = req.params or {}
        start_index = params.get("start_index", 0)
        count = params.get("count", 20)
        if not isinstance(start_index, int) or not isinstance(count, int) or start_index < 0 or count < 1:
            return _error(-32602, "params.start_index and params.count must be non-negative integers", req.id)
        with engine.connect() as conn:
            total = conn.execute(sa.select(sa.func.count()).select_from(player_stats)).scalar() or 0
            rows = conn.execute(
                sa.select(player_stats.c.player).order_by(player_stats.c.id)
                .offset(start_index).limit(count)
            ).fetchall()
        return _result({"total": total, "players": [r[0] for r in rows]}, req.id)

    else:
        return _error(-32601, f"Method not found: {req.method}", req.id)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Wordlist</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: system-ui, -apple-system, sans-serif;
      background: #f5f5f5;
      color: #111;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      padding: 2rem 1rem;
    }
    .container { width: 100%; max-width: 640px; }
    h1 { font-size: 1.75rem; font-weight: 700; margin-bottom: 2rem; }
    h2 { font-size: 1.25rem; font-weight: 700; margin-bottom: 1rem; color: #333; }
    h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.75rem; }
    section {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.25rem;
    }
    textarea {
      width: 100%;
      min-height: 100px;
      padding: 0.6rem 0.75rem;
      border: 1px solid #d0d0d0;
      border-radius: 6px;
      font-size: 0.9rem;
      font-family: inherit;
      resize: vertical;
      margin-bottom: 0.75rem;
    }
    textarea:focus { outline: none; border-color: #555; }
    input[type=text], input[type=number] {
      width: 100%;
      padding: 0.5rem 0.75rem;
      border: 1px solid #d0d0d0;
      border-radius: 6px;
      font-size: 0.9rem;
      font-family: inherit;
      margin-bottom: 0.75rem;
    }
    input[type=text]:focus, input[type=number]:focus { outline: none; border-color: #555; }
    .warning .badge { background: #fef3c7; color: #92400e; }
    .info .badge { background: #ede9fe; color: #5b21b6; }
    button {
      padding: 0.5rem 1.25rem;
      background: #111;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 0.9rem;
      cursor: pointer;
    }
    button:hover { background: #333; }
    button:disabled { background: #999; cursor: default; }
    .results { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.4rem; }
    .result-row {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      padding: 0.35rem 0.6rem;
      border-radius: 5px;
      background: #f9f9f9;
    }
    .badge {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      white-space: nowrap;
    }
    .found .badge { background: #d1fae5; color: #065f46; }
    .not-found .badge { background: #fee2e2; color: #991b1b; }
    .added .badge { background: #dbeafe; color: #1e40af; }
    .existed .badge { background: #f3f4f6; color: #374151; }
    .set .badge { background: #dbeafe; color: #1e40af; }
    .error-msg { color: #991b1b; font-size: 0.875rem; margin-top: 0.75rem; }
    .hint { font-size: 0.8rem; color: #666; margin-bottom: 0.75rem; }
    .subsection { margin-bottom: 1.5rem; }
    .subsection:last-child { margin-bottom: 0; }
    hr { border: none; border-top: 1px solid #e0e0e0; margin: 1.25rem 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Wordlist</h1>

    <section>
      <h2>Check Words</h2>
      <p class="hint">Enter one word per line.</p>
      <textarea id="check-input" placeholder="apple&#10;banana&#10;cherry"></textarea>
      <button id="check-btn" onclick="checkWords()">Check</button>
      <div id="check-results" class="results"></div>
    </section>

    <section>
      <h2>Add Words</h2>
      <p class="hint">Enter one word per line.</p>
      <textarea id="add-input" placeholder="apple&#10;banana&#10;cherry"></textarea>
      <button id="add-btn" onclick="addWords()">Add</button>
      <div id="add-results" class="results"></div>
    </section>

    <section>
      <h2>Game Day</h2>

      <div class="subsection">
        <h3>Current Game Day</h3>
        <p class="hint">Returns the valid game day range for the current moment across all timezones (GMT-12 to GMT+14).</p>
        <button id="gd-current-btn" onclick="getGameDayCurrent()">Get Current</button>
        <div id="gd-current-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>Check Game Day</h3>
        <p class="hint">Enter a day number to check whether it is currently valid.</p>
        <input id="gd-check-input" type="number" placeholder="42" style="padding:0.5rem 0.75rem;border:1px solid #d0d0d0;border-radius:6px;font-size:0.9rem;margin-bottom:0.75rem;width:100%;">
        <button id="gd-check-btn" onclick="checkGameDay()">Check</button>
        <div id="gd-check-results" class="results"></div>
      </div>
    </section>

    <section>
      <h2>Analyse Board</h2>
      <p class="hint">Enter the 11×11 board as 11 rows of 11 uppercase letters (use space for empty cells). Rows are joined automatically.</p>
      <textarea id="analyse-input" style="font-family:monospace;min-height:154px" placeholder="           &#10;           &#10;           &#10;           &#10;           &#10;     CAT   &#10;     A     &#10;     BOARD &#10;           &#10;           &#10;           "></textarea>
      <button id="analyse-btn" onclick="analyseBoard()">Analyse</button>
      <div id="analyse-results" class="results"></div>
    </section>

    <section>
      <h2>Score</h2>
      <p class="hint">Enter one word per line. Prefix with <code>+</code> if in dictionary, <code>-</code> if not (e.g. <code>+APPLE</code>, <code>-ZORK</code>). Words are uppercased automatically.</p>
      <textarea id="score-input" placeholder="+APPLE&#10;+CAT&#10;-ZORK"></textarea>
      <button id="score-btn" onclick="calculateScore()">Calculate</button>
      <div id="score-results" class="results"></div>
    </section>

    <section>
      <h2>Check-In</h2>

      <div class="subsection">
        <h3>Check In</h3>
        <p class="hint">Records a session. Increments unique-player count once per player per day.</p>
        <input id="ci-day" type="number" placeholder="Game day">
        <input id="ci-player" type="text" placeholder="Player name">
        <button id="ci-btn" onclick="doCheckIn()">Check In</button>
        <div id="ci-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>Player Stats</h3>
        <p class="hint">Returns the total number of days a player has checked in.</p>
        <input id="ci-stats-player" type="text" placeholder="Player name">
        <button id="ci-stats-btn" onclick="getPlayerStats()">Get Stats</button>
        <div id="ci-stats-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>Daily Stats</h3>
        <p class="hint">Returns unique player counts and session counts for a range of game days.</p>
        <input id="ci-daily-start" type="number" placeholder="Start game day">
        <input id="ci-daily-count" type="number" placeholder="Number of days" value="7">
        <button id="ci-daily-btn" onclick="getDailyStats()">Get Stats</button>
        <div id="ci-daily-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>All Players</h3>
        <p class="hint">Returns total unique players and a paginated list in order of first check-in.</p>
        <button id="ci-players-btn" onclick="getAllPlayers()">Get Players</button>
        <div id="ci-players-results" class="results"></div>
      </div>
    </section>

    <section>
      <h2>Game</h2>

      <div class="subsection">
        <h3>Full Board Analysis</h3>
        <p class="hint">Finds words, checks the dictionary, and calculates the score for a board.</p>
        <textarea id="ga-board" style="font-family:monospace;min-height:154px" placeholder="           &#10;           &#10;           &#10;           &#10;           &#10;     CAT   &#10;     A     &#10;     BOARD &#10;           &#10;           &#10;           "></textarea>
        <button id="ga-btn" onclick="gameBoardAnalyse()">Analyse</button>
        <div id="ga-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>Submit Board</h3>
        <p class="hint">Submit a completed board for a game day. The score is calculated server-side and verified against the seed word.</p>
        <input id="gs-day" type="number" placeholder="Game day">
        <input id="gs-player" type="text" placeholder="Player name">
        <textarea id="gs-board" style="font-family:monospace;min-height:154px" placeholder="           &#10;           &#10;           &#10;           &#10;           &#10;     CAT   &#10;     A     &#10;     BOARD &#10;           &#10;           &#10;           "></textarea>
        <button id="gs-btn" onclick="gameSubmitBoard()">Submit</button>
        <div id="gs-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>View Results</h3>
        <p class="hint">View the best score and submissions for a game day.</p>
        <input id="gr-day" type="number" placeholder="Game day">
        <button id="gr-btn" onclick="gameGetResults()">Get Results</button>
        <div id="gr-results" class="results"></div>
      </div>
    </section>

    <section>
      <h2>Seed Words</h2>

      <div class="subsection">
        <h3>Set Seed Words</h3>
        <p class="hint">Enter one <code>day:word</code> pair per line.</p>
        <textarea id="sw-set-input" placeholder="1:apple&#10;2:banana&#10;3:cherry"></textarea>
        <button id="sw-set-btn" onclick="setSeedWords()">Set</button>
        <div id="sw-set-results" class="results"></div>
      </div>

      <hr>

      <div class="subsection">
        <h3>Check Seed Words</h3>
        <p class="hint">Enter one day number per line.</p>
        <textarea id="sw-check-input" placeholder="1&#10;2&#10;3"></textarea>
        <button id="sw-check-btn" onclick="checkSeedWords()">Check</button>
        <div id="sw-check-results" class="results"></div>
      </div>
    </section>
  </div>

  <script>
    async function rpc(method, params) {
      const res = await fetch('/rpc', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({jsonrpc: '2.0', method, params, id: 1}),
      });
      return res.json();
    }

    function parseWords(id) {
      return document.getElementById(id).value
        .split('\\n')
        .map(w => w.trim())
        .filter(w => w.length > 0);
    }

    async function checkWords() {
      const words = parseWords('check-input');
      const out = document.getElementById('check-results');
      if (!words.length) { out.innerHTML = ''; return; }

      const btn = document.getElementById('check-btn');
      btn.disabled = true;
      try {
        const data = await rpc('check', {words});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          out.innerHTML = Object.entries(data.result).map(([word, found]) => `
            <div class="result-row ${found ? 'found' : 'not-found'}">
              <span class="badge">${found ? 'Found' : 'Not found'}</span>
              <span>${escHtml(word)}</span>
            </div>`).join('');
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function addWords() {
      const words = parseWords('add-input');
      const out = document.getElementById('add-results');
      if (!words.length) { out.innerHTML = ''; return; }

      const btn = document.getElementById('add-btn');
      btn.disabled = true;
      try {
        const data = await rpc('add', {words});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {added, already_exists} = data.result;
          const rows = [
            ...added.map(w => `
              <div class="result-row added">
                <span class="badge">Added</span>
                <span>${escHtml(w)}</span>
              </div>`),
            ...already_exists.map(w => `
              <div class="result-row existed">
                <span class="badge">Already exists</span>
                <span>${escHtml(w)}</span>
              </div>`),
          ];
          out.innerHTML = rows.join('');
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function setSeedWords() {
      const lines = parseWords('sw-set-input');
      const out = document.getElementById('sw-set-results');
      if (!lines.length) { out.innerHTML = ''; return; }

      const entries = [];
      for (const line of lines) {
        const colon = line.indexOf(':');
        if (colon === -1) {
          out.innerHTML = `<p class="error-msg">Invalid format: "${escHtml(line)}" — expected day:word</p>`;
          return;
        }
        const day = parseInt(line.slice(0, colon).trim(), 10);
        const word = line.slice(colon + 1).trim();
        if (isNaN(day) || !word) {
          out.innerHTML = `<p class="error-msg">Invalid entry: "${escHtml(line)}" — day must be an integer and word must not be empty</p>`;
          return;
        }
        entries.push({day, word});
      }

      const btn = document.getElementById('sw-set-btn');
      btn.disabled = true;
      try {
        const data = await rpc('seedwords.set', {entries});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          out.innerHTML = entries.map(({day, word}) => `
            <div class="result-row set">
              <span class="badge">Set</span>
              <span>Day ${escHtml(String(day))}: ${escHtml(word)}</span>
            </div>`).join('');
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function checkSeedWords() {
      const lines = parseWords('sw-check-input');
      const out = document.getElementById('sw-check-results');
      if (!lines.length) { out.innerHTML = ''; return; }

      const days = [];
      for (const line of lines) {
        const day = parseInt(line, 10);
        if (isNaN(day)) {
          out.innerHTML = `<p class="error-msg">Invalid day number: "${escHtml(line)}"</p>`;
          return;
        }
        days.push(day);
      }

      const btn = document.getElementById('sw-check-btn');
      btn.disabled = true;
      try {
        const data = await rpc('seedwords.check', {days});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          out.innerHTML = Object.entries(data.result).map(([day, word]) => `
            <div class="result-row ${word !== null ? 'found' : 'not-found'}">
              <span class="badge">${word !== null ? 'Found' : 'Not found'}</span>
              <span>Day ${escHtml(day)}: ${word !== null ? escHtml(word) : '—'}</span>
            </div>`).join('');
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function analyseBoard() {
      const out = document.getElementById('analyse-results');
      const raw = document.getElementById('analyse-input').value;
      // Join rows: split on newlines, pad/trim each to BOARD_SIZE, join flat
      const BOARD_SIZE = 11;
      const rows = raw.split('\\n').map(r => {
        const padded = r + ' '.repeat(BOARD_SIZE);
        return padded.slice(0, BOARD_SIZE);
      });
      while (rows.length < BOARD_SIZE) rows.push(' '.repeat(BOARD_SIZE));
      const board = rows.slice(0, BOARD_SIZE).join('').toUpperCase();

      if (board.length !== BOARD_SIZE * BOARD_SIZE) {
        out.innerHTML = `<p class="error-msg">Board must be ${BOARD_SIZE * BOARD_SIZE} characters.</p>`;
        return;
      }

      const btn = document.getElementById('analyse-btn');
      btn.disabled = true;
      try {
        const data = await rpc('analyse', {board});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const words = data.result.words;
          if (!words.length) {
            out.innerHTML = `<div class="result-row not-found"><span class="badge">Empty</span><span>No words found (centre cell empty)</span></div>`;
          } else {
            out.innerHTML = words.map((w, i) => `
              <div class="result-row found">
                <span class="badge">#${i + 1}</span>
                <span>${escHtml(w)}</span>
              </div>`).join('') + `
              <div class="result-row added" style="margin-top:0.5rem">
                <span class="badge">Total</span>
                <span>${words.length} word${words.length !== 1 ? 's' : ''}</span>
              </div>`;
          }
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function calculateScore() {
      const lines = parseWords('score-input');
      const out = document.getElementById('score-results');
      if (!lines.length) { out.innerHTML = ''; return; }

      const words = [], in_dictionary = [];
      for (const line of lines) {
        const prefix = line[0];
        if (prefix !== '+' && prefix !== '-') {
          out.innerHTML = `<p class="error-msg">Each line must start with + or -: "${escHtml(line)}"</p>`;
          return;
        }
        words.push(line.slice(1).trim().toUpperCase());
        in_dictionary.push(prefix === '+');
      }

      const btn = document.getElementById('score-btn');
      btn.disabled = true;
      try {
        const data = await rpc('score', {words, in_dictionary});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const breakdown = words.map((w, i) => `
            <div class="result-row ${in_dictionary[i] ? 'found' : 'not-found'}">
              <span class="badge">${in_dictionary[i] ? 'Dict' : 'Not dict'}</span>
              <span>${escHtml(w)}</span>
            </div>`).join('');
          out.innerHTML = breakdown + `
            <div class="result-row added" style="margin-top:0.5rem">
              <span class="badge">Score</span>
              <span>${data.result.score}</span>
            </div>`;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function getGameDayCurrent() {
      const out = document.getElementById('gd-current-results');
      const btn = document.getElementById('gd-current-btn');
      btn.disabled = true;
      try {
        const data = await rpc('gameday.current', {});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {min_day, max_day} = data.result;
          out.innerHTML = `
            <div class="result-row found">
              <span class="badge">Min</span>
              <span>Day ${min_day}</span>
            </div>
            <div class="result-row found">
              <span class="badge">Max</span>
              <span>Day ${max_day}</span>
            </div>`;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function checkGameDay() {
      const out = document.getElementById('gd-check-results');
      const val = document.getElementById('gd-check-input').value.trim();
      if (!val) { out.innerHTML = ''; return; }
      const day = parseInt(val, 10);
      if (isNaN(day)) {
        out.innerHTML = `<p class="error-msg">Day must be an integer.</p>`;
        return;
      }
      const btn = document.getElementById('gd-check-btn');
      btn.disabled = true;
      try {
        const data = await rpc('gameday.check', {day});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {valid, requested_day, min_day, max_day} = data.result;
          out.innerHTML = `
            <div class="result-row ${valid ? 'found' : 'not-found'}">
              <span class="badge">${valid ? 'Valid' : 'Invalid'}</span>
              <span>Day ${requested_day} &mdash; valid range: ${min_day} &ndash; ${max_day}</span>
            </div>`;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function doCheckIn() {
      const out = document.getElementById('ci-results');
      const game_day = parseInt(document.getElementById('ci-day').value, 10);
      const player = document.getElementById('ci-player').value.trim();
      if (isNaN(game_day)) { out.innerHTML = `<p class="error-msg">Game day must be an integer.</p>`; return; }
      if (!player) { out.innerHTML = `<p class="error-msg">Player name is required.</p>`; return; }
      const btn = document.getElementById('ci-btn');
      btn.disabled = true;
      try {
        const data = await rpc('checkin.checkin', {game_day, player});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {days_played, is_new_day} = data.result;
          out.innerHTML = `
            <div class="result-row found">
              <span class="badge">Checked in</span>
              <span>${escHtml(player)} — day ${game_day}</span>
            </div>
            <div class="result-row ${is_new_day ? 'added' : 'existed'}">
              <span class="badge">${is_new_day ? 'New day' : 'Repeat session'}</span>
              <span>Days played: ${days_played}</span>
            </div>`;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function getPlayerStats() {
      const out = document.getElementById('ci-stats-results');
      const player = document.getElementById('ci-stats-player').value.trim();
      if (!player) { out.innerHTML = `<p class="error-msg">Player name is required.</p>`; return; }
      const btn = document.getElementById('ci-stats-btn');
      btn.disabled = true;
      try {
        const data = await rpc('checkin.days_played', {player});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {days_played} = data.result;
          out.innerHTML = `
            <div class="result-row ${days_played > 0 ? 'found' : 'not-found'}">
              <span class="badge">Days played</span>
              <span>${escHtml(player)}: ${days_played}</span>
            </div>`;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function getDailyStats() {
      const out = document.getElementById('ci-daily-results');
      const start_game_day = parseInt(document.getElementById('ci-daily-start').value, 10);
      const num_days = parseInt(document.getElementById('ci-daily-count').value, 10);
      if (isNaN(start_game_day) || isNaN(num_days) || num_days < 1) {
        out.innerHTML = `<p class="error-msg">Start day and number of days must be positive integers.</p>`; return;
      }
      const btn = document.getElementById('ci-daily-btn');
      btn.disabled = true;
      try {
        const [pData, sData] = await Promise.all([
          rpc('checkin.num_players', {start_game_day, num_days}),
          rpc('checkin.num_sessions', {start_game_day, num_days}),
        ]);
        if (pData.error || sData.error) {
          out.innerHTML = `<p class="error-msg">Error: ${(pData.error || sData.error).message}</p>`;
        } else {
          const players = pData.result.players;
          const sessions = sData.result.sessions;
          out.innerHTML = players.map((p, i) => `
            <div class="result-row info">
              <span class="badge">Day ${start_game_day + i}</span>
              <span>${p} player${p !== 1 ? 's' : ''}, ${sessions[i]} session${sessions[i] !== 1 ? 's' : ''}</span>
            </div>`).join('');
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function getAllPlayers() {
      const out = document.getElementById('ci-players-results');
      const btn = document.getElementById('ci-players-btn');
      btn.disabled = true;
      try {
        const data = await rpc('checkin.players', {start_index: 0, count: 50});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {total, players} = data.result;
          if (total === 0) {
            out.innerHTML = `<div class="result-row not-found"><span class="badge">Empty</span><span>No players yet</span></div>`;
          } else {
            out.innerHTML = `<div class="result-row info"><span class="badge">Total</span><span>${total} unique player${total !== 1 ? 's' : ''}</span></div>` +
              players.map((p, i) => `
                <div class="result-row existed">
                  <span class="badge">#${i + 1}</span>
                  <span>${escHtml(p)}</span>
                </div>`).join('') +
              (total > players.length ? `<div class="result-row info"><span class="badge">…</span><span>${total - players.length} more</span></div>` : '');
          }
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    function boardToFlat(inputId) {
      const BSIZE = 11;
      const raw = document.getElementById(inputId).value;
      const rows = raw.split('\\n').map(r => (r + ' '.repeat(BSIZE)).slice(0, BSIZE));
      while (rows.length < BSIZE) rows.push(' '.repeat(BSIZE));
      return rows.slice(0, BSIZE).join('').toUpperCase();
    }

    async function gameBoardAnalyse() {
      const out = document.getElementById('ga-results');
      const board = boardToFlat('ga-board');
      if (board.length !== 121) { out.innerHTML = `<p class="error-msg">Board must be 121 characters.</p>`; return; }
      const btn = document.getElementById('ga-btn');
      btn.disabled = true;
      try {
        const data = await rpc('board.analyse', {board});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {score, words, in_dictionary} = data.result;
          if (!words.length) {
            out.innerHTML = `<div class="result-row not-found"><span class="badge">Empty</span><span>No words found (centre cell empty)</span></div>`;
          } else {
            out.innerHTML = words.map((w, i) => `
              <div class="result-row ${in_dictionary[i] ? 'found' : 'not-found'}">
                <span class="badge">${in_dictionary[i] ? 'Dict' : 'Not dict'}</span>
                <span>${escHtml(w)}</span>
              </div>`).join('') + `
              <div class="result-row added" style="margin-top:0.5rem">
                <span class="badge">Score</span><span>${score}</span>
              </div>`;
          }
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function gameSubmitBoard() {
      const out = document.getElementById('gs-results');
      const game_day = parseInt(document.getElementById('gs-day').value, 10);
      const player = document.getElementById('gs-player').value.trim();
      const board = boardToFlat('gs-board');
      if (isNaN(game_day)) { out.innerHTML = `<p class="error-msg">Game day must be an integer.</p>`; return; }
      if (!player) { out.innerHTML = `<p class="error-msg">Player name is required.</p>`; return; }
      if (board.length !== 121) { out.innerHTML = `<p class="error-msg">Board must be 121 characters.</p>`; return; }

      const btn = document.getElementById('gs-btn');
      btn.disabled = true;
      try {
        // Calculate score first so submitted_score matches calculated_score
        const analysed = await rpc('board.analyse', {board});
        if (analysed.error) {
          out.innerHTML = `<p class="error-msg">Analysis error: ${analysed.error.message}</p>`; return;
        }
        const score = analysed.result.score;

        const data = await rpc('board.submit', {game_day, score, board, player});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const r = data.result;
          const statusClass = {submitted:'found', not_competitive:'warning', seed_word_not_found:'not-found',
                               score_mismatch:'warning', score_mismatch_not_competitive:'not-found'}[r.status] || 'info';
          const statusLabel = {submitted:'Submitted', not_competitive:'Not competitive',
                               seed_word_not_found:'Seed word not found', score_mismatch:'Score mismatch',
                               score_mismatch_not_competitive:'Mismatch + not competitive'}[r.status] || r.status;
          let rows = `<div class="result-row ${statusClass}"><span class="badge">${statusLabel}</span>`;
          if (r.calculated_score !== undefined) rows += `<span>Score: ${r.calculated_score}</span>`;
          if (r.best_score !== undefined) rows += `<span style="color:#666">(best: ${r.best_score})</span>`;
          if (r.seed_word) rows += `<span style="color:#666">seed: ${escHtml(r.seed_word)}</span>`;
          rows += `</div>`;
          if (r.words && r.words.length) {
            rows += r.words.map((w, i) => `
              <div class="result-row ${r.in_dictionary[i] ? 'found' : 'not-found'}">
                <span class="badge">${r.in_dictionary[i] ? 'Dict' : 'Not dict'}</span>
                <span>${escHtml(w)}</span>
              </div>`).join('');
          }
          out.innerHTML = rows;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    async function gameGetResults() {
      const out = document.getElementById('gr-results');
      const game_day = parseInt(document.getElementById('gr-day').value, 10);
      if (isNaN(game_day)) { out.innerHTML = `<p class="error-msg">Game day must be an integer.</p>`; return; }
      const btn = document.getElementById('gr-btn');
      btn.disabled = true;
      try {
        const data = await rpc('board.results', {game_day});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          const {num_submissions, best_score, submissions} = data.result;
          if (num_submissions === 0) {
            out.innerHTML = `<div class="result-row not-found"><span class="badge">No submissions</span><span>No boards submitted for day ${game_day}</span></div>`;
          } else {
            out.innerHTML = `
              <div class="result-row info"><span class="badge">Total</span><span>${num_submissions} submission${num_submissions !== 1 ? 's' : ''}</span></div>
              <div class="result-row found"><span class="badge">Best score</span><span>${best_score}</span></div>` +
              submissions.map(s => `
              <div class="result-row existed">
                <span class="badge">${escHtml(s.player)}</span>
                <span style="font-family:monospace;font-size:0.75rem">${escHtml(s.board.trim())}</span>
              </div>`).join('');
          }
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    function escHtml(s) {
      return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
  </script>
</body>
</html>
"""
