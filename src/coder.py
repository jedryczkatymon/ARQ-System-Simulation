import binascii
from typing import List, Tuple
from utils import bits_to_bytes, bytes_to_bits

"""
Mechanizmy kodowania i wykrywania błędów używane w symulacji ARQ.

Implementowane funkcje (przykładowo):
- parity_encode / parity_check : prosty bit parzystości (even).
- hamming74_encode_bits / hamming74_check_and_extract / hamming74_check_bits :
  Hamming(7,4) — kodowanie nibble (4 bity) -> 7 bitów, korekcja pojedynczych błędów.
- crc8_append / crc8_check : prosty CRC-8 (poly 0x07, default).
- crc16_append / crc16_check : CRC-16/CCITT (poly 0x1021, init 0xFFFF).
- crc32_append / crc32_check : CRC-32 (binascii.crc32).
- checksum16_append / checksum16_check : Internet-style 16-bit one's complement checksum.

Uwagi:
- Operacje CRC/checksum są bajtowe: używane są konwersje bits_to_bytes/bytes_to_bits.
- Wejścia zakładają wartości 0/1; brak ścisłej walidacji długości czy zakresów.
"""

def parity_encode(data_bits: List[int]) -> List[int]:
    p = sum(data_bits) % 2
    return data_bits + [p]

def parity_check(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    data, p = rx_bits[:-1], rx_bits[-1]
    ok = (sum(data) + p) % 2 == 0
    return ok, data

def hamming74_encode(nibble: List[int]) -> List[int]:
    d = nibble + [0,0,0]
    d1,d2,d3,d4 = nibble

    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]

def hamming74_encode_bits(data_bits: List[int]) -> List[int]:
    out = []
    from utils import chunk
    for nibble in chunk(data_bits, 4):
        if len(nibble) < 4:
            nibble = nibble + [0]*(4-len(nibble))
        out.extend(hamming74_encode(nibble))
    return out

def hamming74_check_and_extract(rx7: List[int]) -> Tuple[bool, List[int]]:
    p1,p2,d1,p3,d2,d3,d4 = rx7
    s1 = p1 ^ d1 ^ d2 ^ d4
    s2 = p2 ^ d1 ^ d3 ^ d4
    s3 = p3 ^ d2 ^ d3 ^ d4
    syndrome = (s3<<2) | (s2<<1) | s1
    corrected = rx7.copy()
    if syndrome != 0 and 1 <= syndrome <= 7:
        corrected[syndrome-1] ^= 1

    p1c,p2c,d1c,p3c,d2c,d3c,d4c = corrected
    ok = ( (p1c ^ d1c ^ d2c ^ d4c) == 0 and
           (p2c ^ d1c ^ d3c ^ d4c) == 0 and
           (p3c ^ d2c ^ d3c ^ d4c) == 0 )
    data = [d1c,d2c,d3c,d4c]
    return ok, data

def crc32_append(data_bits: List[int]) -> List[int]:
    data_bytes = bits_to_bytes(data_bits)
    crc = binascii.crc32(data_bytes) & 0xffffffff
    crc_bytes = crc.to_bytes(4, 'big')
    return data_bits + bytes_to_bits(crc_bytes)

def crc32_check(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    if len(rx_bits) < 32:
        return False, []
    data_bits = rx_bits[:-32]
    crc_bits = rx_bits[-32:]
    data_bytes = bits_to_bytes(data_bits)
    crc_expected = int.from_bytes(bits_to_bytes(crc_bits), 'big')
    crc_calc = binascii.crc32(data_bytes) & 0xffffffff
    return crc_calc == crc_expected, data_bits

def _crc8_bytes(data: bytes, poly: int = 0x07, init: int = 0x00) -> int:
    crc = init
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) & 0xFF) ^ (poly if (crc & 0x80) else 0)
    return crc & 0xFF

def crc8_append(data_bits: List[int]) -> List[int]:
    data_bytes = bits_to_bytes(data_bits)
    crc = _crc8_bytes(data_bytes)
    crc_b = crc.to_bytes(1, 'big')
    return data_bits + bytes_to_bits(crc_b)

def crc8_check(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    if len(rx_bits) < 8:
        return False, []
    data_bits = rx_bits[:-8]
    crc_bits = rx_bits[-8:]
    data_bytes = bits_to_bytes(data_bits)
    crc_expected = int.from_bytes(bits_to_bytes(crc_bits), 'big')
    crc_calc = _crc8_bytes(data_bytes)
    return crc_calc == crc_expected, data_bits

def _crc16_ccitt_bytes(data: bytes, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    crc = init & 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFFFF if (crc & 0x8000) else ((crc << 1) & 0xFFFF)
    return crc & 0xFFFF

def crc16_append(data_bits: List[int]) -> List[int]:
    data_bytes = bits_to_bytes(data_bits)
    crc = _crc16_ccitt_bytes(data_bytes)
    crc_b = crc.to_bytes(2, 'big')
    return data_bits + bytes_to_bits(crc_b)

def crc16_check(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    if len(rx_bits) < 16:
        return False, []
    data_bits = rx_bits[:-16]
    crc_bits = rx_bits[-16:]
    data_bytes = bits_to_bytes(data_bits)
    crc_expected = int.from_bytes(bits_to_bytes(crc_bits), 'big')
    crc_calc = _crc16_ccitt_bytes(data_bytes)
    return crc_calc == crc_expected, data_bits

def _internet_checksum_bytes(data: bytes) -> int:
    s = 0
    it = iter(data)
    for hi in it:
        try:
            lo = next(it)
        except StopIteration:
            lo = 0
        word = (hi << 8) | lo
        s += word
        s = (s & 0xffff) + (s >> 16)
    s = (s & 0xffff) + (s >> 16)
    return (~s) & 0xffff

def checksum16_append(data_bits: List[int]) -> List[int]:
    data_bytes = bits_to_bytes(data_bits)
    chksum = _internet_checksum_bytes(data_bytes)
    chk_b = chksum.to_bytes(2, 'big')
    return data_bits + bytes_to_bits(chk_b)

def checksum16_check(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    if len(rx_bits) < 16:
        return False, []
    data_bits = rx_bits[:-16]
    chksum_bits = rx_bits[-16:]
    data_bytes = bits_to_bytes(data_bits)
    chk_expected = int.from_bytes(bits_to_bytes(chksum_bits), 'big')
    chk_calc = _internet_checksum_bytes(data_bytes)
    return chk_calc == chk_expected, data_bits

# --- pomoc: dekodowanie całego bloku Hamming(7,4) ---
def hamming74_check_bits(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    """
    Sprawdza sekwencję bitów zakodowaną Hamming(7,4) (7-bitowe słowa).
    Zwraca (ok, data_bits) gdzie ok==True gdy wszystkie słowa przeszły walidację
    po ewentualnej korekcji (syndromy zerowe), data_bits to wyodrębnione nibile.
    """
    if len(rx_bits) % 7 != 0:
        # niepełne słowo -> traktujemy jako błąd
        return False, []
    data_out = []
    all_ok = True
    from utils import chunk
    for word in chunk(rx_bits, 7):
        ok, nib = hamming74_check_and_extract(word)
        if not ok:
            all_ok = False
        data_out.extend(nib)
    return all_ok, data_out
