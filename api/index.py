from typing import Any, Dict, Optional, Union

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from db import engine, wordlist, seedwords, submissions, player_stats, daily_stats, _14_player_stats, _14_daily_stats
from board import (
    BOARD_SIZE,
    _GAME_START,
    _14_GAME_START,
    _analyse_board,
    _calculate_score,
    _check_words_in_db,
    _current_game_days,
    _is_seed_word_on_board,
)
from numbers14 import get_target_value
from templates import INDEX_HTML, WORCADIAN_HTML, NUMBERS14_HTML

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
    return INDEX_HTML


@app.get("/worcadian", response_class=HTMLResponse)
def worcadian():
    return WORCADIAN_HTML


@app.get("/14numbers", response_class=HTMLResponse)
def numbers14():
    return NUMBERS14_HTML


@app.post("/rpc")
def rpc(req: RpcRequest):
    try:
        return _rpc(req)
    except Exception as exc:
        return _error(-32603, f"Internal error: {exc}", req.id)


@app.post("/14rpc")
def rpc_14(req: RpcRequest):
    try:
        return _rpc_14_handler(req)
    except Exception as exc:
        return _error(-32603, f"Internal error: {exc}", req.id)


def _rpc_14_handler(req: RpcRequest):
    if req.jsonrpc != "2.0":
        return _error(-32600, "Invalid Request", req.id)

    if req.method == "gameday.current":
        min_day, max_day = _current_game_days(_14_GAME_START)
        return _result({"min_day": min_day, "max_day": max_day}, req.id)

    elif req.method == "gameday.check":
        day = (req.params or {}).get("day")
        if not isinstance(day, int):
            return _error(-32602, "params.day must be an integer", req.id)
        min_day, max_day = _current_game_days(_14_GAME_START)
        valid = min_day <= day <= max_day
        return _result({"valid": valid, "requested_day": day, "min_day": min_day, "max_day": max_day}, req.id)

    elif req.method == "target.get":
        game_day = (req.params or {}).get("game_day")
        if not isinstance(game_day, int):
            return _error(-32602, "params.game_day must be an integer", req.id)
        return _result({"target": get_target_value(game_day)}, req.id)

    elif req.method.startswith("checkin."):
        return _checkin_rpc(req, _14_player_stats, _14_daily_stats, _14_GAME_START)

    else:
        return _error(-32601, f"Method not found: {req.method}", req.id)


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
        min_day, max_day = _current_game_days(_GAME_START)
        return _result({"min_day": min_day, "max_day": max_day}, req.id)

    elif req.method == "gameday.check":
        day = (req.params or {}).get("day")
        if not isinstance(day, int):
            return _error(-32602, "params.day must be an integer", req.id)
        min_day, max_day = _current_game_days(_GAME_START)
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
        min_day, max_day = _current_game_days(_GAME_START)
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

    elif req.method == "board.import":
        params = req.params or {}
        game_day = params.get("game_day")
        board = params.get("board")
        player = params.get("player")
        if not isinstance(game_day, int):
            return _error(-32602, "params.game_day must be an integer", req.id)
        if not isinstance(board, str):
            return _error(-32602, "params.board must be a string", req.id)
        if not isinstance(player, str) or not player.strip():
            return _error(-32602, "params.player must be a non-empty string", req.id)
        if len(board) != BOARD_SIZE * BOARD_SIZE:
            return _error(-32602, f"params.board must be exactly {BOARD_SIZE * BOARD_SIZE} characters", req.id)
        player = player.strip()

        # Skip duplicate (same day + player + board already stored)
        with engine.connect() as conn:
            already = conn.execute(
                sa.select(sa.func.count()).select_from(submissions)
                .where(submissions.c.game_day == game_day)
                .where(submissions.c.player == player)
                .where(submissions.c.board == board)
            ).scalar() or 0
        if already:
            return _result({"status": "duplicate", "game_day": game_day, "player": player}, req.id)

        words = _analyse_board(board)
        in_dictionary = _check_words_in_db(words)
        calculated_score = _calculate_score(words, in_dictionary)

        with engine.begin() as conn:
            conn.execute(submissions.insert().values(
                game_day=game_day, score=calculated_score,
                player=player, board=board,
            ))

        return _result({"status": "imported", "game_day": game_day, "player": player,
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

    elif req.method.startswith("checkin."):
        return _checkin_rpc(req, player_stats, daily_stats, _GAME_START)

    else:
        return _error(-32601, f"Method not found: {req.method}", req.id)


def _checkin_rpc(req: RpcRequest, p_stats: Any, d_stats: Any, game_start: int):
    if req.method == "checkin.checkin":
        params = req.params or {}
        game_day = params.get("game_day")
        player = params.get("player")
        if not isinstance(game_day, int):
            return _error(-32602, "params.game_day must be an integer", req.id)
        if not isinstance(player, str) or not player.strip():
            return _error(-32602, "params.player must be a non-empty string", req.id)
        player = player.strip()

        min_day, max_day = _current_game_days(game_start)
        if not (min_day <= game_day <= max_day):
            return _error(-32602, f"game_day {game_day} is not valid (valid range: {min_day}–{max_day})", req.id)

        with engine.begin() as conn:
            # Ensure daily_stats row exists, then atomically increment sessions
            if not conn.execute(
                sa.select(sa.func.count()).select_from(d_stats)
                .where(d_stats.c.game_day == game_day)
            ).scalar():
                conn.execute(d_stats.insert().values(game_day=game_day, num_players=0, num_sessions=0))
            conn.execute(
                d_stats.update().where(d_stats.c.game_day == game_day)
                .values(num_sessions=d_stats.c.num_sessions + 1)
            )

            stats = conn.execute(
                sa.select(p_stats).where(p_stats.c.player == player)
            ).fetchone()

            current_days = stats[3] if stats else 0        # days_played
            current_recent = stats[2] if stats else 0      # most_recent_game_day
            is_new_day = (current_days == 0 or game_day > current_recent)

            if is_new_day:
                conn.execute(
                    d_stats.update().where(d_stats.c.game_day == game_day)
                    .values(num_players=d_stats.c.num_players + 1)
                )
                new_days = current_days + 1
                if stats is None:
                    conn.execute(p_stats.insert().values(
                        player=player, most_recent_game_day=game_day, days_played=new_days
                    ))
                else:
                    conn.execute(
                        p_stats.update().where(p_stats.c.player == player)
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
                sa.select(p_stats.c.days_played).where(p_stats.c.player == player.strip())
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
                sa.select(d_stats.c.game_day, d_stats.c.num_players)
                .where(d_stats.c.game_day.in_(days))
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
                sa.select(d_stats.c.game_day, d_stats.c.num_sessions)
                .where(d_stats.c.game_day.in_(days))
            ).fetchall()
        day_map = {r[0]: r[1] for r in rows}
        return _result({"sessions": [day_map.get(d, 0) for d in days]}, req.id)

    elif req.method == "checkin.total_players":
        with engine.connect() as conn:
            total = conn.execute(sa.select(sa.func.count()).select_from(p_stats)).scalar() or 0
        return _result({"total": total}, req.id)

    elif req.method == "checkin.players":
        params = req.params or {}
        start_index = params.get("start_index", 0)
        count = params.get("count", 20)
        if not isinstance(start_index, int) or not isinstance(count, int) or start_index < 0 or count < 1:
            return _error(-32602, "params.start_index and params.count must be non-negative integers", req.id)
        with engine.connect() as conn:
            total = conn.execute(sa.select(sa.func.count()).select_from(p_stats)).scalar() or 0
            rows = conn.execute(
                sa.select(p_stats.c.player).order_by(p_stats.c.id)
                .offset(start_index).limit(count)
            ).fetchall()
        return _result({"total": total, "players": [r[0] for r in rows]}, req.id)

    else:
        return _error(-32601, f"Method not found: {req.method}", req.id)
