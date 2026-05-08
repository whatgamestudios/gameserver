# Wordlist Server

A FastAPI backend deployable to Vercel. Maintains a database of words and exposes a JSON RPC API to check and add words, plus a web UI for manual lookups.

## Structure

```
server/
├── api/
│   └── index.py       # FastAPI app — database, JSON RPC, web UI
├── requirements.txt   # Python dependencies
├── vercel.json        # Routes all requests to the FastAPI app
└── README.md
```

## Running locally

It is recommended to run the app inside a Python virtual environment to keep dependencies isolated from your system Python.

**1. Create and activate the virtual environment:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your shell prompt will change to show `(.venv)` when the environment is active.

**2. Install dependencies:**

```bash
pip install -r requirements.txt
pip install uvicorn
```

**3. Configure the database:**

Copy `.env.example` to `.env` and fill in your Neon password:

```bash
cp .env.example .env
```

Edit `.env`:

```
DATABASE_URL=postgresql://neondb_owner:<password>@ep-round-frost-ajban92u.c-3.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**4. Start the server:**

```bash
uvicorn api.index:app --reload
```

The app will be available at `http://localhost:8000`.


**5. Stop the server:**

```bash
pkill -f uvicorn
```

**6. Deactivate the virtual environment when done:**

```bash
deactivate
```

> The `.venv/` directory is listed in `.gitignore` and will not be committed.

## Database

Uses [Neon](https://neon.tech) (PostgreSQL). The connection string is read from the `DATABASE_URL` environment variable.

- **Locally:** set `DATABASE_URL` in `.env` — `python-dotenv` loads it automatically on startup.
- **Vercel:** set `DATABASE_URL` in the project's environment variables in the Vercel dashboard.

> `.env` is listed in `.gitignore` and will never be committed.

## JSON RPC API

All requests are `POST /rpc` with a JSON-RPC 2.0 body.

### `check` — check if words are in the wordlist

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "check",
  "params": { "words": ["apple", "fig", "banana"] },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": { "apple": true, "fig": false, "banana": true },
  "id": 1
}
```

### `add` — add one or more words to the wordlist

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "add",
  "params": { "words": ["fig", "apple"] },
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": { "added": ["fig"], "already_exists": ["apple"] },
  "id": 2
}
```

Words are stored case-sensitively. Duplicate words are silently ignored — the response indicates which words were new vs. already present.

## Web UI

A browser interface is served at `/`. Enter words one per line to check whether they appear in the wordlist or to add new ones.

## Deploying to Vercel

1. Push this repository to GitHub.
2. Import the project in the [Vercel dashboard](https://vercel.com/new).
3. Add a `DATABASE_URL` environment variable pointing to your hosted database.
4. Deploy — Vercel detects the Python runtime from `api/index.py` automatically.
