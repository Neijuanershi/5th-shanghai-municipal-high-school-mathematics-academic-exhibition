# -*- coding: utf-8 -*-
"""
q3_certp2_xcheck.py — 子代理 J: 独立密采样交叉验证 (与 Lipschitz 认证互证).

目的:
  1. 用与认证完全独立的密集采样 (4000 点/段, 固定框架 + 正三角格点) 复核每一有限段的
     最小净距与最紧盘, 验证 q3_certp2_seg 的 '采样dmin' 与 '认证下界';
  2. 回答 audit_sim 的 min_clear < 9 是否来自终局射线 (射线本就必然撞盘), 而非链条;
  3. 用 audit.bisect_collision 复核终局首撞半径, 与 cxk.simulate / 认证区间并列.
"""
import math
import cxk
import q3_audit_sim as audit
import q3_certp2_seg as S

SQ3 = math.sqrt(3.0)
W = cxk.W


def build_segments(heading, events):
    events = sorted(events, key=lambda e: e[1])
    v = cxk.V0
    h = math.radians(heading)
    p = (0.0, 0.0)
    t = 0.0
    segs = []
    for (kind, tt, a) in events:
        if tt > t + 1e-12:
            ux, uy = math.cos(h), math.sin(h)
            segs.append((t, p[0], p[1], tt, v, ux, uy))
            p = (p[0] + v * ux * (tt - t), p[1] + v * uy * (tt - t))
            t = tt
        if kind == "spd":
            v *= a
        else:
            h += math.radians(a)
    return segs, (t, p[0], p[1], v, math.cos(h), math.sin(h))


def dense_min_seg(t0, p0x, p0y, t1, v, ux, uy, xs, ys, radii, ms, ns, N=4000):
    """密集采样一段的最小净距与最紧盘 (固定框架)."""
    ts = t0 + (t1 - t0) * (np.arange(N, dtype=float)) / (N - 1)
    px = p0x + v * ux * (ts - t0)
    py = p0y + v * uy * (ts - t0)
    ct = np.cos(W * ts); st = np.sin(W * ts)
    best = 1e9; bj = -1; bt = ts[0]
    # 分块避免内存过大
    for k in range(0, N, 512):
        sl = slice(k, min(k + 512, N))
        qx = np.outer(ct[sl], xs) - np.outer(st[sl], ys)
        qy = np.outer(st[sl], xs) + np.outer(ct[sl], ys)
        dx = px[sl, None] - qx
        dy = py[sl, None] - qy
        d = np.sqrt(dx * dx + dy * dy)
        j = int(np.argmin(d))
        m = float(d.min())
        if m < best:
            best = m
            bj = int(j % len(xs))
            bt = float(ts[sl][j // len(xs)])
    return best, bt, (int(ms[bj]), int(ns[bj])), float(radii[bj])


def main():
    import numpy as np
    xs, ys, radii, ms, ns = S.build_disks(500.0)

    ver, heading, events = cxk.read_plan("q3_campaign_best_saA.txt")
    segs, final = build_segments(heading, events)

    print("独立密采样 (4000 点/段) vs 认证采样dmin")
    print(f"{'段':>3} {'认证dmin':>11} {'密采样dmin':>11} {'差':>10} "
          f"{'密采样紧盘':>12} {'密采样t':>9}")
    chain_min = 1e9
    chain_min_seg = -1
    for i, (t0, p0x, p0y, t1, v, ux, uy) in enumerate(segs):
        # 认证 dmin (用认证模块重算)
        res = S.certify_segment((p0x, p0y), ux, uy, v, t0, t1,
                                xs[radii <= 470], ys[radii <= 470],
                                radii[radii <= 470], ms[radii <= 470],
                                ns[radii <= 470])
        dm, bt, disk, qr = dense_min_seg(t0, p0x, p0y, t1, v, ux, uy,
                                         xs, ys, radii, ms, ns)
        if dm < chain_min:
            chain_min = dm
            chain_min_seg = i
        diff = res['dmin'] - dm
        flag = '' if abs(diff) < 2e-4 else '  <-- 检查'
        print(f"{i:>3} {res['dmin']:>11.6f} {dm:>11.6f} {diff:>10.2e} "
              f"{'('+str(disk[0])+','+str(disk[1])+')':>12} {bt:>9.6f}{flag}")
    print(f"链条有限段最小净距 = {chain_min:.6f} @ 段{chain_min_seg} (密采样)")
    print()

    # audit_sim 有限段 min_clear (排除终局射线)
    print("audit_sim 口径: 用其 lattice_points 密采样有限段 (不含射线)")
    disks = audit.lattice_points(490.0)
    h = math.radians(heading)
    v = 10.0; p = [0.0, 0.0]; t = 0.0
    amin = 1e9
    for (kind, tt, a) in sorted(events, key=lambda e: e[1]):
        if tt > t + 1e-9:
            n = 2000
            ts = t + (tt - t) * (np.arange(n, dtype=float) / n)
            ux, uy = math.cos(h), math.sin(h)
            for i in range(n):
                th = W * ts[i]
                c, s = math.cos(th), math.sin(th)
                rot = np.array([[c, -s], [s, c]])
                cd = disks @ rot.T
                pt = np.array([p[0] + v * ux * (ts[i] - t),
                               p[1] + v * uy * (ts[i] - t)])
                m = float(np.hypot(pt[0] - cd[:, 0], pt[1] - cd[:, 1]).min())
                if m < amin:
                    amin = m
            p = [p[0] + v * ux * (tt - t), p[1] + v * uy * (tt - t)]
            t = tt
        if kind == "spd":
            v *= a
        else:
            h += math.radians(a)
    print(f"audit_sim 有限段最小净距 = {amin:.6f} (应 >= 9, 与射线无关)")
    print()

    # 终局首撞三方对照
    t_end, px, py, v_end, ux, uy = final
    cards = []
    for (kind, tt, a) in sorted(events, key=lambda e: e[1]):
        cards.append((tt, "acc" if (kind == "spd" and a > 1) else
                      ("dec" if kind == "spd" else "turn"),
                      None if kind == "spd" else a))
    # 重建标准 cards (audit 格式)
    cards = []
    for (kind, tt, a) in sorted(events, key=lambda e: e[1]):
        if kind == "spd":
            cards.append((tt, "acc" if a > 1 else "dec"))
        else:
            cards.append((tt, "turn", a))
    tc0, pc0, score0, mc0 = audit.simulate(heading, cards)
    if tc0 is not None:
        t_ref = audit.bisect_collision(heading, cards, 470.0,
                                       max(0.0, tc0 - 1e-3), tc0)
        # 用 cxk 复算该时刻半径
        vv = 10.0; hh = math.radians(heading); pp = (0.0, 0.0); tt = 0.0
        for (kind, a_time, a) in sorted(events, key=lambda e: e[1]):
            if a_time >= t_ref - 1e-12:
                break
            if a_time > tt + 1e-12:
                pp = (pp[0] + vv * math.cos(hh) * (a_time - tt),
                      pp[1] + vv * math.sin(hh) * (a_time - tt))
                tt = a_time
            if kind == "spd":
                vv *= a
            else:
                hh += math.radians(a)
        pp = (pp[0] + vv * math.cos(hh) * (t_ref - tt),
              pp[1] + vv * math.sin(hh) * (t_ref - tt))
        r_ref = math.hypot(*pp)
        print(f"终局首撞半径三方对照 (纪录):")
        print(f"  cxk.simulate      = 447.8980 (基准)")
        print(f"  audit.bisect 细   = t={t_ref:.6f} r={r_ref:.4f}")
        print(f"  audit.simulate 粗 = {score0:.4f} (2e-4 采样, 略高)")
        print(f"  认证区间          = [447.8890, 447.9046]")
    print()


if __name__ == "__main__":
    import numpy as np
    main()
