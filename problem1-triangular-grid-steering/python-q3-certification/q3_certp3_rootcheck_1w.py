# -*- coding: utf-8 -*-
# q3_certp3_rootcheck_1w.py — root 独立裁决 P3-lite 关键数字 (v2, 防御碰撞段)
# 用 J 的逐盘 Lipschitz 紧认证器 (q3_certp2_seg) 对新候选 447.9725 做刀锋裁决,
# 并核对 K 的悬崖对 / 粗枚举 top-3 / 天真舍入落崖 / 山脊基准。
# 只读既有文件; 新写 q3_certp3_cand_4479725.txt (官方格式候选)。
import time
import cxk
import q3_audit_sim as audit
import q3_certp2_seg as S
import q3_certp2_chain as C

REC = "q3_campaign_best_saA.txt"
CANDFILE = "q3_certp3_cand_4479725.txt"


def candidate(turn2, t_slow):
    ver, heading, events = cxk.read_plan(REC)
    ev = list(events)
    assert ev[-1][0] == "spd" and abs(ev[-1][1] - 3.8873) < 1e-6, ev[-1]
    assert ev[-2][0] == "turn" and abs(ev[-2][1] - 3.7924) < 1e-6, ev[-2]
    assert ev[-3][0] == "turn" and abs(ev[-3][1] - 3.7924) < 1e-6, ev[-3]
    ev[-2] = ("turn", 3.7924, turn2)
    ev[-1] = ("spd", t_slow, 0.8)
    return heading, ev


def my_certify(heading, events, xs, ys, radii, ms, ns, seg_mask):
    """与 q3_certp2_chain.certify_plan 同口径, 但对碰撞段(cert 缺失)做防御处理."""
    segs, final = C.build_segments(heading, events)
    sx = xs[seg_mask]; sy = ys[seg_mask]; sr = radii[seg_mask]
    sm = ms[seg_mask]; sn = ns[seg_mask]
    seg_reports = []
    any_collision = False
    first_coll = None
    worst_cert = float('inf')
    worst_i = -1
    for i, (t0, p0x, p0y, t1, v, ux, uy) in enumerate(segs):
        res = S.certify_segment((p0x, p0y), ux, uy, v, t0, t1,
                                sx, sy, sr, sm, sn)
        seg_reports.append(res)
        if res.get('status') == 'collision':
            any_collision = True
            if first_coll is None:
                first_coll = (i, res)
        if 'cert' in res and res['cert'] < worst_cert:
            worst_cert = res['cert']
            worst_i = i
    t_end, px, py, v_end, ux, uy = final
    ray = S.certify_ray((px, py), ux, uy, v_end, t_end,
                        xs, ys, radii, ms, ns)
    sim = cxk.simulate(heading, events)
    cards = []
    for (kind, tt, a) in sorted(events, key=lambda e: e[1]):
        if kind == "spd":
            cards.append((tt, "acc" if a > 1 else "dec"))
        else:
            cards.append((tt, "turn", a))
    tc, pc, ascore, amin = audit.simulate(heading, cards)
    return dict(segs=segs, seg_reports=seg_reports, final=final,
                any_collision=any_collision, first_coll=first_coll,
                worst_cert=worst_cert, worst_i=worst_i, ray=ray, sim=sim,
                audit=dict(tc=tc, pc=pc, score=ascore, min_clear=amin))


def compact(name, r):
    sim = r['sim']; ray = r['ray']
    print("-" * 90)
    print(f"[{name}]")
    if r['any_collision']:
        i, res = r['first_coll']
        m, n, qr = res['disk']
        print(f"  有限段: !! 有碰撞 !!  首撞段={i}  t={res['t']:.6f}  r={res['r']:.4f}  "
              f"d={res['d']:.6f}  盘({m},{n}) |q|={qr:.1f} 叶数={res['nleaf']}")
    else:
        print(f"  有限段: 全部SAFE  最紧认证下界 = {r['worst_cert']:.6f} @ 段{r['worst_i']}")
        seg = r['segs'][r['worst_i']]; res = r['seg_reports'][r['worst_i']]
        m, n, qr = res['disk']
        print(f"  最紧段: t0={seg[0]:.6f} t1={seg[3]:.6f} cert={res['cert']:.6f} "
              f"dmin={res['dmin']:.6f} 盘({m},{n}) |q|={qr:.1f} 叶数={res['nleaf']}")
    if 'error' not in ray:
        print(f"  射线区间: [{ray['r_lo']:.4f}, {ray['r_hi']:.4f}] 宽 {ray['width']:.4f}")
    else:
        print(f"  射线异常: {ray}")
    if sim['collide']:
        print(f"  cxk: r={sim['r']:.4f}  t={sim['t']:.6f}  撞点({sim['p'][0]:.4f},{sim['p'][1]:.4f})")
    else:
        print(f"  cxk: 无碰撞 (r_cap={sim.get('r_cap')})")
    au = r['audit']
    print(f"  audit: score={au['score']:.4f} t_coll={au['tc']} min_clear={au['min_clear']:.6f}")


def main():
    t_start = time.time()
    xs, ys, radii, ms, ns = S.build_disks(500.0)
    seg_mask = radii <= S.R_DISK
    print(f"圆盘总数 = {len(xs)}, 段认证附近盘(|q|<=470) = {int(seg_mask.sum())}")

    cands = [
        (4.8310, 3.8874, "NEW 447.9725 (Δ1=9.831, L1=11.0595, slow@3.8874)  [期望 447.9725, 刀锋]"),
        (4.8310, 3.8873, "Δ1=9.831 @3.8873 (L1=11.0478)  [期望 L1 悬崖低侧 ~440.5]"),
        (4.8300, 3.8874, "Δ1=9.830 @3.8874  [期望 Δ1 悬崖低侧 ~439.5]"),
        (4.8304, 3.8874, "Δ1=9.8304 @3.8874  [临界 9.83045 之下, 期望低侧]"),
        (4.8305, 3.8874, "Δ1=9.8305 @3.8874  [临界之上, 期望 ~447.97]"),
        (4.8500, 3.8871, "粗top-1 (9.85, L1=11.0245)  [期望 447.9601]"),
        (4.8500, 3.8872, "粗top-2 (9.85, L1=11.0362)  [期望 447.9536]"),
        (4.8500, 3.8874, "粗top-3 (9.85, L1=11.0595)  [期望 447.9406]"),
        (4.8328, 3.8873, "天真舍入 (9.8328, L1=11.0478)  [期望 440.4237 落崖]"),
        (4.8350, 3.8874, "山脊基准 (9.835, L1=11.0595)  [期望 447.9657, cert=9.000763]"),
    ]
    for turn2, ts, nm in cands:
        heading, ev = candidate(turn2, ts)
        r = my_certify(heading, ev, xs, ys, radii, ms, ns, seg_mask)
        if turn2 == 4.8310 and abs(ts - 3.8874) < 1e-9:
            C.print_plan_report(nm, r)          # 刀锋候选打印全 43 段表
        else:
            compact(nm, r)

    # 落盘 NEW 候选官方格式文件并自检
    lines = open(REC, encoding="utf-8").read().splitlines()
    out = lines[:99] + ["R 3.7924 5.0000", "R 3.7924 4.8310", "- 3.8874"]
    with open(CANDFILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    ver, heading, events = cxk.read_plan(CANDFILE)
    sim = cxk.simulate(heading, events)
    print("-" * 90)
    print(f"[官方文件自检 {CANDFILE}] 行数={len(out)+1} ver={ver}")
    print(f"  cxk: r={sim['r']:.4f}  t={sim['t']:.6f}  撞点({sim['p'][0]:.4f},{sim['p'][1]:.4f})")

    print(f"\n总耗时 = {time.time() - t_start:.2f} s")


if __name__ == "__main__":
    main()
