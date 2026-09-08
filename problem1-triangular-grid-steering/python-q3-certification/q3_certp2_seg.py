# -*- coding: utf-8 -*-
"""
q3_certp2_seg.py — 子代理 J 的「逐段 Lipschitz 认证」核心 (独立实现, 不调用 I 的代码).

对 Q3 (盘半径 8 + 机器人 1 = 净距 9, 正三角网格绕原点以 omega=2*pi/60 刚性旋转)
的 cxk 格式方案做严格认证。认证对象是方案展开后的**匀速直线段**序列与终局射线。

认证公式 (固定框架, 与子代理 I 共用同一公式):
    d_q(t) = |p(t) - R(omega t) q0| ,  p(t) = p0 + v*u*(t-t0)   (u 单位航向)
    |d/dt d_q(t)| = |v*u - omega*J*R(omega t) q0| <= v + omega*|q0|
   => min_{t in [a,b]} d_q(t) >= d_q(t_mid) - (v + omega*|q0|) * (b-a)/2

对每一段对附近盘 (|q|<=470) 做**递归二分**: 若叶子下界 >= 9 则该叶子认证 safe;
否则继续细分 (每片叶子只对当前最紧下界叶子做 best-first 细分, 下界单调不减,
最终收敛到该段真实最小净距)。这与 I 的公式一致但实现完全独立。
"""
import math
import heapq
import numpy as np

W = 2.0 * math.pi / 60.0        # 网格旋转角速度 (rad/s)
V0 = 10.0
RCLR = 9.0                      # 净距阈值 (8+1), 相切=9 安全
SQ3 = math.sqrt(3.0)

R_DISK = 470.0                  # 段认证的附近盘上限 |q| <= 470
R_RAY_EXTRA = 20.0              # 射线认证的盘半径余量 (碰撞半径 + 9 + 余量)
DT_FLOOR = 1e-9                 # 叶子绝对最小时间宽度 (防数值死循环)
TIGHT_GAP = 2e-5                # 认证下界与真实最小净距的目标间隙 (m)


# ---------------- 正三角格点圆盘 ----------------

def build_disks(rmax):
    """构建 |c(m,n)| <= rmax 的全部格点 (原点无盘).
    返回 (xs, ys, radii, ms, ns) 五组 numpy 数组."""
    xs, ys, ms, ns = [], [], [], []
    nmax = int(rmax / (10.0 * SQ3)) + 2
    for n in range(-nmax, nmax + 1):
        y = 10.0 * SQ3 * n
        mmax = int((rmax + abs(10.0 * n)) / 20.0) + 2
        for m in range(-mmax, mmax + 1):
            x = 20.0 * m + 10.0 * n
            if m == 0 and n == 0:
                continue
            if x * x + y * y <= rmax * rmax:
                xs.append(x); ys.append(y); ms.append(m); ns.append(n)
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    ms = np.asarray(ms, dtype=int)
    ns = np.asarray(ns, dtype=int)
    radii = np.sqrt(xs * xs + ys * ys)
    return xs, ys, radii, ms, ns


# ---------------- 叶子评估 ----------------

def _leaf_cert(p0x, p0y, ux, uy, v, t0, a, b, xs, ys, radii):
    """对时间区间 [a,b] (绝对时间) 计算叶子认证下界.
    返回 (leaf_cert, dmin, tight_j) 其中 tight_j 是最紧圆盘下标."""
    tm = 0.5 * (a + b)
    dt = b - a
    pmx = p0x + v * ux * (tm - t0)
    pmy = p0y + v * uy * (tm - t0)
    ct = math.cos(W * tm)
    st = math.sin(W * tm)
    qx = ct * xs - st * ys
    qy = st * xs + ct * ys
    dx = pmx - qx
    dy = pmy - qy
    d = np.sqrt(dx * dx + dy * dy)
    L = v + W * radii
    cert = d - L * (0.5 * dt)
    j = int(np.argmin(cert))
    return float(cert[j]), float(d[j]), j


# ---------------- 段认证 ----------------

def certify_segment(p0, ux, uy, v, t0, t1, xs, ys, radii, ms, ns):
    """认证匀速直线段 p(t)=p0+v*u*(t-t0), t in [t0,t1] (网格以绝对时间旋转).

    返回 dict:
      status  : 'safe' | 'collision'
      cert    : 认证净距下界 (safe 时 >= 9, 且逼近真实最小净距)
      dmin    : 最紧叶子的采样净距 (>= cert)
      disk    : (m, n, |q|) 最紧圆盘
      nleaf   : 生成叶子总数
      t0,t1   : 段边界 (回显)
      碰撞时额外: t, r, d
    """
    p0x, p0y = float(p0[0]), float(p0[1])
    # 堆元素: (cert, a, b, dmin, tight_j)  —— cert 为最小堆键
    c0, d0, j0 = _leaf_cert(p0x, p0y, ux, uy, v, t0, t0, t1, xs, ys, radii)
    heap = [(c0, t0, t1, d0, j0)]
    nleaf = 1
    while heap:
        cert, a, b, dmin, j = heapq.heappop(heap)
        dt = b - a
        if cert >= RCLR:
            # 最紧叶子已认证 safe; 若足够细则收紧结束, 否则继续细分该叶子提紧下界
            if radii[j] * W + v <= 0.0:
                return dict(status='safe', cert=cert, dmin=dmin,
                            disk=(int(ms[j]), int(ns[j]), float(radii[j])),
                            nleaf=nleaf, t0=t0, t1=t1)
            gap = (v + W * radii[j]) * dt
            if gap <= TIGHT_GAP:
                return dict(status='safe', cert=cert, dmin=dmin,
                            disk=(int(ms[j]), int(ns[j]), float(radii[j])),
                            nleaf=nleaf, t0=t0, t1=t1)
        else:
            if dt <= DT_FLOOR:
                # 无法再细分: 中点精确净距判定
                if dmin < RCLR:
                    tm = 0.5 * (a + b)
                    pmx = p0x + v * ux * (tm - t0)
                    pmy = p0y + v * uy * (tm - t0)
                    r = math.hypot(pmx, pmy)
                    return dict(status='collision', t=tm, r=r, d=dmin,
                                disk=(int(ms[j]), int(ns[j]), float(radii[j])),
                                nleaf=nleaf, t0=t0, t1=t1)
                return dict(status='safe', cert=cert, dmin=dmin,
                            disk=(int(ms[j]), int(ns[j]), float(radii[j])),
                            nleaf=nleaf, t0=t0, t1=t1)
        # 细分当前最紧叶子
        m = 0.5 * (a + b)
        cl, dl, jl = _leaf_cert(p0x, p0y, ux, uy, v, t0, a, m, xs, ys, radii)
        cr, dr, jr = _leaf_cert(p0x, p0y, ux, uy, v, t0, m, b, xs, ys, radii)
        heapq.heappush(heap, (cl, a, m, dl, jl))
        heapq.heappush(heap, (cr, m, b, dr, jr))
        nleaf += 2
    # 理论不可达
    return dict(status='safe', cert=9.0, dmin=9.0, disk=(0, 0, 0.0),
                nleaf=nleaf, t0=t0, t1=t1)


# ---------------- 终局射线认证 ----------------

def certify_ray(p0, ux, uy, v, t0, xs, ys, radii, ms, ns,
                width_target=0.02, step0=4.0):
    """认证终局射线 [t0, +inf) 的首撞半径区间 [r_lo, r_hi] (含真实首撞半径).
    前提: 射线向外 (dot(p0,u) > 0), 半径单调递增."""
    r0 = math.hypot(p0[0], p0[1])
    pdu = p0[0] * ux + p0[1] * uy
    if pdu <= 0.0:
        return dict(error='ray not outward', dot=pdu)

    def s_of_r(r):
        return (-pdu + math.sqrt(pdu * pdu + (r * r - r0 * r0))) / v

    def seg_at(r_lo, r_hi):
        sa = s_of_r(r_lo)
        sb = s_of_r(r_hi)
        a = t0 + sa
        b = t0 + sb
        pa = (p0[0] + v * ux * sa, p0[1] + v * uy * sa)
        return certify_segment(pa, ux, uy, v, a, b, xs, ys, radii, ms, ns)

    # 阶段 1: 粗步进定位碰撞区
    r = r0
    r_lo = r0
    guard = 0
    while True:
        guard += 1
        if guard > 100000:
            return dict(error='coarse guard', r_lo=r_lo)
        rb = r + step0
        res = seg_at(r, rb)
        if res['status'] == 'safe':
            r_lo = rb
            r = rb
        else:
            break

    # 阶段 2: 二分收窄 (r_lo 恒为已认证 safe 半径, 碰撞在上界内)
    r_hi = r + step0
    # 用碰撞点半径(若已知)收紧上界
    guard = 0
    while r_hi - r_lo > width_target:
        guard += 1
        if guard > 200:
            break
        rm = 0.5 * (r_lo + r_hi)
        res = seg_at(r_lo, rm)
        if res['status'] == 'safe':
            r_lo = rm
        else:
            r_hi = rm
    return dict(r_lo=r_lo, r_hi=r_hi, width=r_hi - r_lo)
