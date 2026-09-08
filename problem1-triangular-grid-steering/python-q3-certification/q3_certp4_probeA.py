# -*- coding: utf-8 -*-
"""q3_certp4_probeA.py — 诊断左半区 A 是否存在"慢/晚撞"终局。
逐点打印(flush), 扫描 Δ1 ∈ [9.8,9.85) 0.001° × 若干 k × slow, 报分数与耗时。
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core

st = core.state()
KS = [902, 926, 950, 974, 996]

for k in KS:
    L1 = k * 1e-4 * core.V0
    for s in (0, 1):
        print(f"=== k={k} (L1={L1:.6f}) slow={s} ===", flush=True)
        for i in range(50):
            d1 = round(9.800 + i * 0.001, 4)
            t0 = time.perf_counter()
            r = core.terminal_score(d1, L1, s, st)
            dt = (time.perf_counter() - t0) * 1000.0
            flag = " SLOW" if dt > 500 else (" HI" if r > 500 else "")
            print(f"  d1={d1:.4f} r={r:9.4f} {dt:7.1f}ms{flag}", flush=True)
        print("", flush=True)
print("PROBE DONE", flush=True)
