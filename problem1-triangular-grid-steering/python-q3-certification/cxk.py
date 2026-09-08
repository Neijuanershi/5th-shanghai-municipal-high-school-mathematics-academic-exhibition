# -*- coding: utf-8 -*-
"""
cxk.py — 第三小问提交格式校验与模拟器 (赛委会格式).

用法:
    python cxk.py <提交文件.txt>

提交格式 (共 102 行):
    第 1 行: 数字 6 (格式版本)
    第 2 行: 出发方向角度 (度)
    第 3..102 行: 每行一次道具使用 (共 100 张卡):
        "+ (time)"          加速卡 (速度 ×1.25)
        "- (time)"          减速卡 (速度 ×0.8)
        "R (time) (angle)"  转向卡 (航向旋转 angle 度, 正=逆时针, |angle|<=5)

物理模型 (第三问条件):
    机器人半径 1, 障碍物半径 8 (有效净距 9 m, 相切不撞);
    初始速度 10 m/s; 100 张卡任意组合, 即时生效, 可叠加;
    全部障碍物绕机器人出发点以周期 60 s 刚性旋转 (共转系变换 R(-ωt));
    目标 = 首撞之前达到的最大距离 sup_t |p(t)|.
    注: 旋转方向因格点镜像对称不影响最远距离的数值, 但影响同一份
        提交是否碰撞——口径已按赛题"绕起点旋转"实现.

碰撞检测:
    旋转框架 + 最近格点 (基坐标取整), 自适应步长;
    慢速端 (v <= 0.3 m/s): 机器人在 ±9 m 窗口内相位扫过整圈,
        用闭式解: 首撞半径 = 最近环半径 20 - 9 = 11.0 m, 避免步进卡死;
    快速端: 步长控制净距分辨 ~0.01 m, 候选以"中点净距 < 9+0.01"触发
        二分精化, 最终以精化后的净距 < 9 判定 (相切=安全).
"""
import sys
import math

W = 2.0 * math.pi / 60.0
V0 = 10.0
RCLR = 9.0                 # 8 + 1
SQ3 = math.sqrt(3.0)
PREC = 1e-4                # 格式精度
R_CAP_BASE = 2.0e4         # 终局检查半径上限基数
EPS = 1e-9
STEP = 0.01                # 净距分辨 (m)
V_SLOW = 0.3               # 慢速闭式解阈值 (m/s)


def read_plan(path):
    with open(path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    if len(lines) < 3:
        raise ValueError("文件行数不足")
    ver = lines[0].lstrip('\ufeff')
    heading = float(lines[1])
    events = []
    for ln in lines[2:]:
        toks = ln.split()
        if toks[0] == "+":
            events.append(("spd", float(toks[1]), 1.25))
        elif toks[0] == "-":
            events.append(("spd", float(toks[1]), 0.8))
        elif toks[0] == "R":
            events.append(("turn", float(toks[1]), float(toks[2])))
        else:
            raise ValueError(f"无法解析的行: {ln!r}")
    return ver, heading, events


def validate(ver, heading, events):
    errs = []
    if ver.strip() != "6":
        errs.append(f"首行应为 6, 实际为 {ver!r}")
    if len(events) != 100:
        errs.append(f"道具行应为 100 行, 实际 {len(events)}")
    for i, (k, t, a) in enumerate(events):
        if t < -PREC:
            errs.append(f"第 {i+3} 行: 时间为负 ({t})")
        if k == "turn" and abs(a) > 5.0 + 1e-6:
            errs.append(f"第 {i+3} 行: 转向角 {a} 超过 5 度")
    return errs


def _decimals(tok):
    return len(tok.split('.')[1]) if '.' in tok else 0


def check_precision(path, events):
    """格式要求 (time)/(angle) 至少精确到 0.0001 — 软警告."""
    warns = []
    with open(path, encoding="utf-8") as f:
        raw = f.readlines()
    body = [ln.split() for ln in raw if ln.strip()][2:]
    for i, toks in enumerate(body):
        if not toks:
            continue
        for tok in toks[1:]:
            if _decimals(tok) < 4:
                warns.append(f"第 {i+3} 行: {tok!r} 精度不足 0.0001")
                break
    return warns


# ---------------- 旋转框架最近格点 ----------------

def nearest_lattice_pts(xr, yr):
    """旋转框架点 (xr,yr) 附近最近的若干格点 -> (d2, x, y)."""
    nf = yr / (10.0 * SQ3)
    mf = (xr - 10.0 * nf) / 20.0
    out = []
    for m in range(int(math.floor(mf)) - 1, int(math.floor(mf)) + 3):
        for n in range(int(math.floor(nf)) - 1, int(math.floor(nf)) + 3):
            if m == 0 and n == 0:
                continue   # 原点不是障碍物
            x = 20.0 * m + 10.0 * n
            y = 10.0 * SQ3 * n
            d2 = (x - xr) ** 2 + (y - yr) ** 2
            out.append((d2, x, y))
    out.sort()
    return out


def min_dist_rot(px, py, t):
    """t 时刻机器人到静态格点的最近距离 (旋转框架)."""
    ct, st = math.cos(W * t), math.sin(W * t)
    xr = ct * px + st * py
    yr = -st * px + ct * py
    d2, _, _ = nearest_lattice_pts(xr, yr)[0]
    return math.sqrt(d2)


# ---------------- 段碰撞 ----------------

def _refine_hit(p0, ux, uy, v, t0, a, b):
    """在 [a,b] 内二分首达净距 9 的时刻; 若全段 >=9 返回 None."""
    lo, hi = a, b
    for _ in range(60):
        m1 = lo + (hi - lo) / 3.0
        m2 = hi - (hi - lo) / 3.0
        d1 = min_dist_rot(p0[0] + v * ux * (m1 - t0),
                          p0[1] + v * uy * (m1 - t0), m1)
        d2 = min_dist_rot(p0[0] + v * ux * (m2 - t0),
                          p0[1] + v * uy * (m2 - t0), m2)
        if d1 < d2:
            hi = m2
        else:
            lo = m1
    tm = 0.5 * (lo + hi)
    dm = min_dist_rot(p0[0] + v * ux * (tm - t0),
                      p0[1] + v * uy * (tm - t0), tm)
    if dm >= RCLR:
        return None
    lo, hi = a, b
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        xm = p0[0] + v * ux * (mid - t0)
        ym = p0[1] + v * uy * (mid - t0)
        if min_dist_rot(xm, ym, mid) < RCLR:
            hi = mid
        else:
            lo = mid
    tc = 0.5 * (lo + hi)
    pc = (p0[0] + v * ux * (tc - t0), p0[1] + v * uy * (tc - t0))
    return tc, pc


def seg_collision(p0, ux, uy, v, t0, t1):
    """直线段 [t0,t1] 的首撞. 返回 (t_coll, p_coll) 或 None."""
    if t1 <= t0:
        return None
    r0 = math.hypot(*p0)
    dur = t1 - t0
    # 慢速闭式解: 段长超过一个周期时相位扫过整圈, 首撞 = 半径首达 11
    if v <= V_SLOW and dur >= 60.0:
        bcoef = 2.0 * (p0[0] * ux + p0[1] * uy) * v
        target = 11.0 * 11.0
        disc = bcoef * bcoef - 4.0 * v * v * (r0 * r0 - target)
        if disc >= 0:
            tp = (-bcoef + math.sqrt(disc)) / (2.0 * v * v)
            if 0.0 < tp <= dur:
                tc = t0 + tp
                pc = (p0[0] + v * ux * tp, p0[1] + v * uy * tp)
                return tc, pc
        return None
    # 时间步进: 每步净距分辨 STEP
    t = t0
    while t < t1:
        px = p0[0] + v * ux * (t - t0)
        py = p0[1] + v * uy * (t - t0)
        r = math.hypot(px, py)
        dt = STEP / max(v + W * r, 1e-9)
        t2 = min(t + dt, t1)
        tm = 0.5 * (t + t2)
        pxm = p0[0] + v * ux * (tm - t0)
        pym = p0[1] + v * uy * (tm - t0)
        d = min_dist_rot(pxm, pym, tm)
        if d < RCLR + STEP:          # 余量覆盖步长分辨损失
            hit = _refine_hit(p0, ux, uy, v, t0, t, t2)
            if hit:
                return hit
        t = t2
    return None


def ray_collision(p0, ux, uy, v, t0):
    """终局半直线 [t0, +inf) 的首撞. 返回 (t, p) 或 None."""
    dot = p0[0] * ux + p0[1] * uy
    r0 = math.hypot(*p0)
    if dot < -EPS:
        t_perp = -dot / v
        p_perp = (p0[0] + v * ux * t_perp, p0[1] + v * uy * t_perp)
        hit = seg_collision(p0, ux, uy, v, t0, t0 + t_perp)
        if hit:
            return hit
        return ray_collision(p_perp, ux, uy, v, t0 + t_perp)
    # 慢速闭式解: 相位在 ±9 m 窗口内扫过整圈 -> 半径 11 处必撞
    if v <= V_SLOW:
        if r0 >= 11.0 - EPS:
            return t0, (p0[0], p0[1])
        tp = (11.0 - r0) / v
        tc = t0 + tp
        pc = (p0[0] + v * ux * tp, p0[1] + v * uy * tp)
        return tc, pc
    r_cap = R_CAP_BASE + 60.0 * v + 100.0
    r = r0
    while r < r_cap:
        dr = STEP / (1.0 + W * r / v)
        r2 = min(r + dr, r_cap)
        rm = 0.5 * (r + r2)
        tm = t0 + (rm - r0) / v
        pxm = p0[0] + v * ux * (tm - t0)
        pym = p0[1] + v * uy * (tm - t0)
        d = min_dist_rot(pxm, pym, tm)
        if d < RCLR + STEP:
            ta = t0 + (r - r0) / v
            tb = t0 + (r2 - r0) / v
            hit = _refine_hit(p0, ux, uy, v, t0, ta, tb)
            if hit:
                return hit
        r = r2
    return None


# ---------------- 主模拟 ----------------

def simulate(heading, events):
    events = sorted(events, key=lambda e: e[1])     # 按时间排序
    v = V0
    h = math.radians(heading)
    p = (0.0, 0.0)
    t = 0.0
    r_max = 0.0
    for (kind, tt, a) in events:
        if tt > t:
            hit = seg_collision(p, math.cos(h), math.sin(h), v, t, tt)
            if hit:
                tc, pc = hit
                return dict(collide=True, t=tc, p=pc,
                            r=max(r_max, math.hypot(*pc)))
            p = (p[0] + v * math.cos(h) * (tt - t),
                 p[1] + v * math.sin(h) * (tt - t))
            r_max = max(r_max, math.hypot(*p))
        t = tt
        if kind == "spd":
            v *= a
        else:
            h += math.radians(a)
    hit = ray_collision(p, math.cos(h), math.sin(h), v, t)
    if hit:
        tc, pc = hit
        return dict(collide=True, t=tc, p=pc, r=max(r_max, math.hypot(*pc)))
    # 未检测到碰撞: 判分值按检查上限计 (不低估)
    r_cap = R_CAP_BASE + 60.0 * v + 100.0
    return dict(collide=False, t=t, p=p, r=max(r_max, r_cap), r_cap=r_cap)


def main():
    if len(sys.argv) < 2:
        print("用法: python cxk.py <提交文件.txt>")
        return 1
    path = sys.argv[1]
    try:
        ver, heading, events = read_plan(path)
    except Exception as e:
        print(f"[解析失败] {e}")
        return 1
    errs = validate(ver, heading, events)
    warns = check_precision(path, events)
    n_spd = sum(1 for e in events if e[0] == "spd" and e[2] > 1)
    n_slow = sum(1 for e in events if e[0] == "spd" and e[2] < 1)
    n_turn = sum(1 for e in events if e[0] == "turn")
    print("=== cxk 校验 ===")
    print(f"文件: {path}")
    print(f"首行版本: {ver.strip()} {'OK' if ver.strip() == '6' else 'FAIL'}")
    print(f"出发角: {heading:.4f} deg")
    print(f"道具: 加速 {n_spd} + 减速 {n_slow} + 转向 {n_turn} = "
          f"{len(events)} {'OK' if len(events) == 100 else 'FAIL'}")
    if errs:
        print("校验问题:")
        for e in errs:
            print("  -", e)
        print("校验失败, 不进行模拟 (退出码 2).")
        return 2
    print("校验: 全部通过")
    for w in warns:
        print("  [精度警告]", w)
    res = simulate(heading, events)
    print("=== 模拟 ===")
    if res["collide"]:
        print(f"首撞: t = {res['t']:.6f} s, r = {res['r']:.4f} m")
        print(f"碰撞点: ({res['p'][0]:.4f}, {res['p'][1]:.4f})")
    else:
        print(f"检查范围内未检测到碰撞 (r 上限 {res['r_cap']:.0f} m), "
              f"判分值按上限计")
    print(f"最远距离 (判分值) = {res['r']:.4f} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
