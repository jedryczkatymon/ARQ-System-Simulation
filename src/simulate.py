from generator import random_bitstream, packetize
from coder import checksum16_append, checksum16_check, crc16_append, crc16_check, crc8_append, crc8_check, hamming74_check_bits, parity_encode, parity_check, crc32_append, crc32_check, hamming74_encode_bits, hamming74_check_and_extract
from channel import bsc_channel, gilbert_elliott_channel
from arq import stop_and_wait
import argparse

"""
Runner symulacji ARQ — demonstracja kodów i modeli kanału.

Zawiera:
- CLI (--seed) dla powtarzalności (seed=None -> losowy przebieg).
- Przykładowe eksperymenty: parity, Hamming(7,4), CRC8/16/32, checksum16.
- Przykładowe kanały: BSC oraz Gilbert‑Elliott.

Uwagi:
- Skrypt ma charakter demonstracyjny; parametry (rozmiar, BER, p_gb, ...) można rozszerzyć.
"""

def main():
    parser = argparse.ArgumentParser(description="Run ARQ simulation. Omit --seed for random signal.")
    parser.add_argument('--seed', type=int, default=None, help='Optional integer seed for reproducibility')
    args = parser.parse_args()
    seed = args.seed

    total_bits = 1024
    payload_size = 32
    N_RUNS = 500

    # prepare aggregation containers for each experiment
    experiments = {
        'Parity': {
            'encode': lambda p: parity_encode(p),
            'check': lambda r: parity_check(r),
            'tx_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=s)),
            'ack_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=(None if s is None else s+1000000))),
        },
        'CRC32': {
            'encode': lambda p: crc32_append(p),
            'check': lambda r: crc32_check(r),
            'tx_factory': lambda s: (lambda b: gilbert_elliott_channel(b, p_gb=0.001, p_bg=0.1, err_good=0.001, err_bad=0.1, seed=s)),
            'ack_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=(None if s is None else s+2000000))),
        },
        'CRC8': {
            'encode': lambda p: crc8_append(p),
            'check': lambda r: crc8_check(r),
            'tx_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=s)),
            'ack_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=(None if s is None else s+3000000))),
        },
        'CRC16': {
            'encode': lambda p: crc16_append(p),
            'check': lambda r: crc16_check(r),
            'tx_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=s)),
            'ack_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=(None if s is None else s+4000000))),
        },
        'Checksum16': {
            'encode': lambda p: checksum16_append(p),
            'check': lambda r: checksum16_check(r),
            'tx_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=s)),
            'ack_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=(None if s is None else s+5000000))),
        },
        'Hamming74': {
            'encode': lambda p: hamming74_encode_bits(p),
            'check': lambda r: hamming74_check_bits(r),
            'tx_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=s)),
            'ack_factory': lambda s: (lambda b: bsc_channel(b, p_flip=0.01, seed=(None if s is None else s+6000000))),
        }
    }

    # aggregator: sums and counts
    agg = {}
    for name in experiments:
        agg[name] = {
            'total_sent_bits': 0,
            'payload_bits': 0,
            'sum_retries': 0,
            'count_retries': 0,
            'undetected_errors': 0
        }

    for run in range(N_RUNS):
        seed_run = None if seed is None else seed + run

        bits = random_bitstream(total_bits, seed=seed_run)
        packets = packetize(bits, payload_size)

        for name, exp in experiments.items():
            tx_channel = exp['tx_factory'](seed_run)
            ack_channel = exp['ack_factory'](seed_run)
            stats = stop_and_wait(
                packets,
                encode=exp['encode'],
                check_and_extract=exp['check'],
                channel_tx=tx_channel,
                channel_ack=ack_channel,
                max_retries=5
            )
            agg[name]['total_sent_bits'] += stats['total_sent_bits']
            agg[name]['payload_bits'] += stats['payload_bits']
            agg[name]['sum_retries'] += sum(stats['retries_per_packet'])
            agg[name]['count_retries'] += len(stats['retries_per_packet'])
            agg[name]['undetected_errors'] += stats.get('undetected_errors', 0)

    # compute and print averages
    print(f"Ran {N_RUNS} simulations. Aggregated (averages per run / per-packet):")
    for name, a in agg.items():
        avg_sent = a['total_sent_bits'] / N_RUNS
        avg_payload = a['payload_bits'] / N_RUNS
        avg_undetected = a['undetected_errors'] / N_RUNS
        avg_retries_per_packet = (a['sum_retries'] / a['count_retries']) if a['count_retries'] else 0
        efficiency = (avg_payload / avg_sent) if avg_sent else 0
        print(f"{name}: avg_sent_bits={avg_sent:.1f}, avg_payload_bits={avg_payload:.1f}, avg_retries_per_packet={avg_retries_per_packet:.3f}, avg_undetected_errors_per_run={avg_undetected:.3f}, efficiency={efficiency:.4f}")

if __name__ == "__main__":
    main()