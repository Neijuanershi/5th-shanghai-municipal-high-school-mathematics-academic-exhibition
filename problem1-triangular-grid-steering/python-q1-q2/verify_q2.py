#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 Q1/Q2 构造路线。所有距离要求 >= 9 (相切允许)。"""
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

def check_path(turns, disks):
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
    return mind, pts

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def line_line(n1, c1, n2, c2):
    """intersect n1.x=c1 and n2.x=c2 (n = unit-ish normals)."""
    det = n1[0] * n2[1] - n1[1] * n2[0]
    if abs(det) < 1e-12:
        return None
    return ((c1 * n2[1] - c2 * n1[1]) / det, (n1[0] * c2 - n2[0] * c1) / det)

def ray_line(P, deg, n, c):
    """intersection of ray from P at angle deg with line n.x=c; None if behind."""
    a = math.radians(deg)
    v = (math.cos(a), math.sin(a))
    denom = n[0] * v[0] + n[1] * v[1]
    if abs(denom) < 1e-12:
        return None
    t = (c - n[0] * P[0] - n[1] * P[1]) / denom
    if t < -1e-9:
        return None
    return (P[0] + t * v[0], P[1] + t * v[1])

# ---------- 常量 ----------
alpha = math.degrees(math.asin(R / 20.0))            # 26.744
beta  = 30.0 - math.degrees(math.acos(0.9))          # 4.158
# delta: 从 Q=(34.5, 11*sqrt3/2) 出发与 (2,1) 相切的下切方向
Q0 = (34.5, 11.0 * SQ3 / 2.0)                        # (34.5, 9.5263)
C21 = c(2, 1)
d21 = dist(Q0, C21)
phi21 = math.degrees(math.atan2(C21[1] - Q0[1], C21[0] - Q0[0]))
delta = phi21 - math.degrees(math.asin(R / d21))      # 26.69 - 31.25 的绝对值 -> 取正
delta = abs(delta)

P1 = c(1, 0); B = c(1, 1); A = c(2, 0)

# 内公切线 ell_1: 与 P1,B 相切, 方向 -beta
nb = (math.sin(math.radians(-beta)), -math.cos(math.radians(-beta)))   # (-sin b, -cos b)
c_ell1 = (nb[0] * P1[0] + nb[1] * P1[1] + nb[0] * B[0] + nb[1] * B[1]) / 2.0
# 内公切线 ell_1': 与 B,A 相切, 方向 +beta
np_ = (math.sin(math.radians(beta)), -math.cos(math.radians(beta)))    # (sin b, -cos b)
c_ell1p = (np_[0] * B[0] + np_[1] * B[1] + np_[0] * A[0] + np_[1] * A[1]) / 2.0
# 三重线 (k=2): 方向 -delta 过 Q0
nd = (math.sin(math.radians(-delta)), -math.cos(math.radians(-delta)))
c_d2 = nd[0] * Q0[0] + nd[1] * Q0[1]

T1 = ray_line((0, 0), alpha, nb, c_ell1)
T2 = line_line(nb, c_ell1, np_, c_ell1p)
print(f"alpha={alpha:.4f} beta={beta:.4f} delta={delta:.4f}")
print(f"T1={T1}  (expect ~18.17,9.16)")
print(f"T2={T2}  (expect ~29.99,8.29)")

# ---------- Q1 (n=2) ----------
turns2 = [(alpha, dist((0, 0), T1)), (-beta, dist(T1, T2)), (beta, 70.0)]
md, _ = check_path(turns2, disks_upto(2))
cards2 = math.ceil((alpha + beta) / 5.0 - 1e-9) + math.ceil(2 * beta / 5.0 - 1e-9)
print(f"\n[Q1 n=2] min dist to 18 disks = {md:.5f}; cards = {cards2}; "
      f"turns = {alpha+beta:.3f} deg + {2*beta:.3f} deg")

# ---------- 蛇形(dodge)路线 ----------
def dodge_path(n):
    turns = [(alpha, dist((0, 0), T1)), (-beta, dist(T1, T2))]
    Pcur = T2
    # 沿 ell_1' (+beta) 到与三重线_2 的交点
    Td = line_line(np_, c_ell1p, nd, c_d2)
    turns.append((beta, dist(T2, Td)))
    Pcur = Td
    for k in range(2, n):
        Qk = (20.0 * k - 5.5, 11.0 * SQ3 / 2.0)
        c_dk = nd[0] * Qk[0] + nd[1] * Qk[1]
        # ell_k' : n+ . x = c_ell1p + 20(k-1) sin(beta)
        c_ek = c_ell1p + 20.0 * (k - 1) * np_[0]
        Pk = line_line(nd, c_dk, np_, c_ek)
        Qn = (20.0 * (k + 1) - 5.5, 11.0 * SQ3 / 2.0)
        c_dn = nd[0] * Qn[0] + nd[1] * Qn[1]
        Tn = line_line(np_, c_ek, nd, c_dn)
        turns.append((-delta, dist(Pcur, Pk)))
        turns.append((beta, dist(Pk, Tn)))
        Pcur = Tn
    turns.append((beta, 70.0))
    return turns

def dodge_cards(n):
    return 7 + 2 + 4 * (n - 2)

for n in [3, 4, 5, 6]:
    t = dodge_path(n)
    md, _ = check_path(t, disks_upto(n))
    print(f"[dodge n={n}] min dist to {len(disks_upto(n))} disks = {md:.5f}; cards = {dodge_cards(n)}")

# ---------- 漂移(drift)路线 ----------
# Pe = ell_1 ∩ 弦AB(方向120度)
u_AB = (math.cos(math.radians(120.0)), math.sin(math.radians(120.0)))
Pe = ray_line(A, 120.0, nb, c_ell1)
print(f"\n[drift] Pe = {Pe}  (expect ~35.44,7.90)")
dPe = dist(Pe, B)
phiPe = math.degrees(math.atan2(B[1] - Pe[1], B[0] - Pe[0]))
eps = phiPe - math.degrees(math.asin(R / dPe))
print(f"eps = {eps:.4f}  (expect ~64.16)")

def drift_sim(n):
    disks = disks_upto(n)
    P = Pe
    th = eps
    segs = []
    dangles = []
    for _ in range(300):
        a = math.radians(th)
        v = (math.cos(a), math.sin(a))
        best_tau, best_disk = 1e9, None
        for (Cx, Cy) in disks:
            dx, dy = Cx - P[0], Cy - P[1]
            d0 = math.hypot(dx, dy)
            if d0 < R - 1e-6:
                best_tau, best_disk = 0.0, (Cx, Cy)
                break
            tau = dx * v[0] + dy * v[1]
            if tau <= 0:
                continue
            dp = abs(dx * v[1] - dy * v[0])
            if dp >= R - 1e-6:
                continue
            tent = tau - math.sqrt(max(0.0, R * R - dp * dp))
            if tent < best_tau:
                best_tau, best_disk = tent, (Cx, Cy)
        r = math.hypot(P[0], P[1])
        if best_disk is None and r > 20 * n + 9:
            segs.append((th, 20.0))
            break
        if best_disk is None:
            segs.append((th, 30.0))
            P = (P[0] + 30 * v[0], P[1] + 30 * v[1])
            continue
        (Cx, Cy) = best_disk
        dx, dy = Cx - P[0], Cy - P[1]
        d = max(math.hypot(dx, dy), R)
        phi = math.degrees(math.atan2(dy, dx))
        a0 = math.degrees(math.asin(min(1.0, R / d)))
        t1 = (phi + a0) % 360.0
        t2 = (phi - a0) % 360.0
        def angdiff(x, y):
            d_ = abs(x - y) % 360.0
            return min(d_, 360.0 - d_)
        newth = t1 if angdiff(t1, th) <= angdiff(t2, th) else t2
        dth = angdiff(newth, th)
        segs.append((th, best_tau + 1e-6))
        P = (P[0] + (best_tau + 1e-6) * v[0], P[1] + (best_tau + 1e-6) * v[1])
        th = newth
        if dth > 1e-3:
            dangles.append(dth)
    return [(alpha, dist((0, 0), T1)), (-beta, dist(T1, Pe))] + segs, dangles

for n in [3, 4, 5, 6, 7, 8]:
    t, dang = drift_sim(n)
    md, _ = check_path(t, disks_upto(n))
    cards = 7 + 14 + sum(math.ceil(abs(x) / 5.0 - 1e-9) for x in dang)
    print(f"[drift n={n}] min dist = {md:.5f}; turns after entry = {[round(x,2) for x in dang]}; cards = {cards}")
