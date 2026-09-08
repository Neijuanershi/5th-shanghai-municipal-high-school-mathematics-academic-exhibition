# -*- coding: utf-8 -*-
"""q3_certp3_probe.py — 校验纪录结构 / 复现锚点分数 / 基准 cxk.simulate 速度。"""
import math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk

REC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q3_campaign_best_saA.txt")
TB = 3.7924
V = 10.0 * 1.25 ** 11
print(f"V = {V:.6f}  (used 116.4153)")

# --- 结构 ---
lines = [ln.rstrip("\n") for ln in open(REC, encoding="utf-8") if ln.strip()]
print(f"记录总行数 = {len(lines)}  (应为 102)")
print(f"第 1 行 = {lines[0]!r}  第 2 行 = {lines[1]!r}")
print(f"第 99 行 = {lines[98]!r}")
print(f"第 100 行 = {lines[99]!r}")
print(f"第 101 行 = {lines[100]!r}")
print(f"第 102 行 = {lines[101]!r}")
n_acc = sum(1 for ln in lines[2:] if ln.startswith("+"))
n_dec = sum(1 for ln in lines[2:] if ln.startswith("-"))
n_turn = sum(1 for ln in lines[2:] if ln.startswith("R"))
print(f"卡片: 加速={n_acc} 减速={n_dec} 转向={n_turn} 合计={n_acc+n_dec+n_turn}  (应为 100)")

# --- 原纪录分数 ---
ver, hd, ev = cxk.read_plan(REC)
r = cxk.simulate(hd, ev)
print(f"\n原纪录 cxk.simulate: collide={r['collide']} r={r['r']:.4f} t={r.get('t'):.4f}  (期望 447.8980)")


def build(d1, L1, slow, out):
    nl = lines[:99]
    nl.append(f"R {TB:.4f} {min(5.0, d1):.4f}")
    nl.append(f"R {TB:.4f} {d1 - min(5.0, d1):.4f}")
    t_slow = TB + L1 / V
    if slow:
        nl.append(f"- {t_slow:.4f}")
    else:
        nl.append(f"R {t_slow:.4f} 0.0000")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(nl) + "\n")
    return out


def sim_plan(d1, L1, slow):
    out = build(d1, L1, slow, "_tmp_probe.txt")
    ver, hd, ev = cxk.read_plan(out)
    res = cxk.simulate(hd, ev)
    return res


# --- 锚点复现 + 基准 ---
anchors = [
    (9.835, 11.06, 1, 447.9657),
    (9.88, 11.05, 1, 447.8980),
    (10.0, 11.0, 1, 447.7406),
    (10.0, 11.0, 0, None),
]
print("\n=== 锚点复现 ===")
for d1, L1, slow, expect in anchors:
    t0 = time.perf_counter()
    res = sim_plan(d1, L1, slow)
    dt = time.perf_counter() - t0
    note = "" if expect is None else f"(期望 {expect:.4f})"
    print(f"d1={d1} L1={L1} slow={slow}: r={res['r']:.4f} collide={res['collide']} "
          f"t={res.get('t'):.4f} 耗时={dt*1000:.0f} ms {note}")

# --- 基准: 连续 N 次 ---
N = 10
t0 = time.perf_counter()
for _ in range(N):
    sim_plan(9.835, 11.06, 1)
dt = time.perf_counter() - t0
print(f"\n基准: {N} 次 cxk.simulate 平均 {dt/N*1000:.1f} ms/次 → 5500 次约 {dt/N*5500:.0f} s")
