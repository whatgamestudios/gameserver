INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Whatgame Studios</title>
</head>
<body>
  <h1>Whatgame Studios</h1>
  <ul>
    <li><a href="/worcadian">Worcadian</a></li>
    <li><a href="/14numbers">14 Numbers</a></li>
  </ul>
</body>
</html>"""

WORCADIAN_HTML = """<!DOCTYPE html>
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
      <p class="hint">Enter the 11&#215;11 board as 11 rows of 11 uppercase letters (use space for empty cells). Rows are joined automatically.</p>
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
              <span>Day ${escHtml(day)}: ${word !== null ? escHtml(word) : '&#8212;'}</span>
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
              <span>${escHtml(player)} &#8212; day ${game_day}</span>
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
              (total > players.length ? `<div class="result-row info"><span class="badge">&#8230;</span><span>${total - players.length} more</span></div>` : '');
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
</html>"""

NUMBERS14_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>14 Numbers</title>
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
    .error-msg { color: #991b1b; font-size: 0.875rem; margin-top: 0.75rem; }
    .hint { font-size: 0.8rem; color: #666; margin-bottom: 0.75rem; }
    .subsection { margin-bottom: 1.5rem; }
    .subsection:last-child { margin-bottom: 0; }
    hr { border: none; border-top: 1px solid #e0e0e0; margin: 1.25rem 0; }
  </style>
</head>
<body>
  <div class="container">
    <h1>14 Numbers</h1>

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
      <h2>Target Number</h2>
      <p class="hint">Returns the target number for a specific game day (range: 250–999).</p>
      <input id="tn-day" type="number" placeholder="Game day">
      <button id="tn-btn" onclick="getTargetNumber()">Get Target</button>
      <div id="tn-results" class="results"></div>
    </section>

    <section>
      <h2>Points</h2>
      <p class="hint">Exact match = 70 pts. Within 50 of target = (50 &minus; difference) pts. Beyond 50 = 0 pts.</p>
      <input id="pts-target" type="number" placeholder="Target number">
      <input id="pts-r1" type="number" placeholder="Result 1">
      <input id="pts-r2" type="number" placeholder="Result 2">
      <input id="pts-r3" type="number" placeholder="Result 3">
      <button id="pts-btn" onclick="calculatePoints()">Calculate</button>
      <div id="pts-results" class="results"></div>
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
  </div>

  <script>
    async function rpc(method, params) {
      const res = await fetch('/14rpc', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({jsonrpc: '2.0', method, params, id: 1}),
      });
      return res.json();
    }

    async function getTargetNumber() {
      const out = document.getElementById('tn-results');
      const game_day = parseInt(document.getElementById('tn-day').value, 10);
      if (isNaN(game_day)) { out.innerHTML = `<p class="error-msg">Game day must be an integer.</p>`; return; }
      const btn = document.getElementById('tn-btn');
      btn.disabled = true;
      try {
        const data = await rpc('target.get', {game_day});
        if (data.error) {
          out.innerHTML = `<p class="error-msg">Error: ${data.error.message}</p>`;
        } else {
          out.innerHTML = `
            <div class="result-row found">
              <span class="badge">Target</span>
              <span>Day ${game_day}: ${data.result.target}</span>
            </div>`;
        }
      } catch (e) {
        out.innerHTML = `<p class="error-msg">Request failed.</p>`;
      } finally {
        btn.disabled = false;
      }
    }

    function calcPointsSingle(target, res) {
      if (target === res) return 70;
      const diff = Math.abs(target - res);
      if (diff > 50) return 0;
      return 50 - diff;
    }

    function calculatePoints() {
      const out = document.getElementById('pts-results');
      const target = parseInt(document.getElementById('pts-target').value, 10);
      const r1 = parseInt(document.getElementById('pts-r1').value, 10);
      const r2 = parseInt(document.getElementById('pts-r2').value, 10);
      const r3 = parseInt(document.getElementById('pts-r3').value, 10);
      if ([target, r1, r2, r3].some(isNaN)) {
        out.innerHTML = `<p class="error-msg">All fields must be integers.</p>`;
        return;
      }
      const p1 = calcPointsSingle(target, r1);
      const p2 = calcPointsSingle(target, r2);
      const p3 = calcPointsSingle(target, r3);
      const total = p1 + p2 + p3;
      out.innerHTML = `
        <div class="result-row ${p1 > 0 ? 'found' : 'not-found'}">
          <span class="badge">Result 1</span>
          <span>${r1} &rarr; ${p1} pt${p1 !== 1 ? 's' : ''}</span>
        </div>
        <div class="result-row ${p2 > 0 ? 'found' : 'not-found'}">
          <span class="badge">Result 2</span>
          <span>${r2} &rarr; ${p2} pt${p2 !== 1 ? 's' : ''}</span>
        </div>
        <div class="result-row ${p3 > 0 ? 'found' : 'not-found'}">
          <span class="badge">Result 3</span>
          <span>${r3} &rarr; ${p3} pt${p3 !== 1 ? 's' : ''}</span>
        </div>
        <div class="result-row added">
          <span class="badge">Total</span>
          <span>${total} pt${total !== 1 ? 's' : ''}</span>
        </div>`;
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
              <span>${escHtml(player)} &#8212; day ${game_day}</span>
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
              (total > players.length ? `<div class="result-row info"><span class="badge">&#8230;</span><span>${total - players.length} more</span></div>` : '');
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
</html>"""
