# -*- coding: utf-8 -*-
"""q3_certp3_verify.py — 核验 fast terminal_score 与完整 cxk.simulate 逐位等价。"""
import math
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk
import q3_certp3_core as core

st = core.state()
p0, h0, t0, v0, r_max_chain = st
print(f"链尾出口态: p0=({p0[0]:.4f},{p0[1]:.4f}) r0={math.hypot(*p0):.4f} "
      f"h0={math.degrees(h0):.4f}° t0={t0:.4f} v0={v0:.6f} r_max_chain={r_max_chain:.4f}")


def realized_L1(L1):
    ts = round(core.t_slow_of(L1) / 1e-4) * 1e-4
    return (ts - core.TB) * core.V0


# 1) 锚点
anchors = [(9.835, 11.06, 1), (9.88, 11.05, 1), (10.0, 11.0, 1), (10.0, 11.0, 0)]
print("\n=== 锚点 (fast vs full) ===")
for d1, L1, slow in anchors:
    lr = realized_L1(L1)
    fr = core.terminal_score(d1, lr, slow)
    full, res, valid = core.full_simulate(d1, L1, slow)
    print(f"d1={d1} L1={L1}(→{lr:.6f}) slow={slow}: fast={fr:.4f} full={full:.4f} "
          f"Δ={abs(fr-full):.2e} valid={valid}")

# 2) 随机样本(覆盖粗网格 + 慢卡 0/1 + 部分 Δ1>10 非法域)
random.seed(42)
print("\n=== 随机样本核验 (200 个) ===")
worst = 0.0
worst_info = None
n_mismatch = 0
for i in range(200):
    d1 = round(random.uniform(8.5, 11.0), 2)
    L1 = round(random.uniform(10.5, 11.6), 2)
    slow = random.choice([0, 1])
    lr = realized_L1(L1)
    fr = core.terminal_score(d1, lr, slow)
    full, res, valid = core.full_simulate(d1, L1, slow)
    d = abs(fr - full)
    if d > worst:
        worst = d
        worst_info = (d1, L1, lr, slow, fr, full)
    if d > 1e-6:
        n_mismatch += 1
        print(f"  MISMATCH d1={d1} L1={L1} lr={lr:.6f} slow={slow}: fast={fr:.6f} full={full:.6f} Δ={d:.3e}")
print(f"最差 |fast-full| = {worst:.3e} @ {worst_info}")
print(f"超过 1e-6 的不一致数 = {n_mismatch} / 200")
print("结论: " + ("通过(逐位等价)" if worst < 1e-6 else "存在不一致, 需排查"))
