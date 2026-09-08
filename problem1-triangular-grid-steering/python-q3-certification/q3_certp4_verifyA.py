# -*- coding: utf-8 -*-
"""q3_certp4_verifyA.py — 左半区 A 全枚举的评分器核验(锚点 + 随机对照完整 cxk.simulate)。

评分器: 复用 q3_certp3_core.terminal_score(终局段快评分, 与 cxk.simulate 逐位等价)。
本脚本把 6 个已知锚点 + 200 组随机方案(官方 t_slow 0.0001s 网格 + slow∈{0,1})分别用
fast 与完整 cxk.simulate 评分, 记录最差 |fast-full|, 结果写 q3_certp4_verifyA.json。
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk
import q3_certp3_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "q3_certp4_verifyA.json")

st = core.state()
p0, h0, t0, v0, r_max_chain = st


def l1_of_tslow(ts):
    return (ts - core.TB) * core.V0


# 已知锚点 (Δ1, t_slow, 期望分数, slow)
anchors = [
    (9.8305, 3.8874, 447.9733, 1),
    (9.8310, 3.8874, 447.9725, 1),
    (9.8350, 3.8874, 447.9657, 1),
    (9.8500, 3.8871, 447.9601, 1),
    (9.8304, 3.8874, 439.4987, 1),
    (9.8328, 3.8873, 440.4239, 1),
]

anchor_rows = []
for d1, ts, exp, slow in anchors:
    l1 = l1_of_tslow(ts)
    fast = core.terminal_score(d1, l1, slow, st)
    full, res, valid = core.full_simulate(d1, l1, slow)
    d = abs(fast - full)
    ok = (d <= 1e-6) and (abs(full - exp) <= 5e-4)
    anchor_rows.append(dict(d1=d1, t_slow=ts, l1=round(l1, 6), slow=slow,
                            expected=exp, fast=round(fast, 6), full=round(full, 6),
                            dfast_full=float(d), dfull_exp=round(full - exp, 6), ok=bool(ok)))

# 随机对照 (官方 t_slow 网格, k 覆盖 [895,1000], slow∈{0,1})
random.seed(20240617)
rows = []
worst = 0.0
worst_info = None
n_bad = 0
for i in range(200):
    d1 = round(random.uniform(9.0, 10.0), 4)          # 官方 0.0001° 可表示
    k = random.randint(895, 1000)
    ts = round(core.TB + k * 1e-4, 4)                 # 官方 0.0001s 网格
    l1 = (ts - core.TB) * core.V0
    slow = random.choice([0, 1])
    fast = core.terminal_score(d1, l1, slow, st)
    full, res, valid = core.full_simulate(d1, l1, slow)
    d = abs(fast - full)
    if d > worst:
        worst = d
        worst_info = (d1, ts, round(l1, 6), slow, fast, full)
    if d > 1e-6:
        n_bad += 1
    rows.append(dict(d1=d1, k=k, t_slow=ts, l1=round(l1, 6), slow=slow,
                     fast=round(fast, 6), full=round(full, 6), d=float(d)))

out = dict(
    chain_state=dict(p0=[round(p0[0], 6), round(p0[1], 6)],
                     r0=round(math.hypot(*p0), 6), h0_deg=round(math.degrees(h0), 6),
                     t0=core.TB, v0=v0, r_max_chain=round(r_max_chain, 6)),
    anchors=anchor_rows,
    anchors_all_ok=all(a["ok"] for a in anchor_rows),
    random_n=len(rows), random_worst_abs=worst, random_n_bad_gt_1e6=n_bad,
    random_worst_info=worst_info,
)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("chain_state:", out["chain_state"])
print("anchors:")
for a in anchor_rows:
    print("  ", a, "OK" if a["ok"] else "FAIL")
print("anchors_all_ok =", out["anchors_all_ok"])
print(f"random worst |fast-full| = {worst:.3e} @ {worst_info}")
print(f"random n_bad(>1e-6) = {n_bad} / {len(rows)}")
print("written:", OUT)
