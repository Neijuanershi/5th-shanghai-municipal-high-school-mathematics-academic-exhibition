# -*- coding: utf-8 -*-
"""
q3_certp1_align.py — P1 五参考点三方对齐测试.

用 P1 原语 (cert_seg_min 有限段 + cert_ray 终局射线) 做整份提交的数值认证,
与 cxk.simulate、q3_audit_sim.simulate 三方并列.

对齐判据 (采纳 P2 子代理 J §5 + root 复跑结论):
  ① 认证区间 [r_safe, r_coll] 必须包含 cxk 首撞半径;
  ② |audit_r − cxk_r| ≤ 0.015 m 记入已知伪象容差
     (q3_audit_sim dt_scan=2e-4 对终局射线「相切掠过」欠采样: 首撞 d=9.000000,
      d<9 窗极窄, 盘相对速度 ~140 m/s, 首撞半径系统性高估 ~+0.013 m).

参考点 (任务书):
  1. 纪录     447.8980  q3_campaign_best_saA.txt  (cxk.read_plan 解析)
  2. 旧纪录   447.7406  重建: Δ1=+10°, L1=11, slow=1
  3. 山脊     447.9657  官方 4 位小数: Δ1=9.835°, L1=11.06, slow=1
  4. 无效点   (Δ1=9.832764°, L1=11.052704) 官方舍入版 → 应 unsafe (cxk 440.42)
  5. 对照     cxk.simulate vs q3_audit_sim.simulate 同点三方并列

重建口径 (q3_final_gap_1w.build / q3_verify_gap_1w.build_candidate):
  保留纪录前 99 行 (11 加速 + 86 链转), 终局 3 行 = 2 张转卡 (Δ1 拆 5.0+余) + 1 慢卡.
  tB=3.7924, v=116.4153 (=10*1.25^11), t_slow=tB+L1/v (4 位小数舍入).
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cxk
import q3_audit_sim as aud
from q3_certp1_seg import (cert_seg_min, disks_in_ring, build_disk_index,
                           RCLR, W, SQ3)
import q3_certp1_ray as ray

REC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "q3_campaign_best_saA.txt")

DISK_INDEX, DISK_NORMS = build_disk_index(480.0)

AUDIT_TOL = 0.015   # ② 已知伪象容差 (m)


# ---------------- 计划重放 (与 q3_cert_merge_sa3.build_segments 同口径) ----------------


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
            segs.append((t, p, tt, v, (ux, uy)))
            p = (p[0] + v * ux * (tt - t), p[1] + v * uy * (tt - t))
            t = tt
        if kind == "spd":
            v *= a
        else:
            h += math.radians(a)
    ux, uy = math.cos(h), math.sin(h)
    return segs, (t, p, v, (ux, uy))


def seg_radius_range(p0, p1):
    r0 = math.hypot(*p0)
    r1 = math.hypot(*p1)
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dd = dx * dx + dy * dy
    if dd > 1e-30:
        s = -(p0[0] * dx + p0[1] * dy) / dd
        if 0.0 < s < 1.0:
            return math.hypot(p0[0] + s * dx, p0[1] + s * dy), max(r0, r1)
    return min(r0, r1), max(r0, r1)


def certify_segment(p0, v, u, t0, t1):
    """认证一条有限直线段对所有盘. 返回 (status, res, disk)."""
    p1 = (p0[0] + v * u[0] * (t1 - t0), p0[1] + v * u[1] * (t1 - t0))
    rmin, rmax = seg_radius_range(p0, p1)
    seg_disks = disks_in_ring(DISK_INDEX, DISK_NORMS, rmin - RCLR, rmax + RCLR)
    status = 'safe'
    worst = None
    wdisk = None
    for q in seg_disks:
        res = cert_seg_min(p0, v, u, t0, t1, q)
        if res['status'] == 'unsafe':
            return 'unsafe', res, q
        if res['status'] == 'indet' and status == 'safe':
            status = 'indet'
            worst = res
            wdisk = q
    return status, worst, wdisk


def certify_plan(path, r_cap=460.0):
    """整份提交认证. 返回 dict(verdict, r_safe, r_coll, ...)."""
    t_start = time.perf_counter()
    ver, heading, events = cxk.read_plan(path)
    segs, (t_end, p_end, v_end, u_end) = build_segments(heading, events)

    r_safe_finite = 0.0
    for (t0, p0, t1, v, u) in segs:
        status, res, disk = certify_segment(p0, v, u, t0, t1)
        if status == 'unsafe':
            t_hi = res['t_hi']
            px = p0[0] + v * u[0] * (t_hi - t0)
            py = p0[1] + v * u[1] * (t_hi - t0)
            r_coll = math.hypot(px, py)
            return dict(verdict='unsafe', where='finite', seg=(t0, t1),
                        r_safe=r_safe_finite, r_coll=r_coll, hit_disk=disk,
                        dmid=res['dmid'], nseg=len(segs),
                        elapsed=time.perf_counter() - t_start)
        if status == 'indet':
            return dict(verdict='indet', where='finite', seg=(t0, t1),
                        r_safe=r_safe_finite, r_coll=None, hit_disk=disk,
                        nseg=len(segs), elapsed=time.perf_counter() - t_start)
        r_safe_finite = max(r_safe_finite, math.hypot(
            p0[0] + v * u[0] * (t1 - t0), p0[1] + v * u[1] * (t1 - t0)))

    r = ray.cert_ray(p_end, u_end, v_end, t_end, r_cap=r_cap)
    if 'error' in r:
        return dict(verdict='error', ray=r, r_safe=r_safe_finite,
                    elapsed=time.perf_counter() - t_start)
    r_safe = max(r_safe_finite, r['r_safe'])
    r_coll = r['r_coll']
    verdict = 'indet' if r.get('indet') else ('safe' if r['all_safe'] else 'unsafe')
    return dict(verdict=verdict, where='ray', r_safe=r_safe, r_coll=r_coll,
                hit_disk=(r.get('hit') or {}).get('disk'), ray=r, nseg=len(segs),
                elapsed=time.perf_counter() - t_start)


# ---------------- 参考点重建 ----------------


def build_candidate(d1, L1, out):
    with open(REC, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    assert len(lines) == 102, f"纪录行数 {len(lines)} != 102"
    tB = 3.7924
    v = 116.4153
    t_slow = tB + L1 / v
    r1 = min(5.0, d1)
    r2 = d1 - r1
    nl = lines[:99]
    nl.append(f"R {tB:.4f} {r1:.4f}")
    nl.append(f"R {tB:.4f} {r2:.4f}")
    nl.append(f"- {t_slow:.4f}")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(nl) + "\n")
    return out


def audit_sim(path):
    h0, cards = aud.parse(path)
    t_coll, p_coll, score, min_clear = aud.simulate(h0, cards, R_max=470.0,
                                                    dt_scan=2e-4)
    r_coll = math.hypot(*p_coll) if p_coll is not None else None
    return t_coll, r_coll, score, min_clear


def run_point(tag, path, expected):
    ver, hd, ev = cxk.read_plan(path)
    errs = cxk.validate(ver, hd, ev)
    sim = cxk.simulate(hd, ev)
    a_t, a_r, a_score, min_clear = audit_sim(path)
    cert = certify_plan(path)
    return dict(tag=tag, errs=errs, sim=sim, a_t=a_t, a_r=a_r,
                a_score=a_score, min_clear=min_clear, cert=cert,
                expected=expected)


def main():
    out_lines = []
    def P(*a):
        line = " ".join(str(x) for x in a)
        out_lines.append(line)
        print(line)

    P("=" * 108)
    P("P1 五参考点三方对齐 (q3_certp1_align.py)")
    P("口径: 区间算术认证 (cert_seg_min 有限段 + cert_ray 终局射线), 净距阈值 9, 相切安全")
    P("=" * 108)

    pts = []
    P("\n[点1] 纪录 447.8980 (q3_campaign_best_saA.txt)")
    pts.append(run_point("P1 纪录 447.8980", REC, 447.8980))

    f2 = build_candidate(10.0, 11.0, "_tmp_p1_old.txt")
    P("\n[点2] 旧纪录 447.7406 (Δ1=+10°, L1=11, slow=1)")
    pts.append(run_point("P2 旧纪录 447.7406", f2, 447.7406))

    f3 = build_candidate(9.835, 11.06, "_tmp_p1_ridge.txt")
    P("\n[点3] 山脊 447.9657 (Δ1=9.835°, L1=11.06, slow=1, 官方 4 位)")
    pts.append(run_point("P3 山脊 447.9657", f3, 447.9657))

    f4 = build_candidate(9.832764, 11.052704, "_tmp_p1_invalid.txt")
    P("\n[点4] 无效点官方舍入版 (Δ1=9.832764°, L1=11.052704)  → 应 unsafe, cxk≈440.42")
    pts.append(run_point("P4 无效点(舍入)", f4, 440.42))

    # 对比表
    P("\n" + "-" * 108)
    P("逐点对比表 (三方)")
    P(f"{'点':<20}{'我方cert判定':<9}{'认证区间':<22}{'cxk r':<10}"
      f"{'audit r(粗)':<12}{'|audit−cxk|':<12}")
    P("-" * 108)
    for pt in pts:
        sim = pt['sim']
        c = pt['cert']
        if c['verdict'] == 'unsafe':
            iv = f"[{c['r_safe']:.4f}, {c['r_coll']:.4f}]"
        elif c['verdict'] == 'safe':
            iv = f"[{c['r_safe']:.4f}, inf)"
        else:
            iv = f"[{c['r_safe']:.4f}, ?] ({c['verdict']})"
        a_r = f"{pt['a_r']:.4f}" if pt['a_r'] is not None else "no-coll"
        delta = (abs(pt['a_r'] - sim['r']) if pt['a_r'] is not None
                 else float('inf'))
        P(f"{pt['tag']:<20}{c['verdict']:<9}{iv:<22}{sim['r']:<10.4f}"
          f"{a_r:<12}{delta:<12.4f}")
    P("-" * 108)

    # 一致性判定 (① + ②)
    P("\n一致性与区间包含判定 (判据: ①区间含cxk 且 ②|audit−cxk|≤0.015m):")
    agree = 0
    for pt in pts:
        sim = pt['sim']
        c = pt['cert']
        cxk_r = sim['r']
        a_r = pt['a_r']
        my_unsafe = (c['verdict'] == 'unsafe')
        cxk_unsafe = sim['collide']
        aud_unsafe = (pt['a_t'] is not None)
        verdict_ok = (my_unsafe == cxk_unsafe == aud_unsafe)
        if c['verdict'] == 'unsafe':
            contain_cxk = c['r_safe'] <= cxk_r <= c['r_coll'] + 1e-9          # ①
            audit_delta = abs(a_r - cxk_r) if a_r is not None else float('inf')
            audit_ok = audit_delta <= AUDIT_TOL                              # ②
        else:
            contain_cxk = False
            audit_delta = float('inf')
            audit_ok = False
        ok = verdict_ok and contain_cxk and audit_ok
        agree += 1 if ok else 0
        P(f"  {pt['tag']:<20} 判定一致={verdict_ok} ①含cxk={contain_cxk} "
          f"②|audit−cxk|={audit_delta:.4f}≤{AUDIT_TOL:.3f}={audit_ok} → "
          f"{'一致' if ok else '矛盾'}")
    P(f"\n三方一致 (判定 + ①区间含cxk + ②|audit−cxk|≤0.015m容差): {agree}/4 点")
    P("注: audit_sim dt_scan=2e-4 对终局射线「相切掠过」(首撞 d=9.000000, d<9 窗极窄, 盘相对速度 ~140 m/s)")
    P("    欠采样 → 首撞半径系统性高估 ~+0.013 m, 属已知伪象容差 (P2 J §5, root 复跑证实), 见点5.")

    # 参考点 5: 对照
    P("\n" + "-" * 108)
    P("[点5] 对照: 双模拟器同点并列 + 我方区间")
    for pt in pts:
        sim = pt['sim']
        c = pt['cert']
        a_r = f"{pt['a_r']:.4f}" if pt['a_r'] is not None else 'inf'
        P(f"  {pt['tag']:<20} cxk={sim['r']:.4f} | audit={a_r} "
          f"| 我方={c['r_safe']:.4f}..{c['r_coll'] if c['r_coll'] is not None else 'inf'}")
    P("=" * 108)

    # 耗时
    P("\n认证耗时 (certify_plan, 含有限段+射线):")
    for pt in pts:
        P(f"  {pt['tag']:<20} {pt['cert']['elapsed']*1000:.0f} ms  "
          f"(nseg={pt['cert']['nseg']}, where={pt['cert']['where']})")

    with open("q3_certp1_align.txt", "w", encoding="utf-8") as fp:
        fp.write("\n".join(out_lines) + "\n")
    print("\n[已写 q3_certp1_align.txt]")


if __name__ == "__main__":
    main()
