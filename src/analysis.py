"""
This module provides functionality for analyzing ARQ system simulation results.

It processes aggregated data from multiple simulation runs to compute statistics
such as efficiency, retransmission rates, and undetected errors for different
encoding schemes. The analysis includes:
- Per-encoder performance summaries
- Ranking of encoders by efficiency, retries, and error detection
- Channel-based grouping and comparison
- Heuristic conclusions about encoder performance trade-offs
"""

def analyze_results(agg_data, n_runs, experiments_meta):
    # prepare per-encoder summaries
    summary = []
    for name, a in agg_data.items():
        avg_sent = a['total_sent_bits'] / n_runs
        avg_payload = a['payload_bits'] / n_runs
        avg_undetected = a['undetected_errors'] / n_runs
        avg_retries = (a['sum_retries'] / a['count_retries']) if a['count_retries'] else 0
        eff = (avg_payload / avg_sent) if avg_sent else 0
        ch = experiments_meta[name].get('channel', 'unknown')
        summary.append({
        'name': name,
        'channel': ch,
        'efficiency': eff,
        'avg_retries_per_packet': avg_retries,
        'avg_undetected_per_run': avg_undetected
        })

    # best/worst
    by_eff = sorted(summary, key=lambda x: x['efficiency'], reverse=True)
    by_retries = sorted(summary, key=lambda x: x['avg_retries_per_packet'])
    by_undetected = sorted(summary, key=lambda x: x['avg_undetected_per_run'])

    print("\n--- Automated analysis / wnioski ---")
    print(f"Najlepsza efektywność: {by_eff[0]['name']} (eff={by_eff[0]['efficiency']:.4f})")
    print(f"Najmniej retransmisji (średnio na pakiet): {by_retries[0]['name']} (retries={by_retries[0]['avg_retries_per_packet']:.3f})")
    print(f"Najmniejsza liczba nierozpoznanych błędów (avg/run): {by_undetected[0]['name']} (undetected={by_undetected[0]['avg_undetected_per_run']:.3f})")

    # group by channel class
    channel_groups = {}
    for s in summary:
        channel_groups.setdefault(s['channel'], []).append(s)
    print("\nPorównanie wg klasy kanału:")
    for ch, items in channel_groups.items():
        avg_eff = sum(i['efficiency'] for i in items) / len(items)
        avg_und = sum(i['avg_undetected_per_run'] for i in items) / len(items)
        avg_ret = sum(i['avg_retries_per_packet'] for i in items) / len(items)
        print(f"- {ch}: mean_eff={avg_eff:.4f}, mean_retries={avg_ret:.3f}, mean_undetected={avg_und:.3f} (n={len(items)})")

    # krótkie wnioski (heurystyczne)
    print("\nHeurystyczne wnioski:")
    print("- Jeśli kod osiąga wysoką efektywność i jednocześnie niskie undetected -> dobry kompromis throughput/bezpieczeństwo.")
    print("- Kody z niskim avg_retries_per_packet minimalizują opóźnienia wywołane retransmisjami.")
    print("- Porównać wyniki dla 'BSC' vs 'Gilbert-Elliott' — bursty kanaly (Gilbert-Elliott) zwykle zwiększają liczbę retransmisji lub wymagają kodów wykrywających wiązki błędów.")