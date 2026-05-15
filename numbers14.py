import hashlib
import struct

MIN_TARGET_VALUE = 250
MAX_TARGET_VALUE = 1000

_T_PLUS = 200
_T_MINUS = 201
_T_MULTIPLY = 202
_T_DIVIDE = 203
_T_LEFT = 204
_T_RIGHT = 205
_MAX_NUMS = 5
_MAX_BRACKETS = 5


class CalcError(Exception):
    pass


def _is_valid_num(n: int) -> bool:
    return n != 0 and (n <= 10 or n in (25, 50, 75, 100))


def _scan_right(tokens: list, s: int, e: int) -> int:
    lrc = 0
    for i in range(s, e + 1):
        if tokens[i] == _T_LEFT:
            lrc += 1
        if tokens[i] == _T_RIGHT:
            if lrc == 0:
                return i
            lrc -= 1
    raise CalcError("Mismatched brackets")


def _apply_op(l: int, r: int, op: int) -> int:
    if op == _T_PLUS:
        return l + r
    if op == _T_MINUS:
        if l < r:
            raise CalcError("Intermediate result cannot be negative")
        return l - r
    if op == _T_MULTIPLY:
        return l * r
    if r == 0:
        raise CalcError("Division by zero")
    q, rem = divmod(l, r)
    if rem != 0:
        raise CalcError("Division must produce a whole number")
    return q


def _get_val(tokens: list, s: int, e: int) -> tuple:
    if tokens[s] == _T_LEFT:
        ri = _scan_right(tokens, s + 1, e)
        return _process(tokens, s + 1, ri - 1), ri + 1
    return tokens[s], s + 1


def _process(tokens: list, s: int, e: int) -> int:
    res, ns = _get_val(tokens, s, e)
    while ns < e:
        op = tokens[ns]
        rv, ns = _get_val(tokens, ns + 1, e)
        if op == _T_PLUS or op == _T_MINUS:
            while ns < e:
                nop = tokens[ns]
                if nop == _T_PLUS or nop == _T_MINUS:
                    break
                nrv, ns = _get_val(tokens, ns + 1, e)
                rv = _apply_op(rv, nrv, nop)
        res = _apply_op(res, rv, op)
    return res


def calc(input_str: str) -> tuple[int, set]:
    """Parse and evaluate a 14 Numbers expression.
    Returns (result, numbers_used_set). Raises CalcError on invalid input.
    """
    input_str = input_str.strip()
    if not input_str:
        raise CalcError("Please enter an expression")

    tokens: list = []
    num_count = lbc = rbc = 0
    in_num = False
    cur = 0
    used: set = set()

    def finalize():
        nonlocal cur, in_num, num_count
        if not _is_valid_num(cur):
            raise CalcError(f"Invalid number {cur} — use 1–10, 25, 50, 75, or 100")
        tokens.append(cur)
        num_count += 1
        if num_count > _MAX_NUMS:
            raise CalcError("Too many numbers (max 5)")
        if cur in used:
            raise CalcError(f"Number {cur} used more than once")
        used.add(cur)
        cur = 0
        in_num = False

    for i, c in enumerate(input_str):
        if c.isdigit():
            if c == '0' and not in_num:
                raise CalcError("Numbers cannot have leading zeros")
            cur = cur * 10 + int(c)
            in_num = True
        elif c in '+-*/':
            if i == 0:
                raise CalcError("Expression cannot start with an operator")
            if not in_num and (not tokens or tokens[-1] != _T_RIGHT):
                raise CalcError("Operator must follow a number or )")
            if in_num:
                finalize()
            tokens.append(
                _T_PLUS if c == '+' else
                _T_MINUS if c == '-' else
                _T_MULTIPLY if c == '*' else
                _T_DIVIDE
            )
        elif c == '(':
            if lbc >= _MAX_BRACKETS:
                raise CalcError("Too many brackets (max 5)")
            if in_num:
                raise CalcError("( cannot directly follow a number")
            tokens.append(_T_LEFT)
            lbc += 1
        elif c == ')':
            if i == 0:
                raise CalcError("Expression cannot start with )")
            if lbc <= rbc:
                raise CalcError("Closing ) before opening (")
            if not in_num and (not tokens or tokens[-1] != _T_RIGHT):
                raise CalcError(") must follow a number or )")
            if in_num:
                finalize()
            tokens.append(_T_RIGHT)
            rbc += 1
        else:
            raise CalcError(f"Unknown character: {c!r}")

    if lbc != rbc:
        raise CalcError("Mismatched brackets")
    if not in_num and tokens and tokens[-1] != _T_RIGHT:
        raise CalcError("Expression ends unexpectedly")
    if in_num:
        finalize()

    return _process(tokens, 0, len(tokens)), used


def calc_points_single(target: int, res: int) -> int:
    if target == res:
        return 70
    diff = abs(target - res)
    return 0 if diff > 50 else 50 - diff


def calc_points(target: int, res1: int, res2: int, res3: int) -> int:
    return calc_points_single(target, res1) + calc_points_single(target, res2) + calc_points_single(target, res3)


def _generate_seed(game_day: int, game: int, iteration: int) -> bytes:
    """Mirror of Solidity generateSeed(): sha256(abi.encodePacked(uint32, uint32, uint32))."""
    packed = struct.pack(">III", game_day, game, iteration)
    return hashlib.sha256(packed).digest()


def _get_next_value(seed: bytes, count: int, mod: int) -> int:
    """Mirror of Solidity getNextValue(): sha256(seed ++ uint32 count), last 4 bytes mod _mod."""
    raw = hashlib.sha256(seed + struct.pack(">I", count)).digest()
    return struct.unpack(">I", raw[-4:])[0] % mod


def get_target_value(game_day: int) -> int:
    """Return the target number for the given 14 Numbers game day (250–999)."""
    seed = _generate_seed(game_day, 0, 0)
    count = 0
    while True:
        val = _get_next_value(seed, count, MAX_TARGET_VALUE)
        count += 1
        if val >= MIN_TARGET_VALUE:
            return val
