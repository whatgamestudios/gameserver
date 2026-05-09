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

# GMT Monday March 30, 2026 00:00:00 UTC — mirrors Solidity UNIX_TIME_GAME_START
_GAME_START = 1774828800
_SECONDS_PER_DAY = 86400
_PLUS_FOURTEEN = 50400   # GMT+14: Kiribati Line Islands
_MINUS_TWELVE = 43200    # GMT-12: Baker and Howard Island


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
metadata.create_all(engine)

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

    function escHtml(s) {
      return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
  </script>
</body>
</html>
"""
