import random
from typing import List

"""
Symulacja kanału Gilberta–Elliotta.

Parametry:
  bits: lista bitów (0/1).
  p_gb: prawdopodobieństwo przejścia G->B (przed generacją błędu).
  p_bg: prawdopodobieństwo przejścia B->G (przed generacją błędu).
  err_good: prawdopodobieństwo błędu w stanie G.
  err_bad: prawdopodobieństwo błędu w stanie B.
  seed: opcjonalny seed (ustawia globalny generator random).

Zachowanie:
  Kanał startuje w stanie 'G'. Dla każdego bitu najpierw może nastąpić zmiana stanu,
    Wejściowa lista bitów (0/1). Każdy element jest traktowany jako
    pojedynczy symbol binarny. Funkcja dokonuje XOR-u z bitem błędu
    (0/1), więc oczekiwane wartości to 0 lub 1.
  p_gb (float):
    Prawdopodobieństwo przejścia ze stanu Good (G) do stanu Bad (B)
    przed wygenerowaniem błędu dla danego bitu. Wartość powinna należeć
    do przedziału [0.0, 1.0].
  p_bg (float):
    Prawdopodobieństwo przejścia ze stanu Bad (B) do stanu Good (G)
    przed wygenerowaniem błędu dla danego bitu. Wartość powinna należeć
    do przedziału [0.0, 1.0].
  err_good (float):
    Prawdopodobieństwo wystąpienia błędu (flipa bitu) w stanie Good (G).
    Wartość w przedziale [0.0, 1.0].
  err_bad (float):
    Prawdopodobieństwo wystąpienia błędu (flipa bitu) w stanie Bad (B).
    Wartość w przedziale [0.0, 1.0].
  seed (int, opcjonalnie):
    Opcjonalne źródło losowości — jeżeli nie jest None, funkcja ustawia
    globalny seed modułu random na tę wartość dla reprodukowalności.
    Uwaga: użycie parametru seed zmienia globalny generator losowy w
    module random, co może wpływać na inne części programu korzystające
    z tego modułu.

Zachowanie / algorytm:
  - Kanał zaczyna w stanie "G" (good).
  - Dla każdego bitu wejściowego, w poniższej kolejności:
    1. Sprawdzany jest obecny stan kanału.
    2. Na podstawie stanu wybierane jest odpowiadające prawdopodobieństwo
       błędu (err_good lub err_bad).
    3. Najpierw wykonywana jest potencjalna zmiana stanu:
       - Jeżeli bieżący stan to 'G' i random.random() < p_gb, stan
         zostaje ustawiony na 'B'.
       - Jeżeli bieżący stan to 'B' i random.random() < p_bg, stan
         zostaje ustawiony na 'G'.
       (Uwaga: w tej implementacji decyzja o zmianie stanu jest podejmowana
       przed generacją błędu dla bieżącego symbolu; dzięki temu błąd
       jest zawsze obliczany z użyciem prawdopodobieństwa odpowiadającego
       stanowi po ewentualnej zmianie, co jest zachowaniem specyficznym
       dla implementacji.)
    4. Generowany jest losowy bit błędu z prawdopodobieństwem err_p i
       wykonywany jest XOR z bitem wejściowym, aby otrzymać bit wyjściowy.
  - Zwracana jest lista bitów wyjściowych o tej samej długości co lista
    wejściowa.

Zwraca:
  List[int]: Nowa lista bitów (0/1) po przejściu przez kanał, tej samej
  długości co parametry wejściowe.

Przykłady użycia:
  - Powtarzalne symulacje: podając seed otrzymamy takie same sekwencje
    losowe wielokrotnie.
  - Eksperymenty z pamięcią kanału: zwiększając p_gb i p_bg zmieniamy
    częstotliwość przeskoków między stanami; zwiększając różnicę między
    err_good i err_bad zwiększamy kontrast między „dobrym” i „złym” stanem.

Uwagi implementacyjne / ograniczenia:
  - Funkcja używa globalnego generatora random modułu random i modyfikuje
    jego seed, jeśli podano parametr seed. Dla izolowania losowości najlepiej
    użyć instancji random.Random wewnątrz funkcji zamiast seedować globalnie.
  - Funkcja nie weryfikuje typu ani poprawności wartości parametrów
    (np. że bits zawiera tylko 0/1 lub że prawdopodobieństwa są w [0,1]).
    W realnym użyciu warto dodać walidację wejścia, by uniknąć błędów.
  - Złożoność czasowa: O(n), gdzie n to liczba bitów.
  - Złożoność pamięciowa: O(n) (zwracana lista wyjściowa).
"""

def bsc_channel(bits: List[int], p_flip: float, seed: int = None) -> List[int]:
    if seed is not None:
        random.seed(seed)
    return [b ^ (1 if random.random() < p_flip else 0) for b in bits]

def gilbert_elliott_channel(bits: List[int], p_gb: float, p_bg: float,
                             err_good: float, err_bad: float,
                             seed: int = None) -> List[int]:
    if seed is not None:
        random.seed(seed)
    state = 'G'
    out = []
    for bit in bits:
        if state == 'G':
            err_p = err_good
            if random.random() < p_gb:
                state = 'B'
        else:
            err_p = err_bad
            if random.random() < p_bg:
                state = 'G'
        out.append(bit ^ (1 if random.random() < err_p else 0))
    return out


