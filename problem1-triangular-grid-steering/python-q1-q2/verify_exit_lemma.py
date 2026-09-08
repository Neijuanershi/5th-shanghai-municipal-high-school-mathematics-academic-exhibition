# Verify the window formulas for Lemma 2.4 (exit lemma) of report.tex.
# Geometry: gap chord between disks C1=(k,0) and C2=(k-1,1), direction u=e(120deg).
# Exit point Q at window parameter s in [9,11]  (distance s to C1, 20-s to C2).
# Robot is a point; disks have radius 9; tangency (distance = 9) allowed.
import math

R = 9.0
DEG = math.pi / 180.0

def w120(x, y):
    """direction (120 deg) unit vector"""
    return (-0.5 * x, math.sqrt(3) / 2 * x)

def dist_to_disk(q, c, v, tmin, tmax, steps=4000):
    """min over t in [tmin,tmax] of |q + t*v - c| (fine sampling near foot)"""
    # exact: f(t)=t^2-2t*(c-q).v+|c-q|^2 ; vertex at tv=(c-q).v
    d = (c[0] - q[0], c[1] - q[1])
    dot = d[0] * v[0] + d[1] * v[1]
    d0 = math.hypot(*d)
    tv = dot
    t_candidates = [tmin, tmax]
    if tmin <= tv <= tmax:
        t_candidates.append(tv)
    best = min(math.hypot(q[0] + t * v[0] - c[0], q[1] + t * v[1] - c[1])
               for t in t_candidates)
    return best

def feasible_theta(s, side, theta_deg, tol=1e-9):
    """side in {'exit','approach','line'}: heading theta_deg clears both gap disks."""
    C1 = (0.0, 0.0)          # disk (k,0) relative to Q at s=... wait: C1-Q = -s*u
    # Set Q at origin; C1 = -s*u, C2 = (20-s)*u, u=e(120deg)
    u = (-0.5, math.sqrt(3) / 2)
    C1 = (-s * u[0], -s * u[1])
    C2 = ((20 - s) * u[0], (20 - s) * u[1])
    v = (math.cos(theta_deg * DEG), math.sin(theta_deg * DEG))
    if side == 'exit':
        tmin, tmax = 0.0, 1e4
    elif side == 'approach':
        tmin, tmax = -1e4, 0.0
    else:
        tmin, tmax = -1e4, 1e4
    d1 = dist_to_disk((0, 0), C1, v, tmin, tmax)
    d2 = dist_to_disk((0, 0), C2, v, tmin, tmax)
    return d1 >= R - tol and d2 >= R - tol

print("=" * 78)
print("s |  exit-only window      | approach-only window  | straight (line) window")
print("=" * 78)
for s in [9.0, 9.5, 10.0, 10.5, 11.0]:
    # predicted windows
    L_out = math.degrees(math.asin(R / s)) - 60.0
    U_out = 120.0 - math.degrees(math.asin(R / (20 - s)))
    L_in = math.degrees(math.asin(R / (20 - s))) - 60.0
    U_in = 120.0 - math.degrees(math.asin(R / s))
    c = max(R / s, R / (20 - s))
    L_line = math.degrees(math.asin(c)) - 60.0
    U_line = 120.0 - math.degrees(math.asin(c))
    print(f"{s:4.1f} | [{L_out:7.2f}, {U_out:6.2f}]      | [{L_in:7.2f}, {U_in:6.2f}]      | [{L_line:7.2f}, {U_line:6.2f}]")

    # brute-force check on a grid of headings, three sides
    for side, (Lp, Up), tag in [('exit', (L_out, U_out), 'E'),
                                ('approach', (L_in, U_in), 'A'),
                                ('line', (L_line, U_line), 'L')]:
        # check the whole predicted interval is feasible and nothing outside (within [-60,90]) is
        bad_in, good_out = [], []
        for th in [t / 10 for t in range(-600, 901)]:
            feas = feasible_theta(s, side, th)
            inside = Lp - 0.05 <= th <= Up + 0.05
            if inside and not feas:
                bad_in.append(th)
            if not inside and feas:
                good_out.append(th)
        if bad_in:
            print(f"   {tag}: PREDICTED-FEASIBLE BUT INFEASIBLE: {bad_in}")
        if good_out:
            print(f"   {tag}: feasible OUTSIDE predicted window: {good_out[:6]}{'...' if len(good_out)>6 else ''}")
        else:
            print(f"   {tag}: window verified exactly on [-60,90] grid")

print()
print("lower endpoint of straight window vs beta=4.1581 deg:")
beta = 30.0 - math.degrees(math.acos(0.9))
for s in [9.0, 9.5, 10.0, 10.5, 11.0]:
    c = max(R / s, R / (20 - s))
    L = math.degrees(math.asin(c)) - 60.0
    print(f"  s={s:4.1f}: c={c:.4f}  L={L:8.3f}  (beta={beta:.3f})  L>=beta: {L >= beta - 1e-9}")

# also: heading of straight segment = intersection of one-sided windows
print()
print("intersection check  [L_in,U_in] ∩ [L_out,U_out] == [L_line,U_line]:")
for s in [9.0, 9.5, 10.0, 10.5, 11.0]:
    L_out = math.degrees(math.asin(R / s)) - 60.0
    U_out = 120.0 - math.degrees(math.asin(R / (20 - s)))
    L_in = math.degrees(math.asin(R / (20 - s))) - 60.0
    U_in = 120.0 - math.degrees(math.asin(R / s))
    c = max(R / s, R / (20 - s))
    Li = max(L_in, L_out); Ui = min(U_in, U_out)
    L_line = math.degrees(math.asin(c)) - 60.0
    U_line = 120.0 - math.degrees(math.asin(c))
    ok = abs(Li - L_line) < 1e-9 and abs(Ui - U_line) < 1e-9
    print(f"  s={s:4.1f}: intersection [{Li:7.2f},{Ui:6.2f}] vs formula [{L_line:7.2f},{U_line:6.2f}]  {'OK' if ok else 'MISMATCH'}")
