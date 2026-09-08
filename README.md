# Research on Two Long-Form Mathematical Problems — 5th Shanghai Municipal High-School Mathematics Academic Exhibition (2026)

Two open-ended research problems solved in summer 2026 (June–August) for the
**5th Shanghai Municipal High-School Mathematics Academic Exhibition**
(第五届上海市中学数学学术展评活动, final rounds 20–21 August 2026, Shanghai Shixi High School).
Competing for Shanghai Xiangming High School, the team was awarded the
**Special Prize (Bronze) of the long-form research track** and the **Third Prize of the
team relay round** (official announcement:
https://mp.weixin.qq.com/s/dzRpSg0Q3pOVVqDV_Fltsg ).

**Author of this work: Jiaming Chu (褚家铭)** · GitHub: [Neijuanershi](https://github.com/Neijuanershi)
All mathematics, proofs and code were conceived and carried out by the author, with deep
assistance from an LLM coding agent (DeepSeek v4 Pro inside the DeepSeek Harness agentic
environment) — including the Lean 4 formalization below.

## Repository layout

```
problem1-triangular-grid-steering/    Obstacle-avoidance game on a triangular lattice
  problem1_report_en.md               English technical report (this document, readable on GitHub)
  problem1_report_zh.pdf              Original Chinese report (222 pp., full source & logs in appendices)
  lean-formalization/                 Lean 4 project: machine-verified lower bound N(n) ≥ 4n+1
  python-q1-q2/                       Python search / verification scripts (subproblems 1–2)
  python-q3-certification/            Certification scripts, official grader, 447.9733 m answer, logs
problem2-triangle-counting/           Extremal triangle counting in edge-augmented point sets
  problem2_report_en.md               English technical report
  problem2_report_zh.pdf              Original Chinese report (complete version)
  code/                               Algorithms A–G: exhaustive DFS, SAT (CaDiCaL), CP-SAT (OR-Tools)
```

## Problem 1 — Obstacle-avoidance game on a triangular lattice
On a 20 m triangular lattice, a 1 m-radius robot travels among radius-8 m circular
obstacles arranged in concentric hexagonal layers; each "steering card" changes heading by
at most 5°, and clearance from every obstacle centre must stay ≥ 9 m.
- Escaping the first two layers needs **exactly 9 cards** (upper & lower bounds close);
- General case: **N(1) = 0, N(n) = 4n+1 for n ≥ 2** — upper bound by per-layer 4β drift
  constructions (β = arcsin(9/10) − 60° ≈ 4.16°); lower bound by a prefix theorem,
  per-layer 4β direction windows and a global reduction partitioned at first-escape times;
  **the combinatorial layer is machine-verified in Lean 4** (five geometric axioms A–E and
  one opaque predicate `Escaped` as the interface; theorem `N_lower_bound` by strong
  induction + telescoping interval sums; `lake build` clean, zero `sorry`,
  `#print axioms` shows exactly the intended axioms);
- Rotating lattice (6°/s) with speed-up/slow-down cards: certified 100-card plan reaching
  **447.9733 m** (11 speed-ups + 88 steering + 1 slow-down), zero errors under the official
  checker, 43/43 segments Lipschitz-certified (clearance lower bound 9.000006).

The report grades every claim honestly: strictly proven / numerically certified / open
(e.g., global optimality beyond 447.9733 m remains open).

## Problem 2 — Extremal triangle counting in edge-augmented point sets
Given n points in general position with a forced subgraph H0 = K1,4 ⊔ 2K2 (6 edges),
minimize the number E(n,k) of total edges that force ≥ k triangles:
- Complete value tables for **n = 9, 10** (84 and 120 entries), triple-verified by
  exhaustive Numba DFS, SAT (CaDiCaL 1.9.5) and OR-Tools CP-SAT;
- Exact closed formula for all **n ≥ 11** with magnitude **E(n,k) = Θ(k^(2/3))**, via a
  triangle version of the Kruskal–Katona lemma and quasi-clique constructions;
- Minimum-degree variant (δ ≥ d): six purely theoretical lower bounds, exact
  E(9,11,3) = 15, closed forms at extreme degrees, 93-entry CP-SAT table (all OPTIMAL);
- Connected graphs with edge-disjoint triangles: **F(n,k) = n−1+k** on its full validity
  range (cycle-space lower bound max{3k, n−1+k}) and impossibility
  **F(9,7) = F(10,7) = ∞**; the remaining-region conjecture is declared open.

## Verification & honesty practices
- Every finite claim is cross-checked by ≥ 2 independent programs with reproduced run logs;
- Claims are labelled *machine-verified / numerically certified / classically proven /
  open*, matching the boundaries stated in the reports;
- An AI-assisted counterexample search forced a real revision of the formalization's
  half-open interval convention (v4.4 → v4.5) — see `problem1-triangular-grid-steering/lean-formalization/`.

## Build (Lean 4 part)
See `problem1-triangular-grid-steering/lean-formalization/README.md`
(Lean 4.33.0-rc1, mathlib @ 8baa3d095e9735e43cf5985d10ae3e9a0f5834d7; the `.lake/`
dependency tree is intentionally not committed).

---
*Research completed June–August 2026. Reports are in Chinese (originals) and English
(technical reports in Markdown at each problem directory).*
