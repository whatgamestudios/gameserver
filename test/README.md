# Tests

Shell scripts that exercise the JSON RPC API using `curl`. Each script targets one RPC method.

## Prerequisites

The server must be running. To start it locally:

```bash
uvicorn api.index:app --reload
```

## Scripts

| Script | Method | What it does |
|--------|--------|--------------|
| `add.sh` | `add` | Adds `apple`, `banana`, and `cherry` to the wordlist |
| `check.sh` | `check` | Checks whether `apple`, `fig`, and `banana` are in the wordlist |

## Running

From the `server/` directory:

```bash
./test/add.sh
./test/check.sh
```

By default the scripts target `http://localhost:8000`. To run against a deployed instance, set `BASE_URL`:

```bash
BASE_URL=https://your-app.vercel.app ./test/add.sh
BASE_URL=https://your-app.vercel.app ./test/check.sh
```

## Expected output

Run `add.sh` first, then `check.sh` to see both `true` and `false` results.

**add.sh**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "added": ["apple", "banana", "cherry"],
        "already_exists": []
    },
    "id": 1
}
```

**check.sh** (after running add.sh)
```json
{
    "jsonrpc": "2.0",
    "result": {
        "apple": true,
        "fig": false,
        "banana": true
    },
    "id": 1
}
```
