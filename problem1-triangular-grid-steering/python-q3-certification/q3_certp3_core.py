# -*- coding: utf-8 -*-
"""q3_certp3_core.py — Q3 终局族(P3-lite)共享核心: 固定链尾回放 + 终局快评分 + 官方格式方案写盘。

终局自由度族(固定链尾 q3_campaign_best_saA.txt 前 99 行):
  自由度 (Δ1, L1, slow):
    Δ1   = 终局转向总量(度), 拆 2 卡 [min(5,Δ1), Δ1-min(5,Δ1)] @ tB=3.7924;
    L1   = 终局转向点到慢卡的直飞距离(m), 通过 t_slow = tB + L1/v 实现;
    slow = 1 放慢卡(×0.8); 0 不放慢卡(用 R t_slow 0.0000 占位, 保持 100 卡, 物理等价无慢卡)。

快评分: 固定链 86 段无碰撞(纪录已证), 只对终局段用 cxk 原生 seg_collision/ray_collision,
  与 cxk.simulate 逐位等价(见 q3_certp3_verify.py 的精确性核验)。
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk

REC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q3_campaign_best_saA.txt")
TB = 3.7924                 # 终局转向时刻(纪录末段 2 转向卡时间)
V0 = 10.0 * 1.25 ** 11      # 116.41532... (链后速度, 11 加速卡)
D2R = math.pi / 180.0


def read_rec_lines():
    with open(REC, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]


def chain_end_state(lines=None):
    """回放固定前缀(前 99 行 = 版本+出发角+11加速+86链转)到 t=TB, 返回
    (p0, h0_rad, t0, v0, r_max_chain)。
    积分公式与 cxk.simulate 逐位一致(不查碰撞, 链段无碰撞已由纪录证实)。
    """
    if lines is None:
        lines = read_rec_lines()
    heading = float(lines[1])
    events = []
    for ln in lines[2:99]:
        toks = ln.split()
        if toks[0] == "+":
            events.append(("spd", float(toks[1]), 1.25))
        elif toks[0] == "-":
            events.append(("spd", float(toks[1]), 0.8))
        else:
            events.append(("turn", float(toks[1]), float(toks[2])))
    events.sort(key=lambda e: e[1])
    v = 10.0
    h = math.radians(heading)
    p = (0.0, 0.0)
    t = 0.0
    r_max = 0.0
    for (kind, tt, a) in events:
        if tt > t:
            p = (p[0] + v * math.cos(h) * (tt - t),
                 p[1] + v * math.sin(h) * (tt - t))
            r_max = max(r_max, math.hypot(*p))
        t = tt
        if kind == "spd":
            v *= a
        else:
            h += math.radians(a)
    # 推进到 tB(末次链转 3.7028 -> 终局转向 3.7924 的直飞段)
    p0 = (p[0] + v * math.cos(h) * (TB - t),
          p[1] + v * math.sin(h) * (TB - t))
    r_max = max(r_max, math.hypot(*p0))
    return p0, h, TB, v, r_max


# 模块级缓存: 链尾出口态
_STATE = None


def state():
    global _STATE
    if _STATE is None:
        _STATE = chain_end_state()
    return _STATE


def t_slow_of(L1):
    """t_slow = TB + L1/V0 (不四舍五入, 连续值)。"""
    return TB + L1 / V0


def t_slow_grid(L1_center, half_n):
    """以 L1_center 为中心, 在官方 0.0001 s 时间网格上取 t_slow 的 2*half_n+1 个可表示值。
    返回 (t_slow 列表, 对应 realized L1 列表)。"""
    tc = round(t_slow_of(L1_center) / 1e-4)  # 中心对应的时间格步
    ts = [(tc + k) * 1e-4 for k in range(-half_n, half_n + 1)]
    l1s = [(tt - TB) * V0 for tt in ts]
    return ts, l1s


def terminal_score(d1, L1, slow, st=None):
    """终局快评分(与 cxk.simulate 对终局段逐位等价)。
    返回分数 r(m)。d1=Δ1(度), L1(m), slow∈{0,1}。st=chain_end_state 输出。
    """
    if st is None:
        st = state()
    p0, h0, t0, v0, r_max_chain = st
    h = h0 + d1 * D2R
    ux, uy = math.cos(h), math.sin(h)
    t1 = t0 + L1 / v0
    hit = cxk.seg_collision(p0, ux, uy, v0, t0, t1)
    if hit:
        return max(r_max_chain, math.hypot(*hit[1]))
    p1 = (p0[0] + v0 * ux * (t1 - t0), p0[1] + v0 * uy * (t1 - t0))
    r_max = max(r_max_chain, math.hypot(*p1))
    v = v0 * (0.8 if slow else 1.0)
    hit = cxk.ray_collision(p1, ux, uy, v, t1)
    if hit:
        return max(r_max, math.hypot(*hit[1]))
    r_cap = cxk.R_CAP_BASE + 60.0 * v + 100.0
    return max(r_max, r_cap)


def build_plan(d1, L1, slow, out, lines=None):
    """写官方格式 102 行方案(前 99 行固定 + 2 终局转向卡 + 慢卡/占位卡)。
    Δ1 拆 2 卡 [min(5,Δ1), Δ1-min(5,Δ1)]; slow=1 写 '-' 慢卡, slow=0 写 'R t 0.0000' 占位。
    返回 (out, valid_flag)。valid_flag=False 表示第二转向卡 |angle|>5(Δ1>10, 超出 2 卡族合法域)。
    """
    if lines is None:
        lines = read_rec_lines()
    ts = round(t_slow_of(L1) / 1e-4) * 1e-4  # 官方 0.0001 s 网格
    nl = lines[:99]
    nl.append(f"R {TB:.4f} {min(5.0, d1):.4f}")
    nl.append(f"R {TB:.4f} {d1 - min(5.0, d1):.4f}")
    if slow:
        nl.append(f"- {ts:.4f}")
    else:
        nl.append(f"R {ts:.4f} 0.0000")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(nl) + "\n")
    valid = abs(d1 - min(5.0, d1)) <= 5.0 + 1e-6
    return out, valid


def full_simulate(d1, L1, slow, tmp="_tmp_certp3.txt", lines=None):
    """完整 cxk.simulate(官方格式方案)。用于核验/认证。返回 (score, res, valid)。"""
    out, valid = build_plan(d1, L1, slow, tmp, lines)
    ver, hd, ev = cxk.read_plan(out)
    res = cxk.simulate(hd, ev)
    return res["r"], res, valid
