# Extremal Triangle Counting in Edge-Augmented Point Sets: Construction, Lower Bounds, and Computational Verification across Four Questions

**Author:** Jiaming Chu (褚家铭)

**Affiliation:** Shanghai Xiangming High School · Team Noxus (上海向明中学 · 诺克萨斯队)

**Source problem:** Problem 2 (long-term problem) of the 5th Shanghai Secondary School Mathematics Academic Exhibition (第五届上海市中学数学学术展评长期题二), defense August 2026.

**Note on language.** This document is the English technical-report version of the author's complete Chinese report. The full Chinese original — including all appendices with verbatim source code and complete run logs — is available in the same directory as `problem2_report_zh.pdf`. Throughout this document the author writes in the third person.

---

## Abstract

The problem asks how many additional line segments must be drawn among $n$ points in general position so that the resulting graph, which must contain a prescribed *forced* subgraph $H_0$, acquires at least $k$ triangles. The author shows that the geometric statement is exactly equivalent to a purely graph-theoretic one, and that the entire problem is governed by a single local principle, the **common-neighbor criterion**: adding an edge $(u,v)$ increases the triangle count by exactly the number of common neighbors of $u$ and $v$. From this criterion follow the two construction principles that drive all upper bounds — *complete graphs are optimal* and *large cliques first*.

Building on this framework, the report resolves the four progressively harder sub-questions:

1. **Question 1 ($n=9,10$):** complete tables of $E(n,k)$, obtained by exhaustive enumeration and independently confirmed by SAT and CP-SAT solvers.
2. **Question 2 (general $n\ge 11$):** an exact, $n$-independent formula $E(n,k)=\binom{a_1}{2}+d$ for $n\ge n_0(k)$, together with the asymptotic order $E(n,k)=\Theta(k^{2/3})$ with leading coefficient $(9/2)^{1/3}$.
3. **Question 3 (minimum degree $\delta\ge d$):** six purely theoretical lower bounds, a fully proved exact value $E(9,11,3)=15$, closed forms in the extreme degree cases $d\in\{n-1,n-2,n-3\}$, and a CP-SAT-verified exact table for $n=9$.
4. **Question 4 (connected, triangle-edge-disjoint):** the universal lower bound $\max\{3k,\,n-1+k\}$, an explicit construction attaining it in a provably solved region, an infeasibility phenomenon at $k=7,\ n=9,10$, and CP-SAT numerical evidence for the remaining region (with the full characterization stated as a conjecture).

Throughout, the author maintains an explicit distinction between results that are *purely proved*, results that are *computationally certified* (UNSAT / OPTIMAL), and results that remain *open*.

---

## 1 Problem Statement and Framework

### 1.1 The geometric problem

Let $n\ge 9$ points be given in the plane, no three collinear. A *forced subgraph* $H_0$ is fixed in advance on vertices $\{0,1,\dots,8\}$ with edge set

$$
H_0 \;=\; \bigl\{(0,1),(0,2),(0,3),(0,4),(5,6),(7,8)\bigr\},
$$

so that $H_0\cong K_{1,4}\sqcup 2K_2$: a star centered at vertex $0$ together with two independent edges. $H_0$ has exactly $6$ edges and contains no triangle. While preserving all six forced edges, one may keep drawing further line segments. The goal is to make the whole graph contain at least $k$ triangles, where a *triangle* means three vertices pairwise joined by edges (a graph-theoretic $3$-cycle; the no-three-collinear hypothesis guarantees the corresponding three points are geometrically non-collinear). Let

$$
E(n,k) \;=\; \min\Bigl\{\,|E(G)|\;:\; |V(G)|=n,\; H_0\subseteq G,\; t(G)\ge k\,\Bigr\},
$$

where $t(G)$ denotes the number of triangles of $G$ and "$H_0\subseteq G$" means all six edges of $H_0$ are present in $G$. The author adopts $k\ge 1$ throughout; the case $k=0$ is trivial, with $E(n,0)=6$ (the graph $H_0$ itself).

### 1.2 Equivalence of the geometric and graph-theoretic problems

The problem is posed geometrically, but it is **exactly equivalent** to the purely graph-theoretic problem above. Any $n$ points in general position can simultaneously serve as the vertices of any simple graph on $n$ vertices in a straight-line drawing: one simply joins each abstract edge by a straight segment. Whether segments cross affects only the picture, never *which* triples of points are pairwise joined. Consequently the number of triangles depends only on the adjacency relation, not on the positions of the points. The author therefore works entirely in the abstract graph framework for the whole report.

### 1.3 Notation

- $t(G)$: the number of triangles in $G$.
- $\binom{m}{r}$: the binomial coefficient, with the convention $\binom{m}{r}=0$ whenever $r>m$ or $r<0$.
- $K_m$: the complete graph on $m$ vertices, with $\binom{m}{2}$ edges and $\binom{m}{3}$ triangles.
- $E(n,k)$: as defined in (1); the minimum number of edges in an $n$-vertex graph containing $H_0$ and at least $k$ triangles.

### 1.4 The common-neighbor criterion

The single most important observation in the report is elementary but decisive. Suppose edges are added one at a time. When an edge $(u,v)$ is added to a graph, the newly created triangles are exactly those of the form $(u,v,w)$ where $w$ is already adjacent to *both* $u$ and $v$. Hence:

> **Common-neighbor criterion.** Adding the edge $(u,v)$ increases the triangle count by exactly the number of common neighbors of $u$ and $v$.

This criterion yields two guiding principles. **Complete graphs are optimal**: among all $m$-edge graphs, the complete graph (and, more generally, the *quasi-clique* of Section 3) maximizes the number of triangles, because every new edge added inside a clique meets the maximum possible number of common neighbors. **Large cliques first**: to reach many triangles with few edges, one should first saturate a large clique, then connect a fresh vertex to as many clique vertices as possible.

### 1.5 The four questions

The report treats four progressively stronger versions of the problem:

1. **Q1.** Complete tables of $E(n,k)$ for $n=9$ and $n=10$.
2. **Q2.** An exact formula and asymptotic order for general $n\ge 11$.
3. **Q3.** The same minimum subject to an additional minimum-degree constraint $\delta(G)\ge d$, denoted $E(n,k,d)$.
4. **Q4.** The minimum $F(n,k)$ subject to three simultaneous constraints: $G$ is *connected*, any two triangles are *edge-disjoint* (no edge lies in two triangles), and $t(G)\ge k$.

---

## 2 Question 1: Complete Tables for $n=9,10$

### 2.1 The range of $k$ and the complete enumeration for $n=9$

The complete graph $K_9$ contains $H_0$, has $\binom{9}{2}=36$ edges and $\binom{9}{3}=84$ triangles, so for $n=9$ it is necessary and sufficient that $1\le k\le 84$.

Apart from the six forced edges there are exactly $30$ optional edges. For each target $k$, the author's program enumerates, in increasing order of the number $c$ of added edges, all $\binom{30}{c}$ ways of choosing $c$ additional edges, and computes the triangle count of the resulting graph. The first $c$ for which some choice yields at least $k$ triangles gives

$$
E(9,k) \;=\; 6+c .
$$

Because every smaller candidate set of edges was exhaustively ruled out, the resulting value is genuinely minimal, and the procedure simultaneously produces a witnessing graph attaining it. The implementation uses Numba acceleration and $8$-way multiprocessing.

The resulting sequence $E(9,k)$ is specified over all $84$ values of $k$. The following table records a representative subset of $16$ values; the complete $84$-entry table appears in the Chinese report (and is reproduced by Code A in the repository).

| $k$ | 1 | 2 | 4 | 8 | 11 | 12 | 16 | 21 | 24 | 27 | 31 | 36 | 40 | 42 | 48 | 56 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| $E(9,k)$ | 7 | 8 | 9 | 12 | 14 | 15 | 16 | 18 | 20 | 21 | 22 | 24 | 26 | 27 | 28 | 29 |

Two values never occur in the sequence: **13** and **23**. Concretely, going from $k=10$ to $k=11$ the minimum jumps from $12$ to $14$, and going from $k=35$ to $k=36$ it jumps from $22$ to $24$.

### 2.2 Three-way verification of the $n=9$ table

The $n=9$ table was cross-checked by three independent routes, which agree entry by entry:

1. **Complete DFS enumeration** (Numba-accelerated, $8$ processes) — Code A.
2. **OR-Tools CP-SAT exact optimization** — for each edge-count tier $e=6,\dots,36$, the maximum number of triangles is solved to optimality (all `OPTIMAL`), and $E(9,k)$ is recovered by inversion; this is a methodologically independent route from brute-force enumeration.
3. **Plain-Python exhaustive anchor checks** for the low end $k\le 10$.

### 2.3 The result for $n=10$

The complete graph $K_{10}$ contains $\binom{10}{3}=120$ triangles, so for $n=10$ the range is $1\le k\le 120$. The answer splits into two ranges.

**Low range, $1\le k\le 84$.** Adding an isolated tenth vertex to an optimal nine-vertex graph does not change edge or triangle counts, giving the upper bound $E(10,k)\le E(9,k)$. The reverse inequality is certified by SAT: for each $k$ and each candidate edge count $e<E(9,k)$, the author builds a SAT instance with variables $x_{uv}$ for optional edges, an exact-edge-count constraint $\sum x_{uv}=e-6$, triangle-indicator variables $y_{abc}$ (Tseitin-encoded as "all three edges present," with $H_0$'s edges treated as true), and a triangle-count constraint $\sum y_{abc}\ge k$. All variables are allocated through a single `IDPool` to eliminate any identifier collision, and instances already excluded by the Kruskal–Katona upper bound (Section 3) are skipped. Every submitted instance returns `UNSAT`. Hence

$$
\boxed{\,E(10,k)=E(9,k)\qquad(1\le k\le 84).\,}
$$

That is, the tenth point is "free": it costs no additional edge in this range.

**High range, $85\le k\le 120$.** Define

$$
d(k)=\min\Bigl\{\,t\ge 2:\ \binom{t}{2}\ge k-84\,\Bigr\}.
$$

Then

$$
\boxed{\,E(10,k)=36+d(k)\qquad(85\le k\le 120).\,}
$$

The upper bound is the quasi-clique construction: take $K_9$ ($36$ edges, $84$ triangles) and join a tenth vertex to any $d(k)$ of its vertices. The $d(k)$ new edges create exactly $\binom{d(k)}{2}$ new triangles, since those $d(k)$ neighbors are pairwise adjacent. The lower bound is a direct application of the triangle Kruskal–Katona lemma (Section 3): with at most $\binom{9}{2}+(d(k)-1)$ edges the graph has at most $\binom{9}{3}+\binom{d(k)-1}{2}=84+\binom{d(k)-1}{2}<k$ triangles, by minimality of $d(k)$. The high-range table is:

| $k$ | $d(k)$ | $E(10,k)$ |
|---:|---:|---:|
| 85 | 2 | 38 |
| 86–87 | 3 | 39 |
| 88–90 | 4 | 40 |
| 91–94 | 5 | 41 |
| 95–99 | 6 | 42 |
| 100–105 | 7 | 43 |
| 106–112 | 8 | 44 |
| 113–120 | 9 | 45 |

---

## 3 Question 2: General $n$ — Exact Formula and $\Theta(k^{2/3})$

### 3.1 The triangle Kruskal–Katona lemma

Both the $n=10$ high-range lower bound and the general-$n$ exact formula rest on a classical extremal statement, which the author derives from the Kruskal–Katona theorem (in Lovász's graph form) and states self-containedly.

> **Lemma (triangle Kruskal–Katona).** Write $m\ge 0$ uniquely as $m=\binom{a}{2}+b$ with $0\le b<a$. Then every simple graph with at most $m$ edges has at most
>
> $$
> f(m)\;=\;\binom{a}{3}+\binom{b}{2}
> $$
>
> triangles. The bound is tight: the *quasi-clique* consisting of $K_a$ together with one new vertex joined to any $b$ vertices of the clique has exactly $m$ edges and $f(m)$ triangles.

The proof is by induction on $m$. Take an $m$-edge graph maximizing the triangle count and a minimum-degree vertex $v$ of degree $\delta$. At most $\binom{\delta}{2}$ triangles pass through $v$, and by induction the remaining graph has at most $f(m-\delta)$ triangles, so $t(G)\le\binom{\delta}{2}+f(m-\delta)$. A short case analysis on whether $\delta\le b$ or $\delta>b$, using the vertex bound $\delta(\delta+1)\le 2m$, verifies $\binom{\delta}{2}+f(m-\delta)\le f(m)$. The quasi-clique shows tightness.

### 3.2 Exact formula for large $k$

For $k\ge 85$ define

$$
a_1=\max\Bigl\{\,t\ge 1:\ \binom{t}{3}\le k\,\Bigr\},\qquad
r=k-\binom{a_1}{3},\qquad
d=\begin{cases}0,&r=0,\\[2pt]\min\bigl\{\,t\ge 1:\ \binom{t}{2}\ge r\,\bigr\},&r>0.\end{cases}
$$

and let $n_0(k)=a_1$ if $r=0$ and $n_0(k)=a_1+1$ if $r>0$. Then for every $n\ge n_0(k)$,

$$
\boxed{\,E(n,k)=\binom{a_1}{2}+d\,},
$$

a formula **independent of $n$**. For $11\le n<n_0(k)$ there is no feasible graph, since even $K_n$ has fewer than $k$ triangles.

- **Upper bound (quasi-clique).** Take $K_{a_1}$. If $r=0$ it is already feasible. If $r>0$, add one new vertex joined to any $d$ clique vertices; this adds $d$ edges and $\binom{d}{2}$ new triangles. Since $a_1\ge 9$ the construction contains $H_0$; isolated points cover any $n\ge n_0(k)$.
- **Lower bound.** If $r=0$, a graph with $\le\binom{a_1}{2}-1$ edges has, by the lemma, at most $\binom{a_1-1}{3}+\binom{a_1-2}{2}<\binom{a_1}{3}=k$ triangles. If $r>0$, a graph with $\le\binom{a_1}{2}+d-1$ edges has at most $\binom{a_1}{3}+\binom{d-1}{2}<k$ triangles by minimality of $d$. In both cases the bound applies to all graphs and hence *a fortiori* to those containing $H_0$.

**Boundary coherence.** The low and high formulas agree: $E(n,84)=E(9,84)=36$, while $k=85$ gives $a_1=9$, $r=1$, $d=2$, and $E(n,85)=36+2=38$. For $n=10$ and $85\le k\le 120$ the general formula coincides with Question 1's formula $36+d(k)$.

### 3.3 The asymptotic order

From $\binom{a_1}{3}\le k<\binom{a_1+1}{3}$ one obtains $a_1=(6k)^{1/3}(1+o(1))$, hence the leading term

$$
E(n,k)=\binom{a_1}{2}+d=\frac{(6k)^{2/3}}{2}\bigl(1+o(1)\bigr)=\Bigl(\tfrac92\Bigr)^{1/3}k^{2/3}\bigl(1+o(1)\bigr)\approx 1.651\,k^{2/3},
$$

and the remainder $d\le a_1=O(k^{1/3})$ is absorbed. Thus $E(n,k)=\Theta(k^{2/3})$ with leading coefficient $(9/2)^{1/3}$.

### 3.4 The reduction proof and the 1426 SAT instances

The lower bound for the *small*-$k$ regime, $E(n,k)=E(9,k)$ for all $n\ge 11$ and $1\le k\le 84$, is proved by a theoretical reduction followed by computer-assisted verification.

The upper bound is again trivial (append isolated points). For the lower bound, suppose a counterexample exists: some $n\ge 11$ and graph $G$ with $H_0\subseteq G$, $t(G)\ge k$, and $e(G)<E(9,k)$. Choose a counterexample $G^{*}$ with **minimum vertex count**. Call a vertex *free* if it is not among the nine vertices of $H_0$.

1. **Every free vertex lies in a triangle.** If a free vertex $v$ were in no triangle, deleting it would preserve $H_0$ and the triangle count while reducing the edge count, yielding a smaller counterexample (if at least $11$ vertices remain) or a ten-vertex counterexample contradicting $E(10,k)=E(9,k)$. Hence no such $v$ exists.
2. **Bound on the number of free vertices.** Each free vertex then has degree $\ge 2$. With $m=n-9$ free vertices and $e$ edges, a degree-counting argument gives $2m\le\sum_{v\text{ free}}\deg(v)\le 2(e-6)$, hence $m\le e-6\le E(9,k)-7$.

The negation of the theorem is therefore equivalent to the existence of a graph on $9+m$ vertices (with $2\le m\le E(9,k)-7$) satisfying $H_0\subseteq G$, total edge count $\le E(9,k)-1$, triangle count $\ge k$, and "every free vertex lies in a triangle." Each such case is encoded as a SAT instance (Tseitin transformation for triangle indicators, cardinality constraints via `seqcounter` and `cardnetwrk`, a single `IDPool`, backend CaDiCaL 1.9.5 through PySAT). The total number of instances is

$$
\sum_{k=1}^{84}\max\bigl\{E(9,k)-8,\,0\bigr\}=1426,
$$

and **all 1426 instances return `UNSAT`**. The reduction therefore compresses the infinitely many potential counterexamples into 1426 finite cases, each excluded by a solver in a reproducible environment — the same paradigm used, e.g., in the computer-assisted proof of the Four-Color Theorem. The author notes that DRAT-style UNSAT certificates could be generated for a fully independently auditable proof if desired.

---

## 4 Question 3: The Minimum-Degree Constraint $E(n,k,d)$

### 4.1 The problem

Impose, in addition to $H_0\subseteq G$ and $t(G)\ge k$, the constraint $\delta(G)\ge d$, and define

$$
E(n,k,d)=\min\Bigl\{\,e(G):\ |V(G)|=n,\ H_0\subseteq G,\ \delta(G)\ge d,\ t(G)\ge k\,\Bigr\},
$$

with the empty minimum $+\infty$. The parameter ranges are $n\ge 9$, $0\le d\le n-1$, $0\le k\le\binom{n}{3}$; within these ranges $K_n$ is always feasible, so the minimum exists.

### 4.2 Six purely theoretical lower bounds

The author derives six lower bounds, each using only part of the problem's data.

1. **Handshake bound.** $E(n,k,d)\ge\lceil nd/2\rceil$, since $2e(G)=\sum_v d_G(v)\ge nd$.
2. **Forced-subgraph degree-gap bound.** In $H_0$, vertex $0$ already has degree $4$, vertices $1,\dots,8$ have degree $1$, and the other $n-9$ vertices have degree $0$. To reach minimum degree $d$ the graph needs $(d-4)_+ + 8(d-1)_+ + (n-9)d$ additional degree units, each new edge supplying at most $2$, where $x_+=\max\{x,0\}$. Hence
$$
E(n,k,d)\ge 6+\Bigl\lceil\frac{(d-4)_++8(d-1)_++(n-9)d}{2}\Bigr\rceil.
$$
3. **Triangle–edge incidence bound.** Each edge lies in at most $n-2$ triangles, so $3\,t(G)\le(n-2)e(G)$, giving $E(n,k,d)\ge\lceil 3k/(n-2)\rceil$.
4. **Non-forced-edge bound.** $H_0$ contains no triangle, so every triangle uses at least one non-forced edge; thus $E(n,k,d)\ge 6+\lceil k/(n-2)\rceil$.
5. **Kruskal–Katona bound.** With the lemma of Section 3, define
$$
L_{\mathrm{KK}}(k)=\min\Bigl\{\,m:\ m=\binom{a}{2}+b,\ 0\le b<a,\ \binom{a}{3}+\binom{b}{2}\ge k\,\Bigr\};
$$
then $E(n,k,d)\ge L_{\mathrm{KK}}(k)$.
6. **Degree–triangle coupling bound $L_{\mathrm{DT}}$.** For each vertex set the lower degree bound $\ell_0=\max\{d,4\}$, $\ell_1=\dots=\ell_8=\max\{d,1\}$, $\ell_9=\dots=\ell_{n-1}=d$. For a fixed edge count $m$ consider the relaxation
$$
U(n,d,m)=\max\Bigl\{\,\sum_{i=0}^{n-1}\binom{x_i}{2}:\ \ell_i\le x_i\le n-1,\ \sum_i x_i=2m\,\Bigr\}.
$$
Since each triangle contributes one adjacent edge-pair at each of its three vertices, $3\,t(G)\le\sum_v\binom{d_G(v)}{2}$, and the degree vector is feasible for the relaxation (graphicality is *not* required, hence "relaxation"). Therefore
$$
E(n,k,d)\ge L_{\mathrm{DT}}(n,k,d):=\min\bigl\{\,m:\ U(n,d,m)\ge 3k\,\bigr\}.
$$
Because the marginal gain $\binom{x+1}{2}-\binom{x}{2}=x$ is increasing, $U(n,d,m)$ is computed by the greedy water-filling rule: distribute the surplus degree $2m-\sum_i\ell_i$ to coordinates of largest current value first, up to $n-1$.

These six bounds are all purely theoretical. Taking their maximum gives the **combined lower bound**

$$
E(n,k,d)\ge L(n,k,d):=\max\{\text{bounds 1–6}\}.
$$

An equality $L(n,k,d)\le M$ with an explicitly constructed $M$-edge feasible graph yields the exact value. Crucially, a lower bound alone never guarantees attainability; a matching construction or computation is always required.

### 4.3 The core worked example: $E(9,11,3)=15$

This value is proved **purely theoretically**.

- **Lower bound.** For $(n,k,d)=(9,11,3)$ the per-vertex degree lower bounds are $(4,3,\dots,3)$ with sum $28$. If $e(G)=14$ then the total degree is exactly $28$, so the relaxation admits no surplus degree and
$$
U(9,3,14)=\binom{4}{2}+8\binom{3}{2}=6+24=30<33=3\cdot 11\le 3\,t(G),
$$
contradicting the coupling bound. Hence $E(9,11,3)\ge 15$.
- **Upper bound.** Take $G=\bigl(K_{\{0,1,2,3,4\}}-\{12\}\bigr)\sqcup K_{\{5,6,7,8\}}$. Its edge count is $\bigl(\binom52-1\bigr)+\binom42=9+6=15$; all forced edges are present; the minimum degree is $3$; and the triangle count is $\bigl(\binom53-3\bigr)+\binom43=7+4=11$ (deleting edge $12$ destroys exactly the three triangles containing it). Hence $E(9,11,3)\le 15$, and the two bounds meet.

### 4.4 Extreme minimum-degree cases

- **$d=n-1$.** Then $G=K_n$, so $E(n,k,n-1)=\binom{n}{2}$ (requiring $k\le\binom{n}{3}$, otherwise infeasible).
- **$d=n-2$.** The complement $Q=\overline G$ satisfies $\Delta(Q)\le 1$, so $Q$ is a matching plus isolated vertices. If $|E(Q)|=q$, then
$$
E(n,k,n-2)=\binom{n}{2}-\min\Bigl\{\,\bigl\lfloor\tfrac n2\bigr\rfloor,\ \Bigl\lfloor\frac{\binom{n}{3}-k}{n-2}\Bigr\rfloor\,\Bigr\}.
$$
Each complement edge destroys exactly $n-2$ triangles, and because the matching edges are disjoint these destroyed sets are disjoint; hence $t(G)=\binom{n}{3}-q(n-2)$. Maximizing $q$ subject to $t(G)\ge k$ and $q\le\lfloor n/2\rfloor$ yields the formula.
- **$d=n-3$.** Now $\Delta(Q)\le 2$, so $Q$ is a disjoint union of paths, cycles, and isolated vertices, and by inclusion–exclusion
$$
t(G)=\binom{n}{3}-(n-2)\,e(Q)+\sum_v\binom{d_Q(v)}{2}-t(Q).
$$
The original problem is therefore exactly equivalent to maximizing $e(Q)$ over complements $Q$ with $\Delta(Q)\le 2$, $E(Q)\cap E(H_0)=\varnothing$, and the above expression $\ge k$; if the maximum is $q_{\max}$, then $E(n,k,n-3)=\binom{n}{2}-q_{\max}$.

### 4.5 The exact table for $n=9$ and a corrected hand-derived table

For $n=9$ and $d=2,3,4,5,6$, the author solves, for each edge-count tier $m$, the maximum number of triangles under the constraints ($H_0$ forced, $\delta\ge d$, at most $m$ edges), using CP-SAT. All **93 instances terminate with `OPTIMAL`**, and $E(9,k,d)$ is recovered by inversion. This computation **corrected an earlier hand-derived table**: in the rows $d=2$ and $d=5$, a total of $20$ tiers had been underestimated (the remaining $73$ tiers agreed). As one concrete example, for $d=2,\ m=24$ the hand-derived value $30$ was corrected to the true value $36$.

### 4.6 Exact equality for $k>84$ and $d=2$

For $k>84$ a deterministic polynomial-time construction algorithm exists: take a main clique $K_m$ containing $H_0$, group the remaining vertices to satisfy the degree constraint (each group of $d+1$ vertices forming $K_{d+1}$ costs $\binom{d+1}{2}$ edges and produces $\binom{d+1}{3}$ triangles, with a borrowing step against the main clique when the remainder is short), and finally connect an interface vertex to $c$ main-clique vertices, which contributes $\binom{c}{2}$ triangles. This yields a feasible (upper-bound) construction.

For $d=2$ this is upgraded to an **exact equality** at the minimum feasible vertex count: for $k>84$,

$$
E(n_0(k),k,2)=E(n_0(k),k)=\binom{a_1}{2}+d,
$$

with $a_1,d,r$ as in Section 3. The lower bound holds because the Q3 feasible region is a subset of the Q2 region; the upper bound holds because the quasi-clique construction of Theorem 2 has minimum degree $\ge 2$ in both the $r=0$ and $r>0$ cases. In particular, for $85\le k\le 120$ one has $n_0(k)=10$ and

$$
\boxed{\,E(10,k,2)=36+d(k)\qquad(85\le k\le 120).\,}
$$

CP-SAT re-verified all $36$ tiers $k=85,\dots,120$ independently, with **36/36 `OPTIMAL`** and full agreement. For $n>n_0(k)$ the pendant-point construction gives the upper bound $E(n,k,2)\le E(n_0(k),k,2)+2(n-n_0(k))$, whose optimality is **open**. For general $d\ge 3$ the optimality of the "main clique + scattered $K_{d+1}$ + single interface" shape is **not proved**; a unified closed formula for arbitrary $(n,k,d)$ remains an open problem, and specific parameters can be resolved exactly with the CP-SAT program in the appendix.

---

## 5 Question 4: Connected, Triangle-Edge-Disjoint Graphs $F(n,k)$

### 5.1 The problem

In addition to $H_0\subseteq G$, Question 4 requires simultaneously:

1. **Connectivity:** $G$ is connected;
2. **Triangle edge-disjointness:** any two distinct triangles have no common edge (every edge belongs to at most one triangle);
3. **Lower triangle count:** $t(G)\ge k$.

Let $F(n,k)$ be the minimum number of edges among all such graphs, with $F(n,k)=\infty$ if none exists. The edge-disjointness condition is the most restrictive of the three.

### 5.2 The universal lower bound via cycle space

> **Theorem.** For every parameter pair $(n,k)$ admitting a feasible graph,
>
> $$
> F(n,k)\;\ge\;\max\bigl\{\,3k,\; n-1+k\,\bigr\}.
> $$

- **(i)** Each triangle uses exactly $3$ edges and the triangles are pairwise edge-disjoint, so $k$ triangles occupy $3k$ distinct edges, giving $e(G)\ge 3k$.
- **(ii)** Since $G$ is connected, its cycle space (edge space modulo cut space) has dimension $e(G)-n+1$. The $k$ characteristic vectors of the edge-disjoint triangles are linearly independent: because the triangles are edge-disjoint, each triangle has a private edge, so no nontrivial linear combination can vanish. Hence $e(G)-n+1\ge k$, i.e. $e(G)\ge n-1+k$.

When $2k\le n-1$ the bound is dominated by $n-1+k$; when $2k\ge n-1$ it is dominated by $3k$. The bound uses no property of $H_0$ and is universal. The cycle-space dimension argument is the cornerstone of all lower-bound work in this question (see Lovász's classic problem book and Zhao's graph theory textbook for background on cycle space and linearly independent triangle families).

### 5.3 Base construction, induction, and expansion

**Base construction ($n=9$, $k=1,2,3,4$).** The author exhibits four graphs, each containing all forced edges, connected, triangle-edge-disjoint, with exactly $k$ triangles and exactly $8+k=n-1+k$ edges:

| $k$ | added edges (besides $H_0$) | triangles | edges |
|---:|---|---|---:|
| 4 | $12,34,05,06,17,18$ | $(0,1,2),(0,3,4),(5,6,0),(7,8,1)$ | $12=8+4$ |
| 3 | $12,34,05,06,27$ | $(0,1,2),(0,3,4),(5,6,0)$ | $11=8+3$ |
| 2 | $12,34,25,27$ | $(0,1,2),(0,3,4)$ | $10=8+2$ |
| 1 | $12,25,27$ | $(0,1,2)$ | $9=8+1$ |

None of these graphs has any extra triangle, and connectivity is witnessed by an explicit spanning tree. Hence $F(9,k)=8+k$ for $k=1,2,3,4$.

**Inductive extension ($k\ge 4$).** For every $k\ge 4$ there is a feasible graph $G_k$ on $2k+1$ vertices with $3k$ edges and exactly $k$ triangles. The base case $k=4$ is the first graph of the table above. Given $G_k$, add two fresh vertices $x,y$ and three fresh edges $0x,0y,xy$ (where $0$ is the center of $H_0$). The new triangle $(0,x,y)$ uses only new edges, so edge-disjointness is preserved; connectivity is preserved via $0x,0y$; and the edge/vertex counts advance by exactly $3$ and $2$.

**Vertex expansion (pendant points).** Given a base graph $G_0$ for $(n_0,k)$ with $e_0=n_0-1+k$ — the base table for $k\le 3$, or $G_k$ for $k\ge 4$ — append $m=n-n_0\ge 0$ pendant vertices, each joined by a single edge to an existing vertex. Pendant edges lie in no triangle, so edge-disjointness and connectivity are preserved, and each new vertex adds exactly one edge. The final edge count is $(n_0-1+k)+(n-n_0)=n-1+k$.

Combining the lower bound with this construction gives the exact formula.

> **Theorem (exact formula).** For $n\ge 9$ and $k\ge 1$: if $k\le 4$ then $F(n,k)=n-1+k$ for all $n\ge 9$; if $k\ge 5$ and $n\ge 2k+1$ then $F(n,k)=n-1+k$. Equivalently, whenever $n\ge\max\{9,\,2k+1\}$, one has $F(n,k)=n-1+k$.

### 5.4 The remaining region, infeasibility, and a conjecture

When $k\ge 5$ and $n<2k+1$, the lower bound is dominated by $3k$ and the above construction no longer applies directly. Two basic facts govern this region:

- **A necessary condition.** $k$ cannot exceed the maximum number of edge-disjoint triangles in $K_n$ (the triangle packing number) $T(n)\le\lfloor n(n-1)/6\rfloor$, attained when $n\equiv 1,3\pmod 6$ (Steiner triple systems), and equal to one less than the upper bound when $n\equiv 5\pmod 6$; the remaining congruence classes are governed by maximum-packing design theory (Lovász, *Combinatorial Problems and Exercises*, Exercise 13.31).
- **Known exact values.** CP-SAT gives $F(9,5)=15$ and $F(9,6)=18$ (both attaining $3k$). For $k=7$ there is an **infeasibility phenomenon**: $F(9,7)=F(10,7)=\infty$ — CP-SAT proves that no $9$- or $10$-vertex graph containing $H_0$ has more than $6$ edge-disjoint triangles — while the minimum feasible vertex count is $n=11$ with $F(11,7)=21=3\cdot 7$.

The full CP-SAT table for $n\le 15$ is:

| $n$ | lower bound $\max(3k,n-1+k)$ | $F(n,5)$ | $F(n,6)$ | $F(n,7)$ |
|---:|---:|---:|---:|---:|
| 9 | $15\ /\ 18\ /\ 21$ | 15 (OPTIMAL) | 18 (OPTIMAL) | $\infty$ (INFEASIBLE) |
| 10 | $15\ /\ 18\ /\ 21$ | 15 (OPTIMAL) | 18 (OPTIMAL) | $\infty$ (INFEASIBLE) |
| 11 | $15\ /\ 18\ /\ 21$ | 15 (thm) | 18 (OPTIMAL) | 21 (OPTIMAL) |
| 12 | $16\ /\ 18\ /\ 21$ | 16 (thm) | 18 (OPTIMAL) | 21 (OPTIMAL) |
| 13 | $17\ /\ 18\ /\ 21$ | 17 (thm) | 18 (thm) | 21 (OPTIMAL) |
| 14 | $18\ /\ 19\ /\ 21$ | 18 (thm) | 19 (thm) | 21 (OPTIMAL) |
| 15 | $19\ /\ 20\ /\ 21$ | 19 (thm) | 20 (thm) | 21 (thm) |

(Here "thm" marks values that follow from the proved formula $F(n,k)=n-1+k$ for $n\ge 2k+1$; "OPTIMAL" marks values certified by CP-SAT; "INFEASIBLE" marks CP-SAT-proved nonexistence. For $k=5$ and $k=6$ the entries $n=9,10$ are solved by CP-SAT and the remaining entries by the theorem; for $k=6$ the theorem applies from $n\ge 13$.)

Across $n\le 15$, every feasible tested parameter attains the lower bound, i.e. $F(n,k)=\max\{3k,\,n-1+k\}$. Accordingly the author states:

> **Conjecture.** For every parameter pair $(n,k)$ admitting a feasible graph,
> $$
> F(n,k)=\max\bigl\{\,3k,\ n-1+k\,\bigr\}.
> $$

The strict proof of this conjecture, and the complete characterization of the infeasible parameters, remain open. In the proved region one also has the recurrences $F(n+1,k)=F(n,k)+1$ (for $k\le 4$ or $n\ge 2k+1$), and, in the remaining region, only the pendant-point upper bound $F(n+1,k)\le F(n,k)+1$ and $F(n,k+1)\le F(n,k)+3$ are currently available.

---

## 6 Computational Verification Infrastructure

Every theoretical lower bound in this report is cross-checked by computation, implementing the double aim of *theory backed by machine verification*. The infrastructure has three independent pillars, with reproducible logs:

1. **Complete enumeration (DFS).** For $n=9$, a Numba-accelerated, $8$-process exhaustive search over the $30$ optional edges yields the complete table $E(9,k)$, $k=1,\dots,84$.
2. **Boolean satisfiability (SAT).** For the $n=10$ low range and the $n\ge 11$ reduction, instances are encoded with a single `IDPool` (eliminating identifier collisions), Tseitin-encoded triangle indicators, and cardinality constraints via `seqcounter`/`cardnetwrk`, and solved with CaDiCaL 1.9.5 through PySAT. All submitted instances return `UNSAT` — including the full set of $1426$ reduced instances in Question 2.
3. **OR-Tools CP-SAT exact optimization.** A methodologically independent second route: for each edge-count tier, maximize the triangle count (Question 1) or directly minimize the edge count (Questions 3 and 4), with all solved instances terminating in `OPTIMAL`. This covers the $93$ instances of the $n=9$ Question 3 table, the $36$ tiers $k=85,\dots,120$ for $n=10$, and the $n\le 15$ Question 4 table.

The three routes agree entry by entry wherever they overlap. The infrastructure also caught a genuine error: the independently recomputed CP-SAT table for $n=9$ corrected an earlier hand-derived table in the rows $d=2$ and $d=5$ (20 of 93 tiers; e.g. $d=2,\ m=24$: hand value $30$ corrected to true value $36$). This underscores the author's methodological point that finite-case conclusions in Question 3 should rest on reproducible computation rather than hand derivation.

All source code and run logs are provided in the repository's `code/` directory and in the appendices of the Chinese report; the author notes that DRAT certificates could be generated for a fully independent audit of the UNSAT claims if required.

---

## 7 Open Problems

The author records the following unresolved questions explicitly, distinguishing them from the proved and computationally certified results:

1. **Question 3, general parameters.** A unified closed-form formula for $E(n,k,d)$ for arbitrary $(n,k,d)$ is open; the six lower bounds and the deterministic construction algorithm sandwich the truth but are not known to be tight in general. In particular, for $d\ge 3$ the optimality of the "main clique + scattered $K_{d+1}$ + single interface" shape is unproved, and the tightness of the $d=2$ expansion bound $E(n,k,2)\le E(n_0(k),k,2)+2(n-n_0(k))$ is open.
2. **Question 4, remaining region.** The conjecture $F(n,k)=\max\{3k,n-1+k\}$ for all feasible parameters is unproved, and the complete characterization of infeasible parameters is open. The current evidence is CP-SAT data for $n\le 15$, in which every feasible tested point attains the bound.

---

## Appendix: Code Inventory

The full source is provided in the repository under `code/` and corresponds to the appendices A–G of the Chinese report. The following table gives a one-line description of each program; the code itself is not reproduced inline here.

| Appendix | File (repo `code/`) | Description |
|---|---|---|
| A | `enum9.py` | $n=9$ complete enumeration of $E(9,k)$ (Numba-accelerated, $8$-process DFS). |
| B | `sat10.py` | SAT verification of $E(10,k)=E(9,k)$ for $1\le k\le 84$ (PySAT). |
| C | `sat1426.py` | SAT verification of the reduced $n\ge 11$ instances for Question 2 (PySAT + CaDiCaL 1.9.5). |
| D | `q3_bounds.py` | Computation of the six theoretical lower bounds of Question 3, including the greedy water-filling evaluation of $L_{\mathrm{DT}}$. |
| E | `q3_exact_search.py` | Question 3 witness-graph search by cumulative edge-count bound (CP-SAT). |
| F | `q3_exact_optimize.py` | Question 3 direct edge-count-minimizing CP-SAT solver. |
| G | `q4_f_solver.py` | Question 4 exact solver for $F(n,k)$ (connected, triangle-edge-disjoint; CP-SAT). |

---

## References

1. L. Lovász, *Combinatorial Problems and Exercises*, 2nd ed., AMS Chelsea, 2007 — cycle space and the linear-algebra method for independent triangle families; Exercise 13.31 on Steiner triple systems and maximum packings.
2. Y. Zhao, *Graph Theory and Additive Combinatorics*, Cambridge University Press, 2023 — cycle space.
