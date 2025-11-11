from generator import random_bitstream, packetize
from coder import parity_encode, parity_check, crc32_append, crc32_check, hamming74_encode_bits, hamming74_check_and_extract
from channel import bsc_channel, gilbert_elliott_channel
from arq import stop_and_wait
import argparse

"""
Symulowany kanał według modelu Gilberta–Elliotta.

Opis:
  Funkcja symuluje przejście ciągu bitów przez kanał z pamięcią opisany
  modelem Gilberta–Elliotta. Model ten ma dwa stany: "G" (good) — stan
  o niskim prawdopodobieństwie błędu — oraz "B" (bad) — stan o wyższym
  prawdopodobieństwie błędu. Kanał może zmieniać stan w kolejnych bitach
  z pewnymi prawdopodobieństwami przejścia, a w zależności od aktualnego
  stanu generuje błędy z przypisanym prawdopodobieństwem.

Parametry:
  bits (List[int]):
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

def main():
    parser = argparse.ArgumentParser(description="Run ARQ simulation. Omit --seed for random signal.")
    parser.add_argument('--seed', type=int, default=None, help='Optional integer seed for reproducibility')
    args = parser.parse_args()
    seed = args.seed

    total_bits = 1024
    payload_size = 32

    bits = random_bitstream(total_bits, seed=seed)
    packets = packetize(bits, payload_size)

    tx_channel = lambda b: bsc_channel(b, p_flip=0.01, seed=None)
    ack_channel = lambda b: bsc_channel(b, p_flip=0.01, seed=None)

    # przykład z parity
    stats_parity = stop_and_wait(
        packets,
        encode=lambda p: parity_encode(p),
        check_and_extract=lambda r: parity_check(r),
        channel_tx=tx_channel,
        channel_ack=ack_channel,
        max_retries=5
    )

    print("Parity stats:", stats_parity)

    # przykład z CRC32
    tx_channel2 = lambda b: gilbert_elliott_channel(b, p_gb=0.001, p_bg=0.1, err_good=0.001, err_bad=0.1, seed=None)
    ack_channel2 = lambda b: bsc_channel(b, p_flip=0.01, seed=None)

    stats_crc = stop_and_wait(
        packets,
        encode=lambda p: crc32_append(p),
        check_and_extract=lambda r: crc32_check(r),
        channel_tx=tx_channel2,
        channel_ack=ack_channel2,
        max_retries=5
    )
    print("CRC32 stats:", stats_crc)

if __name__ == "__main__":
    main()
