import time

import sqlalchemy as sa

from db import engine, wordlist

BOARD_SIZE = 11


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


# GMT Monday March 30, 2026 00:00:00 UTC — Worcadian UNIX_TIME_GAME_START
_GAME_START = 1774828800
# December 1, 2024 00:00:00 UTC — 14 Numbers UNIX_TIME_GAME_START
_14_GAME_START = 1733011200
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


def _current_game_days(game_start: int) -> tuple[int, int]:
    """Return (min_day, max_day) for the current moment, matching determineCurrentGameDays()."""
    now = int(time.time())
    max_day = (now + _PLUS_FOURTEEN - game_start) // _SECONDS_PER_DAY
    min_day = (now - _MINUS_TWELVE - game_start) // _SECONDS_PER_DAY
    return min_day, max_day
