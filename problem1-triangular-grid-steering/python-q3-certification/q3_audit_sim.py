# -*- coding: utf-8 -*-
"""q3_audit_sim.py — 审核用干净房间模拟器(独立于 cxk.py / q3_sim.py 实现)

直接按题面规则实现:
- 正三角网格 c(m,n) = (20m+10n, 10*sqrt(3)*n),原点无盘;
- 所有盘绕原点逆时针旋转,omega = 2*pi/60;
- 机器人原点出发,速度 10,初始航向自由;
- 卡: '+ t' 提速 x1.25, '- t' 减速 x0.8, 'R t a' 转向 a 度(瞬时,|a|<=5);
- 相切不算撞: 判定为与任意盘心距离 < 9 即撞(净距 9 = 1+8);
- 判分 = 首撞前的 sup |p(t)|。
"""
import math
import sys
import numpy as np

SQ3 = math.sqrt(3.0)
OMEGA = 2.0 * math.pi / 60.0          # 旋转角速度
EFF = 9.0                              # 有效净距(半径1+8)


def lattice_points(max_norm):
    """|c(m,n)| <= max_norm 的全部格点(原点除外)。"""
    pts = []
    k = 1
    while 20.0 * k <= max_norm:
        for m in range(-k, k + 1):
            for n in range(-k, k + 1):
                if max(abs(m), abs(n), abs(m + n)) == k:
                    x = 20.0 * m + 10.0 * n
                    y = 10.0 * SQ3 * n
                    if x * x + y * y <= max_norm * max_norm:
                        pts.append((x, y))
        k += 1
    return np.array(pts, dtype=float)


def parse(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    ver = int(lines[0].split()[0])
    assert ver == 6, f"bad version {ver}"
    h0 = float(lines[1].split()[0])
    cards = []
    for ln in lines[2:]:
        parts = ln.split()
        t = float(parts[1])
        if parts[0] == "+":
            cards.append((t, "acc"))
        elif parts[0] == "-":
            cards.append((t, "dec"))
        else:
            cards.append((t, "turn", float(parts[2])))
    cards.sort(key=lambda c: c[0])
    return h0, cards


def simulate(h0_deg, cards, R_max=470.0, dt_scan=2e-4):
    """返回 (t_coll, p_coll, score, min_clear)。无碰撞则 t_coll=inf。"""
    disks = lattice_points(R_max + 20.0)
    h = math.radians(h0_deg)
    v = 10.0
    p = np.array([0.0, 0.0])
    t_cur = 0.0
    segs = []          # (t0, t1, p0, h, v)  直飞段
    for c in cards:
        if c[0] < t_cur - 1e-9:
            continue
        if c[0] > t_cur + 1e-9:
            segs.append((t_cur, c[0], p.copy(), h, v))
            p = p + v * (c[0] - t_cur) * np.array([math.cos(h), math.sin(h)])
            t_cur = c[0]
        if c[1] == "acc":
            v *= 1.25
        elif c[1] == "dec":
            v *= 0.8
        else:
            h += math.radians(c[2])
    # 末段:直飞至撞或超出半径
    segs.append((t_cur, t_cur + 60.0, p.copy(), h, v))

    # 全局粗扫
    t_coll = None
    min_clear = float("inf")
    p_at_coll = None
    score = 0.0
    for (t0, t1, p0, hh, vv) in segs:
        n = max(2, int(math.ceil((t1 - t0) / dt_scan)))
        ts = np.linspace(t0, t1, n, endpoint=False)
        d = np.array([math.cos(hh), math.sin(hh)])
        pts = p0[None, :] + vv * (ts[:, None] - t0) * d[None, :]
        for i in range(n):
            th = OMEGA * ts[i]
            c, s = math.cos(th), math.sin(th)
            rot = np.array([[c, -s], [s, c]])
            cd = disks @ rot.T
            dist = np.hypot(pts[i, 0] - cd[:, 0], pts[i, 1] - cd[:, 1])
            mn = dist.min()
            if mn < min_clear:
                min_clear = mn
            r = math.hypot(pts[i, 0], pts[i, 1])
            if r > score:
                score = r
            if mn < EFF:
                t_coll = ts[i]
                p_at_coll = pts[i].copy()
                break
        if t_coll is not None:
            break
    return t_coll, p_at_coll, score, min_clear


def bisect_collision(h0_deg, cards, R_max, t_lo, t_hi, iters=40):
    """在 [t_lo, t_hi] 内二分求首撞时刻(6 位小数)。t_hi 处已知碰撞。"""
    disks = lattice_points(R_max + 20.0)
    h = math.radians(h0_deg)
    v = 10.0
    p = np.array([0.0, 0.0])
    t_cur = 0.0

    def collides_by(t_end):
        """判断 [0, t_end] 是否已撞(密采样 1000 点/段)。"""
        hh = math.radians(h0_deg)
        vv = 10.0
        pp = np.array([0.0, 0.0])
        tt = 0.0
        for c in cards:
            if c[0] >= t_end - 1e-12:
                break
            if c[0] > tt + 1e-12:
                if _seg_collide(disks, tt, c[0], pp, hh, vv):
                    return True
                pp = pp + vv * (c[0] - tt) * np.array([math.cos(hh), math.sin(hh)])
                tt = c[0]
            if c[1] == "acc":
                vv *= 1.25
            elif c[1] == "dec":
                vv *= 0.8
            else:
                hh += math.radians(c[2])
        return _seg_collide(disks, tt, t_end, pp, hh, vv)

    def _seg_collide(disks, a, b, p0, hh, vv):
        n = 400
        ts = np.linspace(a, b, n, endpoint=False)
        d = np.array([math.cos(hh), math.sin(hh)])
        pts = p0[None, :] + vv * (ts[:, None] - a) * d[None, :]
        for i in range(n):
            th = OMEGA * ts[i]
            c, s = math.cos(th), math.sin(th)
            rot = np.array([[c, -s], [s, c]])
            cd = disks @ rot.T
            dist = np.hypot(pts[i, 0] - cd[:, 0], pts[i, 1] - cd[:, 1])
            if dist.min() < EFF:
                return True
        return False

    lo, hi = t_lo, t_hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if collides_by(mid):
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def main():
    path = sys.argv[1]
    h0, cards = parse(path)
    t_coll, p_at_coll, score, min_clear = simulate(h0, cards)
    print(f"heading0 = {h0} deg")
    print(f"n_cards  = {len(cards)}")
    if t_coll is None:
        print("无碰撞(仿真窗口内)")
        print(f"score = {score:.6f}, min_clear = {min_clear:.6f}")
        return
    t_fine = bisect_collision(h0, cards, 470.0, max(0.0, t_coll - 1e-3), t_coll)
    print(f"首撞 t  = {t_fine:.6f} s (粗扫 {t_coll:.6f})")
    print(f"碰撞点 = ({p_at_coll[0]:.4f}, {p_at_coll[1]:.4f}), r = {math.hypot(*p_at_coll):.6f}")
    print(f"score  = {score:.6f}")
    print(f"全程最小净距 = {min_clear:.6f} (>=9 通过,相切=9 允许)")


if __name__ == "__main__":
    main()
