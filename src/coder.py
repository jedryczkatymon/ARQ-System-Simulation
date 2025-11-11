import binascii
from typing import List, Tuple
from utils import bits_to_bytes, bytes_to_bits

"""
Moduł funkcji kodujących i sprawdzających integralność/naprawę błędów
używanych w symulacji ARQ.

Opis ogólny:
  Zestaw prostych mechanizmów korekcji i wykrywania błędów używanych do
  symulacji kanałów i protokołów ARQ:
    - parity_encode / parity_check: parzystość (even parity) dla sekwencji bitów;
    - hamming74_encode / hamming74_encode_bits / hamming74_check_and_extract:
      kod Hamming(7,4) dla 4-bitowych nibble, możliwość kodowania ciągłego strumienia
      bitów i funkcja sprawdzania + korekcji pojedynczych błędów oraz ekstrakcji danych;
    - crc32_append / crc32_check: dołączanie i sprawdzanie CRC-32 (orientacja
      bajtowa) wykorzystujące binascii.crc32.

Funkcje i ich zachowanie:

  parity_encode(data_bits: List[int]) -> List[int]
    Opis:
      Generuje bit parzystości (even) i dołącza go na końcu wejściowej listy bitów.
    Parametry:
      data_bits: lista bitów (0/1) reprezentujących dane.
    Zwraca:
      Nową listę bitów zawierającą oryginalne bity oraz pojedynczy bit parzystości
      (taki, aby suma bitów była parzysta).

  parity_check(rx_bits: List[int]) -> Tuple[bool, List[int]]
    Opis:
      Sprawdza parzystość i oddziela bity danych od bitu parzystości.
    Parametry:
      rx_bits: otrzymana lista bitów, gdzie ostatni bit traktowany jest jako bit
               parzystości.
    Zwraca:
      (ok, data):
        ok (bool) — True jeżeli parzystość zgadza się (brak wykrytego błędu),
        data (List[int]) — lista bitów danych bez bitu parzystości.

  hamming74_encode(nibble: List[int]) -> List[int]
    Opis:
      Koduje 4-bitowy nibble do 7-bitowego słowa Hamming(7,4).
    Parametry:
      nibble: lista długości 4 zawierająca bity [d1,d2,d3,d4].
    Zwraca:
      7-bitowe słowo w układzie [p1,p2,d1,p3,d2,d3,d4], gdzie p1,p2,p3 to bity parzystości.

  hamming74_encode_bits(data_bits: List[int]) -> List[int]
    Opis:
      Koduje ciąg bitów, dzieląc go na grupy po 4 bity (nibile). Ostatnia grupa
      jest uzupełniana zerami jeżeli jest krótsza niż 4 bity.
    Parametry:
      data_bits: lista bitów dowolnej długości.
    Zwraca:
      Lista bitów po rozszerzeniu każdej grupy 4-bitowej do 7-bitowego kodu Hamming(7,4).

  hamming74_check_and_extract(rx7: List[int]) -> Tuple[bool, List[int]]
    Opis:
      Sprawdza pojedyncze 7-bitowe słowo Hamming(7,4), oblicza syndrom, dokonuje
      korekcji pojedynczego błędu (jeżeli syndrom wskazuje pozycję 1..7) i zwraca
      wyekstrahowane 4 bity danych.
    Parametry:
      rx7: lista 7 bitów reprezentująca odebrane słowo Hamming.
    Zwraca:
      (ok, data):
        ok (bool) — True jeżeli po ewentualnej korekcji wszystkie parzystości są poprawne,
        data (List[int]) — wyekstrahowane bity danych [d1,d2,d3,d4] po korekcji.
    Uwagi:
      Implementacja koryguje tylko pojedyncze błędy; błędy wielobitowe mogą pozostać
      niezauważone lub doprowadzić do niepoprawnych danych mimo ok==False.

  crc32_append(data_bits: List[int]) -> List[int]
    Opis:
      Oblicza CRC-32 (funkcja binascii.crc32) nad bajtową reprezentacją danych
      i dołącza 32 bity CRC (porządek big-endian bajtów) na końcu strumienia bitów.
    Parametry:
      data_bits: lista bitów, której długość dowolna (niezależnie od podziału na bajty —
                 konwersja do bajtów odbywa się przez pomocnicze funkcje bits_to_bytes).
    Zwraca:
      Nową listę bitów: oryginalne dane + 32-bitowe CRC.

  crc32_check(rx_bits: List[int]) -> Tuple[bool, List[int]]
    Opis:
      Sprawdza ostatnie 32 bity jako CRC-32 i porównuje z obliczonym CRC nad
      wcześniejszą częścią bitów.
    Parametry:
      rx_bits: odebrane bity zawierające dane + 32-bitowy CRC na końcu.
    Zwraca:
      (ok, data_bits):
        ok (bool) — True jeżeli CRC pasuje,
        data_bits (List[int]) — część danych bez dołączonego CRC (pusta lista, jeżeli
                               wejście krótsze niż 32 bity).

Przykłady użycia:
  - Dodanie parzystości przed wysyłką i weryfikacja po stronie odbiorczej:
      tx = parity_encode(data); ok, rx_data = parity_check(tx_received)
  - Kodowanie Hamming(7,4) przed przesyłem z możliwością korekcji pojedynczych błędów:
      tx = hamming74_encode_bits(data); po odebraniu każdej 7-bitowej grupy:
      ok, nibble = hamming74_check_and_extract(rx7)
  - Dołączanie CRC-32 aby wykrywać błędy wielobitowe:
      tx = crc32_append(data); ok, data = crc32_check(rx)

Uwagi implementacyjne i ograniczenia:
  - Funkcje zakładają, że wejściowe listy zawierają jedynie wartości 0 lub 1; nie
    wykonują rygorystycznej walidacji typów ani zakresów.
  - hamming74_encode_bits uzupełnia ostatni nibble zerami, co może wpływać na
    interpretację końcowych bitów po dekodowaniu — jeżeli istotna jest długość
    oryginalnych danych, należy tę długość przekazywać/dokumentować zewnętrznie.
  - crc32_append / crc32_check operują na bajtowej reprezentacji bitów (funkcje
    pomocnicze bits_to_bytes/bytes_to_bits). Niezgodności w porządkach bitów/bajtów
    mogą prowadzić do błędnych wyników CRC, więc format konwersji musi być spójny.
  - Złożoność czasowa każdego mechanizmu jest liniowa względem liczby bitów;
    złożoność pamięciowa jest również O(n) ze względu na zwracane kopie list bitów.
"""

# Parity (even)
def parity_encode(data_bits: List[int]) -> List[int]:
    p = sum(data_bits) % 2
    return data_bits + [p]

def parity_check(rx_bits: List[int]) -> Tuple[bool, List[int]]:
    data, p = rx_bits[:-1], rx_bits[-1]
    ok = (sum(data) + p) % 2 == 0
    return ok, data

# Hamming(7,4) - basic for 4-bit nibble
def hamming74_encode(nibble: List[int]) -> List[int]:
    d = nibble + [0,0,0]
    d1,d2,d3,d4 = nibble

    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]

def hamming74_encode_bits(data_bits: List[int]) -> List[int]:
    out = []
    from .utils import chunk
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

# CRC32 append/check (byte-oriented)
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
