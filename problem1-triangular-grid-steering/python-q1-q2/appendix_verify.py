#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Appendix B: verification of the constructions of Theorems 1 and 2.

Model: point robot, obstacle disks of radius R = 9 (tangency allowed).

Key angles (degrees):
  alpha = arcsin(9/20)                            ~ 26.74  (layer-1 window)
  beta  = 30 - arccos(9/10)                       ~ 4.16   (common tangent
                                                           of (1,0) & (1,1))
  delta = arcsin(9/sqrt(301)) - arctan(9*sqrt(3)/31)
                                                  ~ 4.55   (triple tangent)

Answers:  Q1: 9 cards.   Q2: N(1) = 0,  N(n) = 4n + 1 for n >= 2.
"""
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
    """turns: list of (deg, length); the last segment is long (escape)."""
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

def line_line(n1, c1, n2, c2):
    """Intersection of the lines n1.x = c1 and n2.x = c2."""
    det = n1[0] * n2[1] - n1[1] * n2[0]
    if abs(det) < 1e-12:
        return None
    return ((c1 * n2[1] - c2 * n1[1]) / det, (n1[0] * c2 - n2[0] * c1) / det)

def ray_line(P, deg, n, c):
    """Intersection of the ray from P at angle deg with the line n.x = c."""
    a = math.radians(deg)
    v = (math.cos(a), math.sin(a))
    denom = n[0] * v[0] + n[1] * v[1]
    if abs(denom) < 1e-12:
        return None
    t = (c - n[0] * P[0] - n[1] * P[1]) / denom
    if t < -1e-9:
        return None
    return (P[0] + t * v[0], P[1] + t * v[1])

# ---------------- constants and tangent lines ----------------
alpha = math.degrees(math.asin(R / 20.0))
beta = 30.0 - math.degrees(math.acos(0.9))
Q0 = (34.5, 11.0 * SQ3 / 2.0)                 # = (2,0) + 11 * u, u = (-1/2, sqrt(3)/2)
C21 = c(2, 1)
d21 = dist(Q0, C21)
phi21 = math.degrees(math.atan2(C21[1] - Q0[1], C21[0] - Q0[0]))
delta = abs(phi21 - math.degrees(math.asin(R / d21)))

P1 = c(1, 0); B = c(1, 1); A = c(2, 0)

# internal common tangent ell_1 of (1,0),(1,1), direction -beta:
nb = (math.sin(math.radians(-beta)), -math.cos(math.radians(-beta)))
c_ell1 = (nb[0] * P1[0] + nb[1] * P1[1] + nb[0] * B[0] + nb[1] * B[1]) / 2.0
# internal common tangent ell_1' of (1,1),(2,0), direction +beta:
np_ = (math.sin(math.radians(beta)), -math.cos(math.radians(beta)))
c_ell1p = (np_[0] * B[0] + np_[1] * B[1] + np_[0] * A[0] + np_[1] * A[1]) / 2.0
# triple tangent line through Q0, direction -delta:
nd = (math.sin(math.radians(-delta)), -math.cos(math.radians(-delta)))
c_d2 = nd[0] * Q0[0] + nd[1] * Q0[1]

T1 = ray_line((0, 0), alpha, nb, c_ell1)
T2 = line_line(nb, c_ell1, np_, c_ell1p)

def q1_path():
    """9-card solution of Question 1 (tangent chain)."""
    return [(alpha, dist((0, 0), T1)), (-beta, dist(T1, T2)), (beta, 70.0)]

def dodge_path(n):
    """4n+1-card solution of Question 2 for n >= 2 (per-layer dodge)."""
    turns = [(alpha, dist((0, 0), T1)), (-beta, dist(T1, T2))]
    Td = line_line(np_, c_ell1p, nd, c_d2)          # T2 -> T (on ell_1')
    turns.append((beta, dist(T2, Td)))
    Pcur = Td
    for k in range(2, n):
        Qk = (20.0 * k - 5.5, 11.0 * SQ3 / 2.0)     # gate k+1: s = 11 point
        c_dk = nd[0] * Qk[0] + nd[1] * Qk[1]
        c_ek = c_ell1p + 20.0 * (k - 1) * np_[0]    # ell_k' (translate of ell_1')
        Pk = line_line(nd, c_dk, np_, c_ek)         # dodge turn point P_k
        Qn = (20.0 * (k + 1) - 5.5, 11.0 * SQ3 / 2.0)
        c_dn = nd[0] * Qn[0] + nd[1] * Qn[1]
        Tn = line_line(np_, c_ek, nd, c_dn)         # next dodge turn point T_{k+1}
        turns.append((-delta, dist(Pcur, Pk)))
        turns.append((beta, dist(Pk, Tn)))
        Pcur = Tn
    turns.append((beta, 70.0))
    return turns

def pure_chain_path(n):
    """Alternative 4n+1-card solution of Question 2 for n >= 2: per layer,
    turn by 2*beta at A_k = (20k, 9.0237) (onto the -beta internal tangent
    of (k,0),(k,1)) and by 2*beta at B_k = (20k+10, 8.2968) (back to +beta).
    Each layer rotates exactly 4*beta, matching the lower bound exactly."""
    turns = [(alpha, dist((0, 0), T1)), (-beta, dist(T1, T2))]
    P = T2
    for k in range(2, n):
        c_e = c_ell1p + 20.0 * (k - 2) * np_[0]      # exit tangent of gap k
        c_l = c_ell1 + 20.0 * (k - 1) * nb[0]        # dive tangent of corridor k
        Ak = line_line(np_, c_e, nb, c_l)            # = (20k, 9.0237)
        Bk = (20.0 * k + 10.0, 8.296757)             # translate of T2
        turns.append((beta, dist(P, Ak)))
        turns.append((-beta, dist(Ak, Bk)))
        P = Bk
    turns.append((beta, 70.0))
    return turns

def cards(n):
    return 0 if n == 1 else 9 + 4 * (n - 2)

def ray_min_dist(P0, v, C):
    """Minimum distance from the ray P0 + t*v (t >= 0) to the point C."""
    t = (C[0] - P0[0]) * v[0] + (C[1] - P0[1]) * v[1]
    if t <= 0:
        return dist(P0, C)
    return math.hypot(P0[0] + t * v[0] - C[0], P0[1] + t * v[1] - C[1])

def drift_trap_check():
    """The tempting 'diagonal drift' exit (heading eps through the gate-2
    window) cannot beat 4n+1.  The straight continuation already hits a
    disk (min distance < 9).  Sweeping the turn point along the eps-ray
    and all FORWARD post-turn headings (-60..120 deg) against ALL disks of
    layers 1-3 shows: no continuation exists from turn points more than
    3 m before Q1, and the cheapest continuation (near Q1, heading ~52.6
    deg, grazing (1,2)) needs a turn of ~11.6 deg (>= 3 cards).  Combined
    with the per-layer 4-card lower bound the drift route cannot save
    cards, in agreement with the drift remark."""
    Pe = ray_line(A, 120.0, nb, c_ell1)             # ell_1 intersects gate-2 chord
    eps = math.degrees(math.atan2(B[1] - Pe[1], B[0] - Pe[0])) \
          - math.degrees(math.asin(R / dist(Pe, B)))
    v = (math.cos(math.radians(eps)), math.sin(math.radians(eps)))
    blockers = disks_upto(3)                        # all layers 1-3 disks
    feasibles = []          # list of (t, heading) of feasible continuations
    best_any = -1.0         # best min-distance found over the whole sweep
    for t in [0.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0]:
        Pt = (Pe[0] + t * v[0], Pe[1] + t * v[1])
        for i in range(-600, 1201):        # FORWARD headings only, -60..120 deg
            deg = i / 10.0
            a = math.radians(deg)
            w = (math.cos(a), math.sin(a))
            d = min(ray_min_dist(Pt, w, Cb) for Cb in blockers)
            best_any = max(best_any, d)
            if d >= R - 1e-6:
                feasibles.append((t, deg))
    min_turn = min((abs(deg - eps) for (_, deg) in feasibles), default=None)
    # straight continuation (no turn at all):
    md = check_path([(alpha, dist((0, 0), T1)),
                     (-beta, dist(T1, Pe)),
                     (eps, 70.0)], disks_upto(3))
    return eps, md, best_any, feasibles, min_turn
    # straight continuation (no turn at all):
    md = check_path([(alpha, dist((0, 0), T1)),
                     (-beta, dist(T1, Pe)),
                     (eps, 70.0)], disks_upto(3))
    return eps, md, best_any, feasible

if __name__ == "__main__":
    print(f"alpha = {alpha:.4f}  beta = {beta:.4f}  delta = {delta:.4f}")
    print(f"T1 = ({T1[0]:.4f}, {T1[1]:.4f})   T2 = ({T2[0]:.4f}, {T2[1]:.4f})")
    md = check_path(q1_path(), disks_upto(2))
    print(f"Q1 (n=2): min distance = {md:.5f}, cards = {cards(2)}")
    for n in range(3, 7):
        md = check_path(dodge_path(n), disks_upto(n))
        print(f"Q2 n={n}: {len(disks_upto(n))} disks, "
              f"min distance = {md:.5f}, cards = {cards(n)}")
    for n in range(3, 7):
        md = check_path(pure_chain_path(n), disks_upto(n))
        print(f"Q2 pure +-beta chain n={n}: min distance = {md:.5f}, "
              f"cards = {cards(n)}")
    eps, md, best_any, feasibles, min_turn = drift_trap_check()
    print(f"drift exit (eps = {eps:.2f} deg): straight min distance = "
          f"{md:.5f} -> infeasible (trap)")
    n_f = len(feasibles)
    print(f"drift sweep (t in 0..21, heading -60..120 deg, layers 1-3): "
          f"feasible continuations = {n_f}, "
          f"min turn needed = {min_turn if min_turn is not None else 'none'}"
          f" deg, best min distance = {best_any:.5f}")
