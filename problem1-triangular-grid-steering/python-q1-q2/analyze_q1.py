#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
避障游戏 Q1 的几何可行性数值勘探。
模型: 机器人缩为质点, 障碍物膨胀为半径 9 的圆盘(相切不算碰撞 -> 要求距离 >= 9)。
路径: 从原点出发的折线; 每段直线; 转向任意角, 但每张卡 <= 5 度。
Q1: 至少几张卡才能穿出前两层围栏(18 个圆盘)。
"""
import math
import numpy as np

R = 9.0
SQ3 = math.sqrt(3.0)
EPS = 1e-6

def c(m, n):
    return (20.0 * m + 10.0 * n, 10.0 * SQ3 * n)

def layer_points(k):
    """All lattice points (m,n) with max(|m|,|n|,|m+n|) = k (the k-th layer)."""
    return [(m, n) for m in range(-k, k + 1) for n in range(-k, k + 1)
            if max(abs(m), abs(n), abs(m + n)) == k]

layer1 = [c(m, n) for (m, n) in layer_points(1)]
layer2 = [c(m, n) for (m, n) in layer_points(2)]
DISKS = layer1 + layer2
assert len(layer1) == 6 and len(layer2) == 12, (len(layer1), len(layer2))


def ray_safe_len(P, th_deg):
    """从 P 沿方向 th_deg 出发, 到第一次进入某个圆盘的距离(圆盘=前两层, 相切允许)。"""
    th = math.radians(th_deg)
    vx, vy = math.cos(th), math.sin(th)
    L = 1e9
    for (Cx, Cy) in DISKS:
        dx, dy = Cx - P[0], Cy - P[1]
        d0 = math.hypot(dx, dy)
        if d0 < R - EPS:
            return 0.0
        tau = dx * vx + dy * vy
        if tau <= 0.0:
            continue
        dp = abs(dx * vy - dy * vx)
        if dp >= R - EPS:
            continue
        L = min(L, tau - math.sqrt(R * R - dp * dp))
    return L


def feasible_set(P):
    """从 P 出发的"安全方向集"(射线扫到无穷远都不撞前两层圆盘), 返回角度区间列表(度)。"""
    bad = []
    for (Cx, Cy) in DISKS:
        dx, dy = Cx - P[0], Cy - P[1]
        d = math.hypot(dx, dy)
        if d < R - EPS:
            return []
        a = math.degrees(math.asin(min(1.0, R / d)))
        phi = math.degrees(math.atan2(dy, dx))
        lo = (phi - a) % 360.0
        hi = (phi + a) % 360.0
        if lo > hi:
            bad.append((lo, 360.0))
            bad.append((0.0, hi))
        else:
            bad.append((lo, hi))
    bad.sort()
    feas = []
    cur = 0.0
    for (lo, hi) in bad:
        if lo > cur + 1e-9:
            feas.append((cur, lo))
        cur = max(cur, hi)
    if cur < 360.0 - 1e-9:
        feas.append((cur, 360.0))
    return feas


def best_dir(feas, th):
    """到可行方向集的最小角距离, 以及达到它的方向。"""
    th = th % 360.0
    best = 1e9
    bd = None
    for (lo, hi) in feas:
        if lo - 1e-9 <= th <= hi + 1e-9:
            return 0.0, th
        for cand in (lo, hi):
            d = abs(th - cand)
            d = min(d, 360.0 - d)
            if d < best:
                best = d
                bd = cand
    return best, bd


# ---------- sanity: 原点到各方向的安全长度 ----------
print("== sanity: 从原点出发的直线能走多远 ==")
for a in [13.0, 14.93, 15.0, 26.74, 30.0, 33.26, 45.0]:
    print(f"  theta={a:6.2f}deg  safe_len={ray_safe_len((0.0, 0.0), a):.3f}")

print("\n== 第二层门 A((2,0)-(1,1)) 的原点射线窗口: 安全长度>40 的角 ==")
for a in np.arange(12.0, 16.0, 0.05):
    if ray_safe_len((0.0, 0.0), a) > 40.0:
        print(f"  theta={a:.2f}  escapes")

# ---------- 一次转向搜索 ----------
print("\n== 一次转向(2 段)搜索: th1 in [26.75,33.25], t1 in [17.35,25.65] ==")
best1 = None
for th1 in np.arange(26.75, 33.26, 0.05):
    for t1 in np.arange(17.35, 25.65, 0.05):
        if ray_safe_len((0.0, 0.0), th1) < t1 - EPS:
            continue
        P1 = (t1 * math.cos(math.radians(th1)), t1 * math.sin(math.radians(th1)))
        feas = feasible_set(P1)
        if not feas:
            continue
        d, bd = best_dir(feas, th1)
        if best1 is None or d < best1[0]:
            best1 = (d, (th1, t1, bd))
if best1 is None:
    print("  没有可行的 1 次转向路径")
else:
    print(f"  最优 1 次转向: 需转角 = {best1[0]:.3f} deg, (th1,t1,th2) = {best1[1]}")

# ---------- 两次转向搜索 (粗网格) ----------
print("\n== 两次转向(3 段)搜索(粗网格) ==")
best = None
cnt = 0
for th1 in np.arange(26.75, 33.26, 0.25):
    c1, s1 = math.cos(math.radians(th1)), math.sin(math.radians(th1))
    for t1 in np.arange(17.35, 25.65, 0.25):
        if ray_safe_len((0.0, 0.0), th1) < t1 - EPS:
            continue
        P1 = (t1 * c1, t1 * s1)
        for th2 in np.arange(-90.0, 90.01, 1.0):
            L2 = ray_safe_len(P1, th2)
            if L2 < 2.0:
                continue
            c2, s2 = math.cos(math.radians(th2)), math.sin(math.radians(th2))
            t2 = 0.5
            t2max = min(L2, 45.0)
            while t2 <= t2max + 1e-9:
                P2 = (P1[0] + t2 * c2, P1[1] + t2 * s2)
                feas = feasible_set(P2)
                if feas:
                    d, bd = best_dir(feas, th2)
                    cards = math.ceil(abs(th2 - th1) / 5.0 - 1e-9) + math.ceil(d / 5.0 - 1e-9)
                    if best is None or cards < best[0]:
                        best = (cards, (th1, t1, th2, t2, bd, d))
                t2 += 0.75
        cnt += 1
        if cnt % 100 == 0:
            print(f"  ... processed {cnt} (th1,t1) pairs, best={best[0] if best else None} cards")
if best is None:
    print("  粗网格没找到可行的 2 次转向路径")
else:
    print(f"  粗网格最优: {best[0]} 张卡, 参数 {best[1]}")

# ---------- 精细化 ----------
if best is not None:
    (th1b, t1b, th2b, t2b, bdb, db) = best[1]
    print("\n== 精细网格(局部) ==")
    fine = None
    for th1 in np.arange(th1b - 0.4, th1b + 0.401, 0.05):
        for t1 in np.arange(t1b - 0.4, t1b + 0.401, 0.05):
            if ray_safe_len((0.0, 0.0), th1) < t1 - EPS:
                continue
            P1 = (t1 * math.cos(math.radians(th1)), t1 * math.sin(math.radians(th1)))
            for th2 in np.arange(th2b - 2.0, th2b + 2.01, 0.1):
                L2 = ray_safe_len(P1, th2)
                if L2 < 2.0:
                    continue
                c2, s2 = math.cos(math.radians(th2)), math.sin(math.radians(th2))
                t2 = max(0.1, t2b - 1.5)
                t2max = min(L2, t2b + 1.5)
                while t2 <= t2max + 1e-9:
                    P2 = (P1[0] + t2 * c2, P1[1] + t2 * s2)
                    feas = feasible_set(P2)
                    if feas:
                        d, bd = best_dir(feas, th2)
                        cards = math.ceil(abs(th2 - th1) / 5.0 - 1e-9) + math.ceil(d / 5.0 - 1e-9)
                        if fine is None or cards < fine[0]:
                            fine = (cards, (th1, t1, th2, t2, bd, d))
                    t2 += 0.1
    print(f"  精细最优: {fine[0] if fine else None} 张卡, 参数 {fine[1] if fine else None}")

    # ---------- 独立验证 ----------
    if fine is not None:
        (th1v, t1v, th2v, t2v, th3v, dv) = fine[1]
        print("\n== 独立验证最优候选 ==")
        pts = [(0.0, 0.0)]
        segs = [(th1v, t1v), (th2v, t2v), (th3v, 70.0)]
        P = (0.0, 0.0)
        for (th, L) in segs:
            th = math.radians(th)
            v = (math.cos(th), math.sin(th))
            Q = (P[0] + L * v[0], P[1] + L * v[1])
            pts.append(Q)
            P = Q
        print("  转折点:", [(round(x, 3), round(y, 3)) for (x, y) in pts[:3]])
        mind = 1e9
        for (Cx, Cy) in DISKS:
            for i in range(len(pts) - 1):
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                dx, dy = x1 - x0, y1 - y0
                L = math.hypot(dx, dy)
                ux, uy = dx / L, dy / L
                tau = (Cx - x0) * ux + (Cy - y0) * uy
                if tau <= 0:
                    px, py = x0, y0
                elif tau >= L:
                    px, py = x1, y1
                else:
                    px, py = x0 + tau * ux, y0 + tau * uy
                mind = min(mind, math.hypot(px - Cx, py - Cy))
        print(f"  全路径到 18 个圆盘的最小距离 = {mind:.4f} (要求 >= 9)")
        print(f"  转向角: {abs(th2v-th1v):.3f} deg (需 {math.ceil(abs(th2v-th1v)/5.0-1e-9)} 卡), "
              f"{abs(th3v-th2v):.3f} deg (需 {math.ceil(abs(th3v-th2v)/5.0-1e-9)} 卡)")
