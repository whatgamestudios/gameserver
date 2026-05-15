import hashlib
import struct

MIN_TARGET_VALUE = 250
MAX_TARGET_VALUE = 1000


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
