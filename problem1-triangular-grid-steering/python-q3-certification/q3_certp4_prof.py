# -*- coding: utf-8 -*-
"""q3_certp4_prof.py — 分析 terminal_score 各段耗时 (只读, 不改任何既有文件)."""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk
import q3_certp3_core as core

st = core.state()
p0, h0, t0, v0, r_max_chain = st
print("r0=%.4f r_max_chain=%.4f v0=%.6f" % (math.hypot(*p0), r_max_chain, v0))

# 1) min_dist_rot 耗时
N = 50000
t = time.perf_counter()
s = 0.0
for i in range(N):
    s += cxk.min_dist_rot(400.0 + i * 1e-3, 100.0 + i * 1e-3, 0.5 + i * 1e-4)
dt = time.perf_counter() - t
print("min_dist_rot: %.2f us/call (%.0f calls)" % (dt / N * 1e6, N))

# 2) seg_collision 耗时 (11m 终局段)
d1 = 9.85
L1 = 947 * 1e-4 * v0
h = h0 + d1 * cxk.D2R if hasattr(cxk, 'D2R') else h0 + d1 * math.pi / 180.0
ux, uy = math.cos(h), math.sin(h)
t1 = t0 + L1 / v0
t = time.perf_counter()
hit = cxk.seg_collision(p0, ux, uy, v0, t0, t1)
dt_seg = time.perf_counter() - t
print("seg_collision: %.4f s, hit=%s" % (dt_seg, hit is not None))

# 3) ray_collision 耗时 (slow=1)
p1 = (p0[0] + v0 * ux * (t1 - t0), p0[1] + v0 * uy * (t1 - t0))
v = v0 * 0.8
t = time.perf_counter()
hit = cxk.ray_collision(p1, ux, uy, v, t1)
dt_ray = time.perf_counter() - t
print("ray_collision slow=1: %.4f s, hit_r=%.4f" % (dt_ray, math.hypot(*hit[1]) if hit else -1))

# 4) ray_collision 耗时 (slow=0)
v = v0
t = time.perf_counter()
hit = cxk.ray_collision(p1, ux, uy, v, t1)
dt_ray0 = time.perf_counter() - t
print("ray_collision slow=0: %.4f s, hit_r=%.4f" % (dt_ray0, math.hypot(*hit[1]) if hit else -1))

# 5) 统计 ray_collision 步数 (slow=1)
v = v0 * 0.8
dot = p1[0] * ux + p1[1] * uy
r0v = math.hypot(*p1)
r_cap = cxk.R_CAP_BASE + 60.0 * v + 100.0
nstep = 0
r = r0v
while r < r_cap:
    dr = cxk.STEP / (1.0 + cxk.W * r / v)
    r = min(r + dr, r_cap)
    nstep += 1
    if nstep > 2000000:
        break
print("ray_collision 步数(理论, 到 r_cap=%.0f)= %d, r0=%.2f" % (r_cap, nstep, r0v))
