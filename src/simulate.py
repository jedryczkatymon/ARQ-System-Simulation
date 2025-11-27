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

    bits = random_bitstream(total_bits, seed=seed)
    packets = packetize(bits, payload_size)

    tx_channel = lambda b: bsc_channel(b, p_flip=0.01, seed=None)
    ack_channel = lambda b: bsc_channel(b, p_flip=0.01, seed=None)

    stats_parity = stop_and_wait(
        packets,
        encode=lambda p: parity_encode(p),
        check_and_extract=lambda r: parity_check(r),
        channel_tx=tx_channel,
        channel_ack=ack_channel,
        max_retries=5
    )

    print("Parity stats:", stats_parity)

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

    stats_crc8 = stop_and_wait(
        packets,
        encode=lambda p: crc8_append(p),
        check_and_extract=lambda r: crc8_check(r),
        channel_tx=tx_channel,
        channel_ack=ack_channel,
        max_retries=5
    )
    print("CRC8 stats:", stats_crc8)

    stats_crc16 = stop_and_wait(
        packets,
        encode=lambda p: crc16_append(p),
        check_and_extract=lambda r: crc16_check(r),
        channel_tx=tx_channel,
        channel_ack=ack_channel,
        max_retries=5
    )
    print("CRC16 stats:", stats_crc16)

    stats_checksum = stop_and_wait(
        packets,
        encode=lambda p: checksum16_append(p),
        check_and_extract=lambda r: checksum16_check(r),
        channel_tx=tx_channel,
        channel_ack=ack_channel,
        max_retries=5
    )
    print("Checksum16 stats:", stats_checksum)

    stats_hamming = stop_and_wait(
        packets,
        encode=lambda p: hamming74_encode_bits(p),
        check_and_extract=lambda r: hamming74_check_bits(r),
        channel_tx=tx_channel,
        channel_ack=ack_channel,
        max_retries=5
    )
    print("Hamming(7,4) stats:", stats_hamming)

if __name__ == "__main__":
    main()
