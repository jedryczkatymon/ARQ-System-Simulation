from typing import List, Iterable

"""
Narzędzia konwersji bitów i pomocnicza funkcja dzielenia na kawałki.

Opis:
  Moduł zawiera trzy funkcje pomocnicze do pracy z reprezentacją bitową:
  - bits_to_bytes(bits): konwertuje sekwencję bitów (0/1) na obiekt bytes,
    grupując bity po 8 i dokładając bity 0 (przesunięcie w lewo) dla niepełnego bajtu.
  - bytes_to_bits(data): rozbija każdy bajt z obiektu bytes na listę bitów
    (MSB pierwszy).
  - chunk(lst, n): generator zwracający kolejne fragmenty listy/iterowalnego
    obiektu o maksymalnej długości n.

Funkcje:

  bits_to_bytes(bits: Iterable[int]) -> bytes
    Parametry:
      bits: Iterowalny obiekt liczb całkowitych (oczekiwane wartości 0 lub 1).
    Zachowanie:
      - Bity są przetwarzane w kolejności otrzymanej z iterowalnego wejścia.
      - Każde 8 kolejnych bitów tworzy jeden bajt, gdzie pierwszy przetworzony
        bit staje się najbardziej znaczącym bitem bajtu (MSB).
      - Jeśli liczba bitów nie jest wielokrotnością 8, ostatni bajt jest
        dopełniony z prawej strony zerami (bity są przesunięte w lewo).
    Zwraca:
      Obiekt bytes zawierający zakodowane bajty.

  bytes_to_bits(data: bytes) -> List[int]
    Parametry:
      data: Obiekt bytes lub dowolna sekwencja bajtów.
    Zachowanie:
      - Dla każdego bajtu generowana jest lista ośmiu bitów w porządku od MSB
        do LSB (tj. bity 7..0).
    Zwraca:
      Lista int (0/1) o długości równej 8 * len(data).

  chunk(lst: List, n: int)
    Parametry:
      lst: Lista lub sekwencja poddawana dzieleniu.
      n: Maksymalny rozmiar pojedynczego kawałka (int > 0).
    Zachowanie:
      - Zwraca generator, który kolejno yielduje podlisty lst[i:i+n] dla i
        skokiem równym n, aż do końca listy.
    Zwraca:
      Generator fragmentów listy (każdy fragment jest widokiem/podlistą).

Przykłady użycia:
  - Przekształcenie bitów na bajty i z powrotem:
      b = bits_to_bytes([1,0,0,0,0,0,0,1])  # jeden bajt 0x81
      bits = bytes_to_bits(b)               # [1,0,0,0,0,0,0,1]
  - Dzielenie dużej listy na bloki:
      for block in chunk(my_list, 1024):
          process(block)

Uwagi implementacyjne / ograniczenia:
  - Funkcje zakładają poprawne typy wejściowe (np. bits zawiera 0/1).
    Brak walidacji wartości może prowadzić do nieoczekiwanych rezultatów.
  - bits_to_bytes wykonuje dopełnienie zerami dla niepełnych bajtów; jeśli
    wymagane inne dopełnienie, trzeba je zaimplementować oddzielnie.
  - Kolejność bitów: zarówno bits_to_bytes jak i bytes_to_bits traktują
    pierwszy element wejścia jako najbardziej znaczący bit bajtu (big-endian
    w obrębie bajtu).
  - Złożoność czasowa: O(n) dla operacji zależnych od liczby bitów/bajtów.
  - Złożoność pamięciowa: O(n) — zwracane struktury (lista lub bytes)
    rosną liniowo z rozmiarem wejścia.
"""

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
