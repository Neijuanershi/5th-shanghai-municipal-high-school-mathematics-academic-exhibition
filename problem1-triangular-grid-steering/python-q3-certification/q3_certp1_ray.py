# -*- coding: utf-8 -*-
"""
q3_certp1_ray.py — P1 原语二: 认证射线首撞 cert_ray.

终局半直线 p(s)=p0+v*u*s (s≥0 为段内经过时间), 半径 r(s)=|p(s)| 单调增 (向外射线).
对盘集 (|q| ≤ disk_cap) 沿射线分段调用 cert_seg_min:
  - 每段所有盘都 safe → r_safe 推进到该段末端半径;
  - 某段首次出现 unsafe 盘 → r_coll = 该盘 unsafe 叶子 [t_lo,t_hi] 末端半径 (上界);
  - 全部 safe 到 r_cap → (r_cap, inf).

返回认证区间 [r_safe, r_coll]: 真实首撞半径 r* ∈ (r_safe, r_coll],
即 r_safe 是首撞半径的 sound 下界, r_coll 是 sound 上界.
"""
import math
from q3_certp1_seg import (cert_seg_min, disks_in_ring, build_disk_index,
                           W, RCLR)

# 全局盘集: 覆盖终局射线 r_cap=460 所需的最大 |q| = 460 + 9 = 469.
GLOBAL_DISKS, GLOBAL_NORMS = build_disk_index(480.0)


def cert_ray(p0, u, v, t0, r_cap=460.0, disk_cap=470.0, dL=0.1):
    """认证射线首撞半径区间.

    射线按弧长 L 参数化: p(L)=p0+u*L, r(L)=|p(L)| (pdu=p0·u>0 时单调增),
    t(L)=t0+L/v (绝对时刻, 旋转相位用). 沿弧长分段调用 cert_seg_min:
      - 每段所有盘 safe → r_safe 推进到该段末端半径 r(L_b);
      - 某段首现 unsafe 盘 → r_coll = 该盘 unsafe 叶子末端半径 |p(L_hi)|;
      - 全部 safe 到 r_cap → (r_cap, inf).

    参数
    ----
    p0 : (px,py)  射线起点 (绝对时刻 t0 处机器人位置)
    u  : (ux,uy)  单位航向
    v  : float    速率 (m/s, 恒定)
    t0 : float    绝对起始时刻 (旋转相位用绝对时刻)
    r_cap : float 检查半径上限
    disk_cap : float 盘集截断半径 (|q| ≤ disk_cap)
    dL : float    射线分段弧长步长 (m); cert_seg_min 内部自适细分, dL 只影响 r_safe 粒度

    返回
    ----
    dict(r_safe=..., r_coll=..., all_safe=bool, hit=dict|None, neval=..., nseg=...)
    """
    disks_all = [q for q, rq in zip(GLOBAL_DISKS, GLOBAL_NORMS) if rq <= disk_cap]
    norms_all = [math.hypot(q[0], q[1]) for q in disks_all]

    r0 = math.hypot(p0[0], p0[1])
    pdu = p0[0] * u[0] + p0[1] * u[1]
    if pdu < 0.0:
        return dict(r_safe=r0, r_coll=math.inf, error='ray not outward', dot=pdu)

    # 到达半径 r_cap 所需弧长: |p0+u*L|^2 = r_cap^2 → L = -pdu + sqrt(pdu^2 + r_cap^2 - r0^2)
    L_cap = -pdu + math.sqrt(pdu * pdu + r_cap * r_cap - r0 * r0)

    r_safe = r0
    L = 0.0
    neval = 0
    nseg = 0
    hit = None
    while L < L_cap:
        L_b = min(L + dL, L_cap)
        p_a = (p0[0] + u[0] * L, p0[1] + u[1] * L)
        p_b = (p0[0] + u[0] * L_b, p0[1] + u[1] * L_b)
        r_a = math.hypot(*p_a)
        r_b = math.hypot(*p_b)
        t_a = t0 + L / v
        t_b = t0 + L_b / v
        # 只取可能撞的盘: |q| ∈ [r_a-9, r_b+9] (三角形不等式, sound)
        seg_disks = disks_in_ring(disks_all, norms_all, r_a - RCLR, r_b + RCLR)
        status = 'safe'
        worst = None
        for q in seg_disks:
            res = cert_seg_min(p_a, v, u, t_a, t_b, q)
            neval += res.get('neval', 0)
            if res['status'] == 'unsafe':
                status = 'unsafe'
                worst = res
                worst['disk'] = q
                break
            if res['status'] == 'indet' and status == 'safe':
                status = 'indet'
                worst = res
                worst['disk'] = q
        nseg += 1
        if status == 'safe':
            r_safe = r_b
            L = L_b
            continue
        if status == 'unsafe':
            t_hi = worst['t_hi']
            L_hi = v * (t_hi - t0)
            px = p0[0] + u[0] * L_hi
            py = p0[1] + u[1] * L_hi
            r_coll = math.hypot(px, py)
            hit = dict(disk=worst['disk'], t_hi=t_hi, dmid=worst['dmid'],
                       ub=worst.get('ub'), r_coll=r_coll)
            return dict(r_safe=r_safe, r_coll=r_coll, all_safe=False,
                        hit=hit, neval=neval, nseg=nseg, r0=r0)
        # indet: 无法认证 safe, 也无法认证撞 —— 保守返回 (r_safe 停在前段末端)
        return dict(r_safe=r_safe, r_coll=r_b, all_safe=False, indet=True,
                    hit=worst, neval=neval, nseg=nseg, r0=r0)
    return dict(r_safe=r_cap, r_coll=math.inf, all_safe=True,
                hit=None, neval=neval, nseg=nseg, r0=r0)


if __name__ == "__main__":
    # 自检: 从原点沿 +x 外发射线, 最近环盘在 (20,0), 首撞 r* = 20-9 = 11 m.
    u = (1.0, 0.0)
    res = cert_ray((0.0, 0.0), u, 10.0, 0.0, r_cap=30.0)
    print(res)
