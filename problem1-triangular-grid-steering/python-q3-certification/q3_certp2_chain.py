# -*- coding: utf-8 -*-
"""
q3_certp2_chain.py — 子代理 J: 固定链方案全链逐段 Lipschitz 认证 (P2).

对 cxk 格式 102 行方案:
  1. 解析 (cxk.read_plan) 并展开为匀速直线段序列 + 终局射线 (自己的展开器);
  2. 对每一段用 q3_certp2_seg.certify_segment 对附近盘 (|q|<=470) 认证净距 >= 9;
  3. 终局 free-run 用 q3_certp2_seg.certify_ray 认证首撞半径区间;
  4. 与 cxk.simulate / q3_audit_sim.simulate 三方并列对照 (纪录 + 山脊两方案).

山脊方案 (内存构建, 不写文件): 与纪录相同, 仅改两行:
  - 倒数第 2 张转卡 R 3.7924 4.8800 -> R 3.7924 4.8350  (Δ1 = 5.0+4.835 = 9.835 deg)
  - 慢卡 - 3.8873 -> - 3.8874  (L1 = 116.4153*0.095 = 11.06 m)
"""
import math
import time
import cxk
import q3_audit_sim as audit
import q3_certp2_seg as S

SQ3 = math.sqrt(3.0)


# ---------------- 方案展开 (自己的版本, 等价 cxk.simulate 物理) ----------------

def build_segments(heading, events):
    """返回 (segs, final). segs: (t0, p0x, p0y, t1, v, ux, uy). final=(t,p,v,ux,uy)."""
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
    ux, uy = math.cos(h), math.sin(h)
    return segs, (t, p[0], p[1], v, ux, uy)


# ---------------- 全链认证 ----------------

def certify_plan(heading, events, xs, ys, radii, ms, ns, seg_mask):
    """认证方案. 返回 dict: 逐段表, 射线区间, 最紧段, 全链判定."""
    segs, final = build_segments(heading, events)
    sx = xs[seg_mask]; sy = ys[seg_mask]; sr = radii[seg_mask]
    sm = ms[seg_mask]; sn = ns[seg_mask]

    seg_reports = []
    any_collision = False
    worst_cert = float('inf')
    worst_i = -1
    for i, (t0, p0x, p0y, t1, v, ux, uy) in enumerate(segs):
        res = S.certify_segment((p0x, p0y), ux, uy, v, t0, t1,
                                sx, sy, sr, sm, sn)
        seg_reports.append(res)
        if res['status'] == 'collision':
            any_collision = True
        if res['cert'] < worst_cert:
            worst_cert = res['cert']
            worst_i = i

    t_end, px, py, v_end, ux, uy = final
    ray = S.certify_ray((px, py), ux, uy, v_end, t_end,
                        xs, ys, radii, ms, ns)

    sim = cxk.simulate(heading, events)
    # audit_sim 用 cards 列表
    cards = []
    for (kind, tt, a) in sorted(events, key=lambda e: e[1]):
        if kind == "spd":
            cards.append((tt, "acc" if a > 1 else "dec"))
        else:
            cards.append((tt, "turn", a))
    tc, pc, ascore, amin = audit.simulate(heading, cards)

    return dict(segs=segs, seg_reports=seg_reports, final=final,
                any_collision=any_collision, worst_cert=worst_cert,
                worst_i=worst_i, ray=ray, sim=sim,
                audit=dict(tc=tc, pc=pc, score=ascore, min_clear=amin))


# ---------------- 输出 ----------------

def fmt_disk(d):
    m, n, r = d
    return f"({m},{n})|q|={r:.1f}"


def print_plan_report(name, r):
    print("=" * 96)
    print(f"方案: {name}   heading={r['sim']['t']*0:+.0f}")
    print("=" * 96)
    print(f"{'段':>3} {'t0':>9} {'t1':>9} {'v':>8} {'safe':>6} {'认证下界':>11} "
          f"{'采样dmin':>11} {'紧盘(m,n)':>12} {'|q|':>8} {'叶数':>6}")
    for i, (seg, res) in enumerate(zip(r['segs'], r['seg_reports'])):
        t0, p0x, p0y, t1, v, ux, uy = seg
        m, n, qr = res['disk']
        st = 'SAFE' if res['status'] == 'safe' else 'COLLIDE'
        print(f"{i:>3} {t0:>9.6f} {t1:>9.6f} {v:>8.2f} {st:>6} "
              f"{res['cert']:>11.6f} {res['dmin']:>11.6f} "
              f"{'('+str(m)+','+str(n)+')':>12} {qr:>8.1f} {res['nleaf']:>6}")
    print("-" * 96)
    print(f"有限段: {'全部 SAFE' if not r['any_collision'] else '!! 有碰撞 !!'}  "
          f"最紧认证下界 = {r['worst_cert']:.6f} m @ 段{r['worst_i']}")
    ray = r['ray']
    if 'error' in ray:
        print(f"终局射线: 异常 {ray}")
    else:
        print(f"终局射线首撞半径区间: [{ray['r_lo']:.4f}, {ray['r_hi']:.4f}] m "
              f"(宽 {ray['width']:.4f} m)")
    sim = r['sim']
    if sim['collide']:
        print(f"cxk.simulate:    r = {sim['r']:.4f} m  t = {sim['t']:.6f} s  "
              f"撞点 ({sim['p'][0]:.4f},{sim['p'][1]:.4f})")
        inb = ray.get('r_lo', -1e9) <= sim['r'] <= ray.get('r_hi', 1e9)
        print(f"   -> cxk 成绩在认证区间内: {'是' if inb else '否'}")
    else:
        print(f"cxk.simulate:    无碰撞 (r_cap={sim.get('r_cap')})")
    au = r['audit']
    print(f"audit_sim:       score = {au['score']:.4f} m  "
          f"t_coll = {au['tc']}  min_clear = {au['min_clear']:.6f}")
    print()


# ---------------- 主流程 ----------------

def build_ridge_events():
    """内存构建山脊方案 (与纪录仅差两行). 返回 (heading, events)."""
    ver, heading, events = cxk.read_plan("q3_campaign_best_saA.txt")
    ev = list(events)
    # 定位倒数两张转卡与慢卡
    assert ev[-1][0] == "spd" and abs(ev[-1][1] - 3.8873) < 1e-6, ev[-1]
    assert ev[-2][0] == "turn" and abs(ev[-2][1] - 3.7924) < 1e-6, ev[-2]
    assert ev[-3][0] == "turn" and abs(ev[-3][1] - 3.7924) < 1e-6, ev[-3]
    ev[-2] = ("turn", 3.7924, 4.8350)   # 第二张终局转卡 4.8800 -> 4.8350
    ev[-1] = ("spd", 3.8874, 0.8)       # 慢卡 3.8873 -> 3.8874
    return heading, ev


def main():
    t_start = time.time()
    xs, ys, radii, ms, ns = S.build_disks(500.0)
    seg_mask = radii <= S.R_DISK
    print(f"圆盘总数 = {len(xs)}, 段认证附近盘(|q|<=470) = {int(seg_mask.sum())}")

    # 纪录方案
    ver, heading, events = cxk.read_plan("q3_campaign_best_saA.txt")
    r_rec = certify_plan(heading, events, xs, ys, radii, ms, ns, seg_mask)
    print_plan_report("纪录 q3_campaign_best_saA.txt (Δ1=9.88°, L1=11.05)", r_rec)

    # 山脊方案
    heading_r, events_r = build_ridge_events()
    r_rid = certify_plan(heading_r, events_r, xs, ys, radii, ms, ns, seg_mask)
    print_plan_report("山脊 (Δ1=9.835°, L1=11.06, slow@3.8874)", r_rid)

    print(f"总耗时 = {time.time() - t_start:.2f} s")
    return r_rec, r_rid


if __name__ == "__main__":
    main()
