# -*- coding: utf-8 -*-
"""
q3_certp1_seg.py — P1 原语一: 认证段净距 cert_seg_min (单盘, 双精度数值认证).

问题模型 (与 cxk.py / q3_audit_sim.py 一致, 惯性系表述):
  机器人直线段: p(t) = p0 + v*u*(t - t0),  t ∈ [t0, t1] (t 为绝对时刻)
  单盘盘心:     q(t) = R(w t) q0,  R(θ)=[[cosθ,-sinθ],[sinθ,cosθ]] (逆时针)
  净距:         d_q(t) = |p(t) - q(t)|; 相切 d=9 安全, 仅 d<9 判撞.

sound 下界 (利普希茨):
  |d(d_q)/dt| ≤ v + w*|q0| =: L
  ⟹ min_{[t0,t1]} d_q ≥ d_q(t_mid) - L*(t1-t0)/2     (下界)
  ⟹ max_{[t0,t1]} d_q ≤ d_q(t_mid) + L*(t1-t0)/2     (上界)

算法 (左优先递归二分, 迭代栈):
  叶子区间 [a,b]:
    lb = d_mid - half ≥ 9  → safe (该子区间全程 ≥9)
    ub = d_mid + half < 9  → unsafe (该子区间全程 <9, 必有撞)
    否则 (band 跨 9)       → 继续二分; 若区间空间直径 v*(b-a) < MIN_SPATIAL 仍跨 9 → indet (切点级)
  unsafe 定位到空间直径 < MIN_SPATIAL=1e-4 m 即返回最早的 unsafe 叶子.
  全部叶子 safe → safe; 存在 indet 且无 unsafe → indet (保守: 不判 safe).

这是数值认证 (math 双精度), 不是形式化证明: 浮点误差未显式跟踪,
但每个判定 (safe/unsafe) 都用严格利普希茨不等式, 双精度误差 ≪ 判定余量.
"""
import math

W = 2.0 * math.pi / 60.0      # 旋转角速度 rad/s
RCLR = 9.0                    # 有效净距 = 盘半径 8 + 机器人半径 1
SQ3 = math.sqrt(3.0)
MIN_SPATIAL = 1e-4            # unsafe 定位的区间空间直径 (m) = v*(t1-t0)
MAX_DEPTH = 80                # 防御性深度上限


def rot(qx, qy, th):
    """逆时针旋转 R(th)·(qx,qy)."""
    c = math.cos(th)
    s = math.sin(th)
    return c * qx - s * qy, s * qx + c * qy


def dist_pq(px, py, q0, t):
    """|p - R(w t) q0|."""
    qx, qy = rot(q0[0], q0[1], W * t)
    return math.hypot(px - qx, py - qy)


def lattice_points(max_norm):
    """静态格点 c(m,n)=(20m+10n, 10√3·n), |c|<=max_norm, 原点除外."""
    pts = []
    nmax = int(max_norm / (10.0 * SQ3)) + 2
    for n in range(-nmax, nmax + 1):
        y = 10.0 * SQ3 * n
        mmax = int((max_norm + abs(10.0 * n)) / 20.0) + 2
        for m in range(-mmax, mmax + 1):
            if m == 0 and n == 0:
                continue
            x = 20.0 * m + 10.0 * n
            if x * x + y * y <= max_norm * max_norm:
                pts.append((x, y))
    return pts


def disks_in_ring(all_disks, all_norms, r_lo, r_hi):
    """返回 |q| ∈ [r_lo, r_hi] 的格点 (sound: 三角形不等式 | |p|-|q| | ≤ d).
    段上 |p|∈[rmin,rmax], 能撞 (d<9) 的盘必满足 rmin-9 < |q| < rmax+9."""
    return [q for q, rq in zip(all_disks, all_norms) if r_lo <= rq <= r_hi]


def build_disk_index(max_norm):
    """预计算格点与半径, 供按环过滤."""
    disks = lattice_points(max_norm)
    norms = [math.hypot(q[0], q[1]) for q in disks]
    return disks, norms


def cert_seg_min(p0, v, u, t0, t1, q0):
    """认证段净距原语 (单盘 q0).

    参数
    ----
    p0 : (px,py)  段起点 (绝对时刻 t0 处机器人位置)
    v  : float    段内速率 (m/s, 恒定)
    u  : (ux,uy)  单位航向
    t0, t1 : float  段绝对起止时刻 (t1 > t0)
    q0 : (qx,qy)  静态格点坐标 (盘心, 绕原点旋转)

    返回
    ----
    dict(status=..., ...)
      'safe'   : 认证 min d ≥ 9 (该盘全程无撞)
      'unsafe' : 认证存在子区间 [t_lo,t_hi] 全程 d<9 (该盘必撞), 且空间直径 < MIN_SPATIAL
      'indet'  : band 跨 9 且到最小直径仍无法判定 (切点级, 保守不判 safe)
    """
    if t1 <= t0:
        return dict(status='safe', reason='empty', L=0.0, neval=0)

    qn = math.hypot(q0[0], q0[1])
    L = v + W * qn                       # |d'/dt| 上界
    min_dt = MIN_SPATIAL / max(v, 1e-12)  # 空间直径 v*dt < 1e-4 m
    ux, uy = u[0], u[1]
    px0, py0 = p0[0], p0[1]

    def ev(a, b):
        tm = 0.5 * (a + b)
        px = px0 + v * ux * (tm - t0)
        py = py0 + v * uy * (tm - t0)
        dm = dist_pq(px, py, q0, tm)
        half = L * (b - a) * 0.5
        return tm, dm, half

    stack = [(t0, t1, 0)]     # (a, b, depth); 左优先: 先 push 右再 push 左
    indet = None
    neval = 0
    while stack:
        a, b, depth = stack.pop()
        tm, dm, half = ev(a, b)
        neval += 1
        lb = dm - half
        ub = dm + half
        if lb >= RCLR:
            continue                       # safe 叶子
        if ub < RCLR:
            if (b - a) <= min_dt * (1.0 + 1e-9):
                return dict(status='unsafe', t_lo=a, t_hi=b, dmid=dm, half=half,
                            L=L, ub=ub, depth=depth, neval=neval)
            if depth >= MAX_DEPTH:
                return dict(status='indet', t_lo=a, t_hi=b, dmid=dm, half=half,
                            L=L, depth=depth, neval=neval, reason='depth')
            stack.append((tm, b, depth + 1))
            stack.append((a, tm, depth + 1))
        else:
            if (b - a) <= min_dt * (1.0 + 1e-9):
                if indet is None:
                    indet = (a, b, dm)
                continue                   # 切点级叶子, 记录后继续向右找 unsafe
            if depth >= MAX_DEPTH:
                if indet is None:
                    indet = (a, b, dm)
                continue
            stack.append((tm, b, depth + 1))
            stack.append((a, tm, depth + 1))

    if indet is not None:
        return dict(status='indet', t_lo=indet[0], t_hi=indet[1], dmid=indet[2],
                    L=L, neval=neval)
    return dict(status='safe', L=L, neval=neval)


if __name__ == "__main__":
    # 极简自检: 一条远离所有盘的段应 safe; 一条穿盘的段应 unsafe.
    u = (1.0, 0.0)
    print(cert_seg_min((0.0, 30.0), 10.0, u, 0.0, 0.1, (0.0, 0.0)))
    print(cert_seg_min((0.0, 9.0), 10.0, u, 0.0, 0.001, (0.0, 0.0)))
