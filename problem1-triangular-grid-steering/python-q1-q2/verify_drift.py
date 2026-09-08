#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 n>=7 的'斜向漂移'路线 (每层 1 张卡), 与蛇形路线比较, 得到第二问最终公式."""
import math

SQ3 = math.sqrt(3.0)
R = 9.0

def c(m, n):
    return (20.0 * m + 10.0 * n, 10.0 * SQ3 * n)

def layer(k):
    return [c(m, n) for m in range(-k, k + 1) for n in range(-k, k + 1)
            if max(abs(m), abs(n), abs(m + n)) == k]

def disks_upto(n):
    out = []
    for k in range(1, n + 1):
        out += layer(k)
    return out

def seg_min_dist(P0, v, L, C):
    t = (C[0] - P0[0]) * v[0] + (C[1] - P0[1]) * v[1]
    if t <= 0:
        px, py = P0
    elif t >= L:
        px, py = P0[0] + L * v[0], P0[1] + L * v[1]
    else:
        px, py = P0[0] + t * v[0], P0[1] + t * v[1]
    return math.hypot(px - C[0], py - C[1])

def check(turns, disks):
    pts = [(0.0, 0.0)]
    P = (0.0, 0.0)
    for (th, L) in turns:
        a = math.radians(th)
        v = (math.cos(a), math.sin(a))
        Q = (P[0] + L * v[0], P[1] + L * v[1])
        pts.append(Q)
        P = Q
    mind = 1e9
    for (Cx, Cy) in disks:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            if L == 0:
                continue
            ux, uy = dx / L, dy / L
            mind = min(mind, seg_min_dist((x0, y0), (ux, uy), L, (Cx, Cy)))
    return mind

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def ray_chord(P, th_deg, chord):
    """intersection of ray from P (deg) with the infinite chord line; None if behind."""
    a = math.radians(th_deg)
    v = (math.cos(a), math.sin(a))
    # chord through (x0,y0),(x1,y1)
    (x0, y0), (x1, y1) = chord
    dx, dy = x1 - x0, y1 - y0
    det = v[0] * dy - v[1] * dx
    if abs(det) < 1e-12:
        return None
    t = ((x0 - P[0]) * dy - (y0 - P[1]) * dx) / det
    if t < -1e-9:
        return None
    return (P[0] + t * v[0], P[1] + t * v[1])

alpha = math.degrees(math.asin(R / 20.0))     # 26.744
beta = 30.0 - math.degrees(math.acos(0.9))    # 4.158

# base points of the 9-card Q1 slalom
T1 = (18.1715, 9.1567)
Pe = (35.4381, 7.9014)   # ell_1 ∩ chord (2,0)-(1,1)
eps = 64.1581            # tangent to (1,1) from Pe

# drift crossings (hand-computed, each on a gate chord, alternating tangents)
seq = [
    (eps, ((c(2,1)), (c(1,2)))),       # gate 3: (2,1)-(1,2)   -> Q1
    (57.36, ((c(2,2)), (c(1,3)))),     # gate 4: (2,2)-(1,3)   -> Q2
    (62.10, ((c(2,3)), (c(1,4)))),     # gate 5: (2,3)-(1,4)   -> Q3
    (58.10, ((c(2,4)), (c(1,5)))),     # gate 6: (2,4)-(1,5)   -> Q4
    (62.00, ((c(2,5)), (c(1,6)))),     # gate 7: (2,5)-(1,6)   -> Q5
    (57.95, ((c(2,6)), (c(1,7)))),     # gate 8: (2,6)-(1,7)   -> Q6
    (62.00, ((c(2,7)), (c(1,8)))),     # gate 9
    (58.00, ((c(2,8)), (c(1,9)))),     # gate 10
]

# 数值求解: 每个 tangent 角从当前点对下一圆盘做精确切线
# 这里直接用上面手算值; 为稳妥, 重新精确计算每步的切线角:
P = Pe
cur = eps
steps = []          # (heading, Q)
for (th_nom, chord) in seq:
    # 实际切线: 当前点 P 对"挡路盘"的切线
    # 挡路盘: 下一弦的两个端点中较近的一个? 用与当前方向夹角最小的切线
    pass

# 直接用上面 seq 的航向, 计算各弦交点:
turns = [(alpha, dist((0, 0), T1)), (-beta, dist(T1, Pe))]
P = Pe
for (th, chord) in seq:
    Q = ray_chord(P, th, chord)
    if Q is None:
        print("BEHIND at", th, chord)
        break
    turns.append((th, dist(P, Q)))
    P = Q
turns.append((th, 60.0))   # 最后一段直线

for n in range(3, 9):
    # n 层: 需要穿过的门: 第2层(已在Pe), 第3..n层: seq 前 n-2 个
    turns_n = [(alpha, dist((0, 0), T1)), (-beta, dist(T1, Pe))]
    P = Pe
    for j in range(n - 2):
        th, chord = seq[j]
        Q = ray_chord(P, th, chord)
        turns_n.append((th, dist(P, Q)))
        P = Q
    turns_n.append((th, 60.0))
    md = check(turns_n, disks_upto(n))
    cards = 7 + 14 + (2 if n >= 4 else 0) + max(0, n - 4)
    print(f"[drift n={n}] min dist = {md:.5f}; cards = {cards}")
