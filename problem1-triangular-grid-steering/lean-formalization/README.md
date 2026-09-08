# Q2Formal —— 第二问下界 "N(n) ≥ 4n+1 (∀ n ≥ 2)" 的组合层形式化

照设计文档 `Q2_lean_baseline_plan.md` v4.4 第 5–6 节实施; 任务与验收红线见 `Q2Formal_HANDOFF.md`。

## 边界声明

形式化范围 = "几何公理 → ∀n 下界" 的组合层(归纳 + 记账 + 切分)。
几何层以显式公理进入; 构造方向(≤, 即 `dodge_path`)保持经典证明 + 双程序数值复核,
**不在本项目内实现**。

**本定理以五条未机器验证的几何公理(A:前缀 9 卡,第一问;B:逐层 4 卡;C:栅栏嵌套;D:首次穿越存在;E:首次穿越严格序)与一个未机器定义的几何谓词 Escaped 为前提**。

- 公理恰 5 条(A–E, `Q2Formal/Axioms.lean`), 不可约谓词恰 1 个(`Escaped`, `Q2Formal/Model.lean`), 全项目零占位(无未证项);
- 目标定理(设计文档第 3 节, 逐字):
  `N_lower_bound (n : ℕ) (hn : 2 ≤ n) : ∀ p : Plan, Valid n p → (∃ t, Escaped p n t) → p.cards ≥ 4 * n + 1`

> **对设计文档的一处经批准的修法**: 公理 A 由设计第 2 节的"总卡数 ≥ 9"改为**前缀局部化**
> `axiom base_nine : ∀ (p : Plan) (t : ℝ), Valid 2 p → FirstEscape p 2 t → CrossCardsLe p 0 t ≥ 9`
> (第 2 层首次逃出时刻 t **及之前**的闭区间卡数 ≥ 9)。原因: 原形式与公理 B 的逐层 CrossCards 无法经区间
> 可加性合成 9 + 4(n−2)(对同一总卡数的两个下界不可相加, 反例模型见开工报告); 新形式使归纳骨架
> 完整成立, 公理仍恰 5 条、C/D/E 与全部谓词签名不动。
>
> **v4.5 修订(闭区间化, 本版生效)**: v4.4 的半开形式 `CrossCards p 0 t ≥ 9` 在"弦上大转角转向"路径下
> 为假——古典真值: 第二次转向(走廊 −β → 出射 ≥β, ≥2β)可**恰在** t 时刻发生(门缝弦上转向, 转角可远大于
> 2β, 如 s* = 9.13 处一次转向 34.2° 穿出, 半开前缀 [0,t) 仅 7 卡 < 9)。v4.4 注释所引 (eq:exitwin)
> 双侧窗口论证只排除 ±β 弦上转向, 不排除大转角弦上转向。故 v4.5 起: 公理 A 用**闭前缀** `CrossCardsLe p 0 t`,
> 公理 B 用**左开右闭**逐层段 `CrossCardsOC p t₁ t₂`(段右端首逃时刻的卡归本段), 闭前缀与开闭链拼合
> 无重叠、无遗漏, 合成 9 + 4(n−2) 不变(修法依据: report ch3 前缀定理证明与独立审计发现的反例)。

## 文件清单(设计文档第 5 节)

| 文件 | 内容 |
|---|---|
| `Q2Formal/Model.lean` | Plan(含时刻戳 steps)、时间化 Escaped(opaque)、FirstEscape 谓词、轨迹、Valid、CrossCards / CrossCardsLe / CrossCardsOC |
| `Q2Formal/Axioms.lean` | 仅公理 A、B、C、D、E(共 5 条, docstring 指向 report.tex / 草稿行号) |
| `Q2Formal/Counting.lean` | ceil、Valid 单调、嵌套⟹不交、记账(全证) |
| `Q2Formal/Main.lean` | 定理 + 强归纳(全证) |
| `Q2Formal/README.md` | 边界声明 + 第 6 节对应清单 |

## 手工对应清单(设计文档第 6 节, 逐条可查)

1. 离散模型 ↔ 题面(速度常数、转向 ≤5°、相切不撞);
2. **Escaped 语义绑定**:`Escaped p k t` = "p 在时刻 t 已逃出第 k 层栅栏";含"不与前 n 层碰撞 ⟺ ∃t, Escaped n t(对合法路径)"的存在量词表述(审计3 收紧版)。嵌套事实 = 公理 C;首次穿越存在性 = 公理 D;首次穿越严格序 = 公理 E——三者同为栅栏几何的古典事实,显式公理化、不在 Lean 内证明;
3. 第一问 = 公理 A 的前缀版(report.tex Theorem 1 的首次逃出前缀形式; v4.5: 闭区间首段 CrossCardsLe p 0 t ≥ 9);
4. 公理 B = report 门到门 4β + 草稿 v0.3 绕行 ≥4β(对齐链 / 上侧可取等 / 下侧 ≥128.3° / 单对界 2(θ₁₂+2β));
5. **全局归约:已有古典证明(草稿 `Q2_global_reduction_draft.md` v0.3 第 3–4 节,六轮审计通过),未机器化**;
6. CrossCards/CrossCardsLe/CrossCardsOC 对折返路径的切分语义(首次逃出时刻 + 闭前缀 [0,t₂] + 左开右闭逐层段 (t_j,t_{j+1}] + 端点归属, v4.5)与题目"首撞前 sup|p|"口径一致。

## 实现注记

- `Plan.cards` 按设计文档第 1 节注释 `-- = steps.length` 实现为定义式访问器: `p.cards = p.steps.length` 为**定义相等**(记账引理需要此相等; 若实现为独立结构字段, 该字段与 steps.length 无任何约束, 定理将不可证)。
- ceil 引理为自证版 `ceilNat : ℝ → ℕ`(存在性 = 阿基米德性, 最小性 = Nat.find; 单调 + 次可加全证)。
- 区间切分约定(v4.5 修订): 闭前缀 `CrossCardsLe p t₁ t₂` 按 `t₁ ≤ τᵢ ≤ t₂` 计数(公理 A), 左开右闭 `CrossCardsOC p t₁ t₂` 按 `t₁ < τᵢ ≤ t₂` 计数(公理 B 与链); 半开 `CrossCards` 保留备用。与古典 ch3 前缀定理/逐层段逐字对齐。

## 环境(可复现)

- Lean 版本: 4.33.0-rc1(elan 工具链 `leanprover/lean4:v4.33.0-rc1`, commit 见 `lean --version`);
- mathlib: rev `8baa3d095e9735e43cf5985d10ae3e9a0f5834d7`(v4.33.0-rc1 对应的 master, 本地 checkout 全路径依赖, 零网络构建)。
  **rev 出处(红线 ④ 追溯)**: 该哈希取自原始 checkout `C:\Users\Donna\mathlib4` 的 `git log -1`, 输出:
  ```
  $ git -C C:\Users\Donna\mathlib4 log -1 --format='%H%n%cd%n%s'
  8baa3d095e9735e43cf5985d10ae3e9a0f5834d7
  Fri Jul 17 23:35:31 2026 +0000
  feat(Analysis): use `IsApply` for `GroupSeminorm` (#41560)
  ```
  本项目的 `.lake/packages/mathlib` 是该 checkout 的无 `.git` 路径拷贝(故在其上 `git rev-parse` 不可复验);
  复验请回到原始 checkout 运行上述 `git log -1`。
  依赖 pin: batteries `45337c63`、Qq `ee41917a`、aesop `57d3325b`、Cli `da07ca80`、importGraph `18a90119`、
  plausible `b1c4a69a`、proofwidgets `b1436dc7`、LeanSearchClient `0498c7c0`(均来自 mathlib@8baa3d09 的 lake-manifest)。
- 注: 因本机 GitHub 直连不稳定且无 v4.32.0 官方 release 源码, 采用本机已构建的 rc1 mathlib
  (Std 随 rc1 工具链内置); 版本与提交号如上, 可复现。

## 验收自检(设计文档第 5 节)

> 注(验收 ② 的 grep 作用域): 裸 `grep -R "sorry\|admit"` / `grep -R "axiom"` 会命中 `README.md`、`RESTART_STATUS.md`
> 等文档自检清单行中的字面 "axiom"/"sorry/admit" 字样; 验收实际使用的是限定 `.lean` 源码的命令:
> `grep -R "sorry\|admit" --include="*.lean"`、`grep -R "axiom" --include="*.lean"`、`grep -R "opaque" --include="*.lean"`。

- [x] `lake build` 零错误;
- [x] `grep -R "sorry\|admit" --include="*.lean"` 零命中; `grep -R "axiom" --include="*.lean"` 恰 5 条(A–E); `grep -R "opaque" --include="*.lean"` 恰 1 个(Escaped);
- [x] `#print N_lower_bound` 与设计文档第 3 节逐字一致(`#print` 保留 `∀ p : Plan,` 前缀;`#check` 打印绑定箭头记法,语义同一);
- [x] Lean 版本与 mathlib 提交号可复现;
- [x] PPT 粗体公理/谓词声明与文档逐字一致(见上)。
