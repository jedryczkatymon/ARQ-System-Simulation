import random
from typing import List

"""
Modele kanałów binarnych używane w symulacji.

Dostępne funkcje:
- bsc_channel(bits, p_flip, seed=None)
    Binary Symmetric Channel: odwrócenie bitu z prawdopodobieństwem p_flip.
    Używa lokalnej instancji random.Random(seed).
- gilbert_elliott_channel(bits, p_gb, p_bg, err_good, err_bad, seed=None)
    Gilbert–Elliott: model z dwoma stanami (G/B) i przejściami p_gb/p_bg.
    Błędy generowane z prawdopodobieństwem zależnym od stanu.
    Używa lokalnego RNG (seed opcjonalny).

Uwagi:
- Funkcje nie walidują typów/zakresów parametrów.
- seed=None -> instancja RNG z losowym ziarnem (różne przebiegi).
"""

def bsc_channel(bits: List[int], p_flip: float, seed: int = None) -> List[int]:
    rnd = random.Random(seed)
    return [b ^ (1 if rnd.random() < p_flip else 0) for b in bits]

def gilbert_elliott_channel(bits: List[int], p_gb: float, p_bg: float,
                             err_good: float, err_bad: float,
                             seed: int = None) -> List[int]:
    rnd = random.Random(seed)
    state = 'G'
    out = []
    for bit in bits:
        if state == 'G':
            if rnd.random() < p_gb:
                state = 'B'
            err_p = err_good if state == 'G' else err_bad
        else:
            if rnd.random() < p_bg:
                state = 'G'
            err_p = err_bad if state == 'B' else err_good
        out.append(bit ^ (1 if rnd.random() < err_p else 0))
    return out


