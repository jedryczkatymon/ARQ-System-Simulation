from typing import List, Callable, Tuple
from copy import deepcopy

"""
Stop-and-Wait ARQ — prosty symulator retransmisji z potwierdzeniami.

Funkcje / oczekiwane callables:
- encode(packet: List[int]) -> List[int] : tworzy ramkę do wysyłki.
- check_and_extract(frame: List[int]) -> (ok: bool, data: List[int]) : walidacja i ekstrakcja.
- channel_tx(frame) / channel_ack(ack) : symulacja kanału danych i kanału ACK.

stop_and_wait zwraca słownik ze statystykami:
- total_sent_bits, payload_bits, retries_per_packet, undetected_errors.

Uwagi:
- stop_and_wait nie waliduje wejść; statystyki liczą długości zwracane przez encode.
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
