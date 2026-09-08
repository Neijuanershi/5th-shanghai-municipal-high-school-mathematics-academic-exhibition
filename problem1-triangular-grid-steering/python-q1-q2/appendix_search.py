#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Appendix A: numerical exploration for Question 1 (first two layers).

Model: shrink the robot to a point and inflate every obstacle disk to
radius R = 8 + 1 = 9.  Tangency is allowed, so every constraint reads
"distance >= 9".  The robot follows a polyline starting at the origin;
a turn of angle d costs ceil(|d|/5) cards.

Results: 0 turns: impossible; 1 turn: impossible; 2 turns: feasible
with 9 cards (turns of 30.90 deg and 8.32 deg); the optimal path is
tangent to the disks along its whole length (min distance = 9.00000).
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
    """Length along the ray from P (direction th_deg, degrees) until it
    first enters some disk; +inf (1e9) if it never does."""
    th = math.radians(th_deg)
    vx, vy = math.cos(th), math.sin(th)
    L = 1e9
    for (Cx, Cy) in DISKS:
        dx, dy = Cx - P[0], Cy - P[1]
        d0 = math.hypot(dx, dy)
        if d0 < R - EPS:
            return 0.0
        tau = dx * vx + dy * vy          # foot parameter along the ray
        if tau <= 0.0:
            continue
        dp = abs(dx * vy - dy * vx)      # perpendicular distance of the line
        if dp >= R - EPS:
            continue
        L = min(L, tau - math.sqrt(R * R - dp * dp))
    return L

def feasible_set(P):
    """Safe direction set of a ray from P clearing all disks to infinity,
    returned as a list of angular intervals (degrees)."""
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
    """Minimal angular distance from th to the feasible set, and the
    closest feasible direction."""
    th = th % 360.0
    best, bd = 1e9, None
    for (lo, hi) in feas:
        if lo - 1e-9 <= th <= hi + 1e-9:
            return 0.0, th
        for cand in (lo, hi):
            d = abs(th - cand)
            d = min(d, 360.0 - d)
            if d < best:
                best, bd = d, cand
    return best, bd

def seg_min_dist(P0, v, L, C):
    t = (C[0] - P0[0]) * v[0] + (C[1] - P0[1]) * v[1]
    if t <= 0:
        px, py = P0
    elif t >= L:
        px, py = P0[0] + L * v[0], P0[1] + L * v[1]
    else:
        px, py = P0[0] + t * v[0], P0[1] + t * v[1]
    return math.hypot(px - C[0], py - C[1])

def check_polyline(segs):
    """segs: list of (deg, length).  Returns minimal distance to all disks."""
    pts = [(0.0, 0.0)]
    P = (0.0, 0.0)
    for (th, L) in segs:
        a = math.radians(th)
        v = (math.cos(a), math.sin(a))
        Q = (P[0] + L * v[0], P[1] + L * v[1])
        pts.append(Q)
        P = Q
    mind = 1e9
    for (Cx, Cy) in DISKS:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy)
            if L == 0:
                continue
            ux, uy = dx / L, dy / L
            mind = min(mind, seg_min_dist((x0, y0), (ux, uy), L, (Cx, Cy)))
    return mind

def main():
    # ---- one-turn search over the first segment (direction, distance) ----
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
    print("one-turn search:", None if best1 is None else
          f"min required turn {best1[0]:.3f} deg at {best1[1]}")

    # ---- two-turn search (coarse grid) ----
    best = None
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
                        cards = math.ceil(abs(th2 - th1) / 5.0 - 1e-9) \
                                + math.ceil(d / 5.0 - 1e-9)
                        if best is None or cards < best[0]:
                            best = (cards, (th1, t1, th2, t2, bd, d))
                    t2 += 0.75
    print("two-turn coarse:", best)

    # ---- local refinement around the optimum ----
    if best:
        (th1b, t1b, th2b, t2b, bdb, db) = best[1]
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
                            cards = math.ceil(abs(th2 - th1) / 5.0 - 1e-9) \
                                    + math.ceil(d / 5.0 - 1e-9)
                            if fine is None or cards < fine[0]:
                                fine = (cards, (th1, t1, th2, t2, bd, d))
                        t2 += 0.1
        print("two-turn refined:", fine)
        if fine:
            (th1v, t1v, th2v, t2v, th3v, dv) = fine[1]
            segs = [(th1v, t1v), (th2v, t2v), (th3v, 70.0)]
            md = check_polyline(segs)
            print(f"independent verification: min distance = {md:.5f} (must be >= 9)")

if __name__ == "__main__":
    main()
