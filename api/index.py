import os
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

metadata = sa.MetaData()
wordlist = sa.Table(
    "wordlist",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("word", sa.String, unique=True, nullable=False),
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
    h2 { font-size: 1.1rem; font-weight: 600; margin-bottom: 0.75rem; }
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
    .error-msg { color: #991b1b; font-size: 0.875rem; margin-top: 0.75rem; }
    .hint { font-size: 0.8rem; color: #666; margin-bottom: 0.75rem; }
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

    function escHtml(s) {
      return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
  </script>
</body>
</html>
"""
