# -*- coding: utf-8 -*-
"""q3_certp3_cliffwidth.py — 对关键悬崖做 1D 细采样, 精确测过渡带宽度(真·悬崖宽度)。

在细网格最优 (Δ1=9.831, L1=11.0595, slow=1) 附近:
  A. Δ1 方向悬崖: L1=11.0595 固定, Δ1∈[9.830, 9.831] 步 0.00001°;
  B. L1 方向悬崖: Δ1=9.831 固定, L1∈[11.0478, 11.0595] 步 0.02 mm。
输出每条悬崖的跳变位置、步高、以及"过渡带宽度"(相邻采样点间隔, 即悬崖的真·尖锐度上界)。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3_certp3_core as core

_ST = None


def _init_worker():
    global _ST
    _ST = core.state()


def _eval_d1(d1):
    return (d1, core.terminal_score(d1, 11.0595, 1, _ST))


def _eval_l1(l1):
    return (l1, core.terminal_score(9.831, l1, 1, _ST))


def transitions(sweep, unit):
    """找出分数跳变(相邻 |Δ|>1m), 返回 [(x_lo, x_hi, s_lo, s_hi, step)]。"""
    out = []
    for i in range(len(sweep) - 1):
        x0, s0 = sweep[i]
        x1, s1 = sweep[i + 1]
        if abs(s0 - s1) > 1.0:
            out.append((x0, x1, s0, s1, abs(x1 - x0)))
    return out


def main():
    import multiprocessing as mp
    st = core.state()

    print("=== A. Δ1 方向悬崖 (L1=11.0595, slow=1, Δ1∈[9.830,9.831] 步 1e-5°) ===")
    d1s = [9.830 + 1e-5 * k for k in range(101)]
    with mp.Pool(8, initializer=_init_worker) as pool:
        sweep = pool.map(_eval_d1, d1s, chunksize=8)
    tr = transitions(sweep, "deg")
    print(f"  采样 {len(sweep)} 点, 跳变数={len(tr)}")
    for (x0, x1, s0, s1, step) in tr:
        print(f"    Δ1 {x0:.5f}→{x1:.5f} (间隔 {step*1e5:.2f}e-5°): {s0:.4f}→{s1:.4f} 步高 {abs(s1-s0):.4f}")

    print("\n=== B. L1 方向悬崖 (Δ1=9.831, slow=1, L1∈[11.0478,11.0595] 步 0.02mm) ===")
    l1s = [11.0478 + 2e-5 * k for k in range(int((11.0595 - 11.0478) / 2e-5) + 1)]
    with mp.Pool(8, initializer=_init_worker) as pool:
        sweep = pool.map(_eval_l1, l1s, chunksize=8)
    tr = transitions(sweep, "m")
    print(f"  采样 {len(sweep)} 点, 跳变数={len(tr)}")
    for (x0, x1, s0, s1, step) in tr:
        print(f"    L1 {x0:.6f}→{x1:.6f} (间隔 {step*1000:.2f}mm): {s0:.4f}→{s1:.4f} 步高 {abs(s1-s0):.4f}")

    # 顺带: 连续 argmax 舍入点 (9.8328°, L1=11.0595) 核验
    print("\n=== C. 连续 argmax 舍入点核验 ===")
    r = core.terminal_score(9.8328, 11.0595, 1, st)
    print(f"  (Δ1=9.8328, L1=11.0595, slow=1) → {r:.4f}  (已知: 舍入后 440.42)")
    r = core.terminal_score(9.831, 11.0595, 1, st)
    print(f"  (Δ1=9.831,  L1=11.0595, slow=1) → {r:.4f}  (细网格最优 447.9725)")


if __name__ == "__main__":
    main()
