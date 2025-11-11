from typing import List, Callable, Tuple
from copy import deepcopy

"""
Stop-and-wait ARQ — symulacja prostego protokołu z potwierdzeniami.

Opis:
  Funkcja symuluje działanie protokołu Stop-and-Wait ARQ dla sekwencji pakietów binarnych.
  Dla każdego pakietu:
    - pakiet jest najpierw kodowany przez dostarczoną funkcję encode,
    - zakodowany ciąg wysyłany jest przez kanał transmitujący (channel_tx),
    - odbiornik sprawdza integralność i ewentualnie wyciąga dane za pomocą
      check_and_extract, zwracając parę (ok, data),
    - nadawca otrzymuje jednobitowe potwierdzenie (ACK) symulowane przez
      channel_ack (bit 1 = ACK, 0 = NACK),
    - jeśli nadawca otrzyma ACK=1, przechodzi do następnego pakietu,
      w przeciwnym razie retransmituje pakiet do osiągnięcia limitu prób max_retries.

Parametry:
  packets (List[List[int]]):
    Lista pakietów; każdy pakiet jest listą bitów (0/1). Każdy element traktowany
    jest jako pojedynczy bit payloadu.
  encode (Callable[[List[int]], List[int]]):
    Funkcja kodująca pakiet przed wysłaniem. Przyjmuje listę bitów i zwraca
    listę bitów (ramka/kodowany ciąg) do wysłania przez channel_tx.
  check_and_extract (Callable[[List[int]], Tuple[bool, List[int]]]):
    Funkcja wykonywana po odebraniu ramki na stronie odbiorczej. Powinna zwrócić
    krotkę (ok, data), gdzie ok (bool) oznacza, czy ramka przeszła kontrolę (np. CRC),
    a data (List[int]) to wyekstrahowany payload (może być niezmieniony albo pusta
    lista w przypadku błędu).
  channel_tx (Callable[[List[int]], List[int]]):
    Funkcja symulująca kanał transmisji danych. Przyjmuje listę bitów (ramkę) i
    zwraca listę bitów odebranych na drugim końcu (może zawierać błędy lub zmiany
    długości zależnie od modelu kanału).
  channel_ack (Callable[[List[int]], List[int]]):
    Funkcja symulująca kanał potwierdzeń (ACK). Przyjmuje jednobitową listę [1] lub [0]
    i zwraca listę bitów odebranych przez nadawcę. Implementacja spodziewa się, że
    otrzymany wynik jest indeksowalny i że pierwszy element odpowiada odebranemu ACK.
  max_retries (int, opcjonalnie):
    Maksymalna liczba retransmisji (domyślnie 10). Pętla retransmisji pozwala na próbę
    wysyłki aż do momentu otrzymania ACK=1 lub do przekroczenia tego limitu.
    Uwaga: w implementacji warunek pętli używa porównania <= max_retries, co wpływa na
    interpretację liczby prób (zawiera próbę zerową i zwiększenia licznika przy niepowodzeniu).

Zwraca:
  dict: Słownik ze statystykami symulacji zawierający pola:
    - 'total_sent_bits' (int): łączna liczba bitów wysłanych przez channel_tx
      (liczona jako długość zakodowanej ramki przy każdej próbie).
    - 'payload_bits' (int): łączna liczba bitów payloadu (suma długości oryginalnych pakietów)
      — liczona raz na pakiet przed pętlą retransmisji.
    - 'retries_per_packet' (List[int]): lista liczby prób (retransmisji) dla każdego pakietu;
      wartość odzwierciedla licznik retries z pętli po zakończeniu obsługi pakietu
      (zarówno w przypadku sukcesu jak i wyczerpania prób).
    - 'undetected_errors' (int): licznik przypadków, gdy check_and_extract zwróciło ok == True,
      ale wyekstrahowane dane różniły się od oryginalnego pakietu (błąd nie wykryty przez mechanizm).

Zachowanie / algorytm:
  Dla każdego pakietu:
    1. Zwiększa stats['payload_bits'] o długość oryginalnego pakietu.
    2. Wywołuje encode(pkt) w celu otrzymania ramki do wysyłki.
    3. W pętli retransmisji (dopóki retries <= max_retries):
        - Zwiększa stats['total_sent_bits'] o długość zakodowanej ramki.
        - Wysyła ramkę przez channel_tx (używając deepcopy zakodowanej ramki).
        - Odbiera wynik check_and_extract(rx) -> (ok, data).
        - Tworzy jednobitowy ACK = [1] jeśli ok else [0], wysyła przez channel_ack
          (również z deepcopy).
        - Jeżeli odebrany ack_rx jest truthy i ack_rx[0] == 1, to:
          * Jeżeli ok == True, ale data != pkt, inkrementuje undetected_errors.
          * Uzyskuje sukces i przerywa pętlę.
        - W przeciwnym razie zwiększa licznik retries i powtarza.
    4. Po zakończeniu pętli zapisuje liczbę retries do 'retries_per_packet'.
  Pętla liczy wysłania ramki i symuluje zarówno błędy w kanale danych, jak i w kanale ACK;
  funkcja nie wykonuje rzeczywistego kodowania ani dekodowania poza wywołaniami przekazanych funkcji.

Przykłady użycia:
  - Testy protokołu: podstawiając różne modele channel_tx/channel_ack
    (np. binarne kanały losowe, modele z pamięcią) można badać wpływ błędów na liczbę
    retransmisji i nie wykryte błędy.
  - Porównanie mechanizmów detekcji błędów: podstawiając różne funkcje check_and_extract
    (np. z CRC o różnej długości) można ocenić częstość undetected_errors.

Uwagi implementacyjne / ograniczenia:
  - Funkcja zakłada, że encode, check_and_extract, channel_tx i channel_ack są poprawnie
    zaimplementowane i zwracają typy oczekiwane przez tę funkcję; brak jest szczegółowej
    walidacji wejść (np. czy pakiety składają się wyłącznie z 0/1).
  - Statystyka 'total_sent_bits' liczy długość zwracaną przez encode dla każdej próby;
    jeżeli encode zwraca strukturę niestandardową lub liczy bity inaczej, metryka może być
    nieadekwatna.
  - Funkcja używa deepcopy przed wysyłkami (symulacja niezależnych kopii); koszt kopiowania
    może mieć wpływ przy bardzo dużych ramach.
  - Złożoność czasowa: O(sum_i len(encode(pkt_i)) * attempts_i), gdzie attempts_i ≤ max_retries+1
    dla każdego pakietu.
  - Złożoność pamięciowa: O(1) dodatkowej pamięci poza wynikiem i buforami, choć encode/channel
    mogą zwracać nowe listy bitów.
"""

def stop_and_wait(packets: List[List[int]],
                  encode: Callable[[List[int]], List[int]],
                  check_and_extract: Callable[[List[int]], Tuple[bool, List[int]]],
                  channel_tx: Callable[[List[int]], List[int]],
                  channel_ack: Callable[[List[int]], List[int]],
                  max_retries: int = 10) -> dict:
    stats = {
        'total_sent_bits': 0,
        'payload_bits': 0,
        'retries_per_packet': [],
        'undetected_errors': 0
    }
    for pkt in packets:
        retries = 0
        stats['payload_bits'] += len(pkt)
        encoded = encode(pkt)
        success = False
        while retries <= max_retries:
            stats['total_sent_bits'] += len(encoded)
            rx = channel_tx(deepcopy(encoded))
            ok, data = check_and_extract(rx)
            ack = [1 if ok else 0]
            ack_rx = channel_ack(deepcopy(ack))
            if ack_rx and ack_rx[0] == 1:
                if ok and data != pkt:
                    stats['undetected_errors'] += 1
                success = True
                break
            retries += 1
        stats['retries_per_packet'].append(retries)
    return stats
