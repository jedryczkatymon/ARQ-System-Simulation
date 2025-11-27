"""
Generator bitów i narzędzie do dzielenia na pakiety.

Funkcje:
- random_bitstream(length: int, seed: int|None) -> List[int]
    Zwraca listę losowych bitów (0/1). Używa lokalnej instancji random.Random(seed)
    — seed=None oznacza losowość systemową (różne przebiegi).
- packetize(bits: List[int], payload_size: int) -> List[List[int]]
    Dzieli listę bitów na pakiety o stałym payload_size; ostatni pakiet jest
    dopełniany zerami.

Uwagi:
- Brak walidacji argumentów (np. payload_size>0).
"""

import random
from typing import List
from utils import chunk

def random_bitstream(length: int, seed: int = None) -> List[int]:
    rnd = random.Random(seed)
    return [rnd.getrandbits(1) for _ in range(length)]

def packetize(bits: List[int], payload_size: int) -> List[List[int]]:
    packets = []
    for p in chunk(bits, payload_size):
        if len(p) < payload_size:
            p = p + [0] * (payload_size - len(p))
        packets.append(p)
    return packets
