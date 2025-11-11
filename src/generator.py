import random
from typing import List
from utils import chunk

"""
Generowanie losowego strumienia bitów.

Opis:
  Funkcja tworzy listę losowych bitów (0 lub 1) o zadanej długości.
  Bit jest generowany jako losowy pojedynczy bit poprzez random.getrandbits(1).
  Funkcja może ustawić globalny seed modułu random, jeśli podano parametr seed,
  co pozwala na reprodukowalność wyników.

Parametry:
  length (int):
    Liczba bitów do wygenerowania. Oczekiwane wartości to liczby całkowite
    nieujemne. Przy długości 0 zwracana jest pusta lista.
  seed (int, opcjonalnie):
    Opcjonalna wartość seed ustawiana globalnie w module random przed
    generowaniem. Jeżeli seed jest None (domyślnie), nie następuje zmiana
    stanu generatora globalnego.

Zachowanie / algorytm:
  - Jeżeli seed nie jest None, wywoływane jest random.seed(seed), co ustawia
    globalny generator losowy w module random i zapewnia powtarzalność
    wygenerowanego strumienia pomiędzy uruchomieniami.
  - Następnie dla każdego z length elementów wywoływane jest
    random.getrandbits(1), co zwraca 0 lub 1.
  - Zwracana jest lista długości length zawierająca wygenerowane bity.

Zwraca:
  List[int]: Lista bitów (0/1) o długości równej parametrowi length.

Przykłady użycia:
  - Powtarzalne testy: podając konkretny seed otrzymamy tę samą sekwencję.
  - Szybkie generowanie surowych bitów do symulacji kanałów lub testów.

Uwagi implementacyjne / ograniczenia:
  - Funkcja modyfikuje globalny generator random poprzez random.seed(seed),
    jeżeli podano seed — może to wpływać na inne części programu używające
    tego generatora. Dla izolacji losowości zalecane jest korzystanie z
    instancji random.Random zamiast ustawiania globalnego seeda.
  - Nie następuje walidacja typu elementów zwracanej listy (zawsze 0/1),
    ani walidacja parametru length poza założeniami dokumentacyjnymi.
  - Złożoność czasowa: O(n), gdzie n = length.
  - Złożoność pamięciowa: O(n) (zwracana lista).
"""

"""
Podział strumienia bitów na pakiety (packetize).

Opis:
  Funkcja dzieli listę bitów na pakiety o zadanym rozmiarze ładunku (payload).
  Ostatni pakiet, jeśli ma krótszą długość niż payload_size, zostaje wypełniony
  zerami (padding) do żądanego rozmiaru. Zwracana jest lista pakietów, gdzie
  każdy pakiet jest listą bitów długości payload_size.

Parametry:
  bits (List[int]):
    Wejściowa lista bitów (oczekiwane wartości 0 lub 1). Funkcja traktuje
    każdy element jako pojedynczy symbol binarny.
  payload_size (int):
    Rozmiar ładunku w bitach dla pojedynczego pakietu. Powinien być dodatnią
    liczbą całkowitą (> 0). Każdy wynikowy pakiet będzie miał długość równą
    payload_size.

Zachowanie / algorytm:
  - Funkcja iteruje po wejściowej liście bits, grupując kolejne elementy
    w podlisty o maksymalnej długości payload_size (używając pomocniczej
    funkcji chunk z modułu utils).
  - Dla ostatniego fragmentu o długości mniejszej niż payload_size wykonuje
    się padding zerami tak, aby każdy pakiet miał stałą długość.
  - Kolejne pakiety są dodawane do wynikowej listy pakietów w tej samej
    kolejności co w wejściowym strumieniu.

Zwraca:
  List[List[int]]: Lista pakietów, gdzie każdy pakiet jest listą bitów długości
  payload_size. Jeżeli wejściowa lista bits była pusta, zwracana jest pusta
  lista.

Przykłady użycia:
  - Przygotowanie danych do transmisji ze stałym rozmiarem ramki.
  - Testy protokołów ARQ, gdzie pakiety muszą mieć określony rozmiar.

Uwagi implementacyjne / ograniczenia:
  - Funkcja zakłada, że utils.chunk zwraca kolejne fragmenty listy; nie weryfikuje
    typu ani zawartości fragmentów (np. czy bits zawiera tylko 0/1).
  - Nie ma obsługi nieprawidłowych wartości payload_size (np. <= 0) — warto dodać
    walidację wejścia, aby zapobiec błędom.
  - Złożoność czasowa: O(n), gdzie n to długość listy bits.
  - Złożoność pamięciowa: O(n) (wynikowa lista pakietów wraz z paddingiem).
"""

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
