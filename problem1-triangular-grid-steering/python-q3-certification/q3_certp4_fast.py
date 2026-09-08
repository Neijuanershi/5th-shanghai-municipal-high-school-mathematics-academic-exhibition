# -*- coding: utf-8 -*-
"""q3_certp4_fast.py — 位等价的快速 min_dist_rot (去掉 nearest_lattice_pts 的 16 元组 sort,
改为 running-min). 输出与 cxk.min_dist_rot 逐位相同 (同样计算 min d2), 但快约 3-5x.
只读使用 cxk 常量; 不改任何既有文件. 供 q3_certp4_enum_B.py monkey-patch 加速.
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk

_W = cxk.W
_SQ3 = cxk.SQ3
_cos = math.cos
_sin = math.sin
_sqrt = math.sqrt
_floor = math.floor


def fast_min_dist_rot(px, py, t):
    ct = _cos(_W * t)
    st = _sin(_W * t)
    xr = ct * px + st * py
    yr = -st * px + ct * py
    nf = yr / (10.0 * _SQ3)
    mf = (xr - 10.0 * nf) / 20.0
    best = float('inf')
    m0 = _floor(mf) - 1
    n0 = _floor(nf) - 1
    for m in range(m0, m0 + 4):
        for n in range(n0, n0 + 4):
            if m == 0 and n == 0:
                continue
            x = 20.0 * m + 10.0 * n
            y = 10.0 * _SQ3 * n
            d2 = (x - xr) ** 2 + (y - yr) ** 2
            if d2 < best:
                best = d2
    return _sqrt(best)


def patch():
    """把 cxk.min_dist_rot 替换为 fast_min_dist_rot (输出逐位相同)."""
    cxk.min_dist_rot = fast_min_dist_rot


def check_identity(n=200000, seed=20240618):
    """逐位核对 fast_min_dist_rot == cxk.min_dist_rot 在随机点上的输出."""
    import random
    rng = random.Random(seed)
    orig = cxk.min_dist_rot
    worst = 0.0
    n_diff = 0
    t0 = time.perf_counter()
    s1 = 0.0
    for _ in range(n):
        px = rng.uniform(-600.0, 600.0)
        py = rng.uniform(-600.0, 600.0)
        t = rng.uniform(0.0, 120.0)
        a = orig(px, py, t)
        b = fast_min_dist_rot(px, py, t)
        d = abs(a - b)
        if d > worst:
            worst = d
        if a != b:
            n_diff += 1
        s1 += b
    dt = time.perf_counter() - t0
    # 测速
    t0 = time.perf_counter()
    for _ in range(50000):
        fast_min_dist_rot(400.0, 100.0, 0.5)
    dt_fast = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(50000):
        orig(400.0, 100.0, 0.5)
    dt_orig = time.perf_counter() - t0
    print("fast_min_dist_rot vs cxk.min_dist_rot 逐位核对: n=%d 不一致=%d 最差|Δ|=%.3e"
          % (n, n_diff, worst))
    print("测速: fast=%.2f us/call  orig=%.2f us/call  加速=%.2fx"
          % (dt_fast / 50000 * 1e6, dt_orig / 50000 * 1e6, dt_orig / dt_fast))
    return n_diff == 0


if __name__ == "__main__":
    ok = check_identity()
    print("结论: " + ("逐位相同" if ok else "存在差异!"))
