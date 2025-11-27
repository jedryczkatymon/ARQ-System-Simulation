"""
Narzędzia bitowe — konwersje i dzielenie na bloki.

Funkcje:
- bits_to_bytes(bits: Iterable[int]) -> bytes
    Konwertuje sekwencję bitów (0/1) do bytes (MSB pierwszy w bajcie).
    Nie usuwa informacji o długości — brak metadata o dopełnieniu.
- bytes_to_bits(data: bytes) -> List[int]
    Rozbija bajty na listę bitów (MSB->LSB).
- chunk(lst: List, n: int)
    Generator zwracający podlisty o maks. długości n.

Uwagi:
- Wejścia zakładają wartości 0/1; brak rygorystycznej walidacji.
- bits_to_bytes dopełnia ostatni bajt zerami (big-endian w obrębie bajtu).
"""

from typing import List, Iterable

def bits_to_bytes(bits: Iterable[int]) -> bytes:
    b = 0
    out = bytearray()
    bits = list(bits)
    for i, bit in enumerate(bits):
        b = (b << 1) | (bit & 1)
        if (i + 1) % 8 == 0:
            out.append(b)
            b = 0
    rem = len(bits) % 8
    if rem != 0:
        b = b << (8 - rem)
        out.append(b)
    return bytes(out)

def bytes_to_bits(data: bytes) -> List[int]:
    out = []
    for byte in data:
        for i in range(7, -1, -1):
            out.append((byte >> i) & 1)
    return out

def chunk(lst: List, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]
