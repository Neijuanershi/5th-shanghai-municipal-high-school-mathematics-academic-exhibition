# 第二问 Lean4「保底级」形式化设计文档 v4.4(九轮审计 + 实施反馈修订,设计层终版)

> 版本链:v1 → … → v4.1(Escaped 时间化)→ v4.2(Plan 时刻戳 + FirstEscape)→ v4.3(公理 D、E 定死)
> → **v4.4(本版)**。
> v4.4 变更(实施会话反馈,已批准方案一):**公理 A 改前缀形式**——
> `base_nine : ∀ (p : Plan) (t : ℝ), Valid 2 p → FirstEscape p 2 t → CrossCards p 0 t ≥ 9`。
> 理由:v4.3 的总量形式(`p.cards ≥ 9`)无法与逐层 CrossCards 合成 9 + 4(n−2)(总量下界与总量下界只能取 max,不能相加);
> 前缀形式按首次逃出时刻切分,基例 9 卡与逐层 4 卡落在互不相交的半开区间上,直接相加。
> 古典真值:report.tex Theorem 1 的下界对首次逃出前的前缀成立(7+2 卡严格先于 t₂)。其余条款(B–E、
> 谓词签名、定理语句、验收)一律不动(仍恰 5 条 axiom + 1 个 opaque)。任何实施以本版为准。

---

## 0. 定位(不变)

形式化范围 = "几何公理 → ∀n 下界"的组合层(归纳 + 记账 + 切分)。
几何层以显式公理进入;构造方向(≤)保持经典证明 + 双程序数值复核。
**全局归约已有古典证明(`Q2_global_reduction_draft.md` v0.3 第 3–4 节,六轮审计通过),不进入 Lean。**

---

## 1. 离散模型(`Model.lean`)

```lean
structure Plan where
  heading0 : ℝ
  steps    : List (ℝ × ℝ)   -- (θᵢ, τᵢ): 第 i 张转向卡的转角与生效时刻, τ 严格递增
  cards    : ℕ              -- = steps.length

-- 不透明谓词(语义绑定 README 第 6.2 条): "p 在时刻 t 已逃出第 k 层栅栏"
opaque Escaped : Plan → ℕ → ℝ → Prop

-- 首次逃出谓词(v4.2: Classical.choose 只能取任意见证, 故"首次"必须谓词化)
def FirstEscape (p : Plan) (k : ℕ) (t : ℝ) : Prop :=
  Escaped p k t ∧ ∀ s < t, ¬ Escaped p k s

-- 轨迹重建: 按 τᵢ 分界逐段直线; 第 i 段方向 = heading0 + Σ_{j<i} θⱼ, 速度归一为 1
def pathPoint (p : Plan) (t : ℝ) : ℝ × ℝ := ...   -- 分段定义, 分界点即 steps 的时刻

-- 分层 Valid: 轨迹全程与第 1..n 层格点距离 ≥ 9
def Valid (n : ℕ) (p : Plan) : Prop := ...

-- 区间卡数(v4.2): 半开区间 [t₁, t₂) 内的转向卡数
def CrossCards (p : Plan) (t₁ t₂ : ℝ) : ℕ :=
  (p.steps.filter (fun st => t₁ ≤ st.2 ∧ st.2 < t₂)).length
```

要点:
1. **Escaped 时间化**:定理假设 = `∃ t, Escaped p n t`;首次逃出由 `FirstEscape` 谓词刻画(存在性由公理 D 保证,见第 2 节)。
2. **不相交性(Counting.lean 要证的引理)**:`CrossCards p t₁ t₂` 按半开区间计数;各层区间两两不交由公理 E(首次时刻严格递增)给出。
3. `Valid_n` 单调性:`Valid n → Valid k (k ≤ n)`(Counting.lean 证明)。

---

## 2. 公理(五条 A–E,全部显式、局部、严格弱于定理;含 v4.1 新增的嵌套公理)

```lean
-- 公理 A = 第一问的前缀版(report.tex Theorem 1;v4.4 起总量 p.cards ≥ 9 改为前缀 CrossCards ≥ 9:
-- 古典真值 = 定理 1 的下界对首次逃出前的前缀成立,7+2 卡严格先于 t₂;前缀形式才能与逐层 4 卡不相交相加)
axiom base_nine : ∀ (p : Plan) (t : ℝ), Valid 2 p → FirstEscape p 2 t → CrossCards p 0 t ≥ 9

-- 公理 B = 逐层穿越 ≥ 4 卡(v4.2: 按 FirstEscape 首次时刻陈述, 显式参数版;
-- 古典背书: report 第 459–466 行门到门 4β + 草稿 v0.3 第 3 节绕行 ≥4β)
axiom layer_four : ∀ (p : Plan) (k : ℕ) (t₁ t₂ : ℝ), 2 ≤ k → Valid (k+1) p →
                     FirstEscape p k t₁ → FirstEscape p (k+1) t₂ →
                     CrossCards p t₁ t₂ ≥ 4

-- 公理 C = 栅栏嵌套(不透明谓词 Escaped 的古典事实;README 第 6.2 条绑定)
axiom escape_nested : ∀ (p : Plan) (k : ℕ) (t : ℝ),
                        Escaped p (k+1) t → Escaped p k t

-- 公理 D = 古典事实 F1(v4.3 由 README 事实升级为公理;栅栏几何, 与 C 同源):
-- 首次穿越时刻存在(折线 + 闭栅栏)
axiom first_exists : ∀ (p : Plan) (k : ℕ), (∃ t, Escaped p k t) →
                       (∃ t, FirstEscape p k t)

-- 公理 E = 古典事实 F2(同源): 外栅栏首次逃出严格晚于内栅栏(连续性)
axiom first_order : ∀ (p : Plan) (k : ℕ) (t₁ t₂ : ℝ),
                      FirstEscape p (k+1) t₂ → FirstEscape p k t₁ → t₁ < t₂
```

docstring 指向 report.tex / 草稿的精确位置;**不引用任何第三问文件**。
(注:v4.3 起 F1/F2 即公理 D、E——五条公理 A–E 均为栅栏几何的古典事实,同源同地位,显式声明、不在 Lean 内证明。)

---

## 3. 目标定理(逐字,v4.1)

```lean
theorem N_lower_bound (n : ℕ) (hn : 2 ≤ n) :
  ∀ p : Plan, Valid n p → (∃ t, Escaped p n t) → p.cards ≥ 4 * n + 1
```

构造方向(≤)不形式化,声明:经典构造 `dodge_path(n)`(report.tex)满足 `Valid n ∧ Escaped n ∧ cards = 4n+1`;数值复核净距 = 9.00000(双程序独立)。

---

## 4. 证明骨架(`Main.lean`)

1. **记账引理(全证,零 sorry)**:ceil 单调/次可加;卡数 ≥ Σ⌈段转角/5°⌉;`CrossCards p t₁ t₂` 关于互不重叠的半开区间可加(端点归属由定义 `t₁ ≤ τᵢ < t₂` 直接给出,与古典 3.3 节逐字对齐);`Valid n → Valid k`。
2. **强归纳**:基例 = 由公理 D 取 `FirstEscape p 2 t₂` 见证,对其应用公理 A(前缀形式)得首段 `CrossCards p 0 t₂ ≥ 9`;归纳步:由公理 D 从 `∃t, Escaped p k t` 取得各层(k=2..n)`FirstEscape` 见证,由公理 E 得各层首次时刻严格递增,应用公理 B 逐层得 `CrossCards ≥ 4`;区间 [0,t₂)、[t₂,t₃)、… 两两不交,由半开区间可加性合成 `9 + 4(n−2)`。
3. 算术:9 + 4(n−2) = 4n+1。

**实现期风险点(已预判)**:① F1/F2 已定死为公理 D、E(八轮审计裁定,无悬而未决项);② 半开区间端点卡归属与古典 3.3 节逐字一致(CrossCards 定义 `t₁ ≤ τᵢ < t₂` 已内建)。

---

## 5. 交付物与验收

| 文件 | 内容 |
|---|---|
| `Q2Formal/Model.lean` | Plan(含时刻戳 steps)、时间化 Escaped(opaque)、FirstEscape 谓词、轨迹、Valid、CrossCards |
| `Q2Formal/Axioms.lean` | 仅公理 A、B、C、D、E(共 5 条,docstring 指向 report.tex / 草稿行号) |
| `Q2Formal/Counting.lean` | ceil、Valid 单调、嵌套⟹不交、记账(全证) |
| `Q2Formal/Main.lean` | 定理 + 强归纳(全证) |
| `Q2Formal/README.md` | 边界声明 + 第 6 节对应清单 |

验收:① `lake build` 零错误;② 全项目 `grep -R "sorry\|admit"` 零命中,`grep -R "axiom"` **恰 5 条(A–E)**,`opaque` 恰 1 个(Escaped);③ `#print N_lower_bound` 逐字一致(`#print` 保留声明时的 `∀ p : Plan,` 前缀;#check 打印绑定箭头记法,语义同一,仅作交叉确认);④ README 边界与 PPT 一致;⑤ **PPT 粗体句:"本定理以五条未机器验证的几何公理(A:前缀 9 卡,第一问;B:逐层 4 卡;C:栅栏嵌套;D:首次穿越存在;E:首次穿越严格序)与一个未机器定义的几何谓词 Escaped 为前提"**。

---

## 6. 手工对应清单(形式化外,写入 README,逐条可查)

1. 离散模型 ↔ 题面(速度常数、转向 ≤5°、相切不撞);
2. **Escaped 语义绑定**:`Escaped p k t` = "p 在时刻 t 已逃出第 k 层栅栏";含"不与前 n 层碰撞 ⟺ ∃t, Escaped n t(对合法路径)"的存在量词表述(审计3 收紧版)。嵌套事实 = 公理 C;首次穿越存在性 = 公理 D;首次穿越严格序 = 公理 E——三者同为栅栏几何的古典事实,显式公理化、不在 Lean 内证明;
3. 第一问 = 公理 A 的前缀版(report.tex Theorem 1 的首次逃出前缀形式:首段 CrossCards p 0 t ≥ 9);
4. 公理 B = report 门到门 4β + 草稿 v0.3 绕行 ≥4β(对齐链 / 上侧可取等 / 下侧 ≥128.3° / 单对界 2(θ₁₂+2β));
5. **全局归约:已有古典证明(草稿 v0.3 第 3–4 节,六轮审计通过),未机器化**;
6. CrossCards 对折返路径的切分语义(首次逃出时刻 + 半开区间 + 端点归属)与题目"首撞前 sup|p|"口径一致。

---

## 7. 自检清单

- [ ] 无半径门槛;定理以时间化 `Escaped` 为载,覆盖全部路径类(口袋区/换门/折返);
- [ ] 公理恰 5 条(A 前缀 9 卡(第一问)、B 逐层 4 卡、C 嵌套、D 首次存在、E 首次严格序),各自严格弱于定理,docstring 指向精确位置;
- [ ] 全局归约不进入 Lean,README 第 5 条注明"已有古典证明、未机器化";
- [ ] CrossCards 按半开区间定义,各层区间不交由公理 E 保证;公理 D 提供 FirstEscape 见证,归纳步不依赖 Classical.choose;
- [ ] 零 sorry、5 axiom、1 opaque、`#print` 逐字一致(`#check` 语义一致)、版本可复现;
- [ ] PPT 粗体公理/谓词声明与文档逐字一致。

---

## 8. 古典层状态(已完成,仅供追溯)

`Q2_global_reduction_draft.md` v0.3 经六轮审计:引理 3(约束和 + "之间"前提)、取等构造(ℓ₁∩ℓ₂ 交点,逐点净距 ≥9)、单对界 2(θ₁₂+2β)、折返切分,全部独立重算通过。report.tex 已同步(rem:alt 重写、lem:iso、全局归约、折返句),两遍 xelatex 编译零错误(32 页,验收复核通过)。

---

## 9. v4.5 修订记录(闭区间化, 本版生效)

五路并行审校发现 v4.4 的公理 A 半开前缀形式在"弦上大转角转向"路径下**为假**: 第二问第二层门缝弦上的一次大转角转向(如 s* = 9.13 处一次转向 34.2° 穿出)恰发生在首次逃出时刻 t, 半开区间 [0, t) 只含第一次转向的 7 卡 < 9。v4.4 所引 (eq:exitwin) 双侧窗口论证只排除 ±β 弦上转向, 不排除大转角弦上转向。修订(闭区间化):

1. **公理 A**: `CrossCards p 0 t ≥ 9`(半开)改为 `CrossCardsLe p 0 t ≥ 9`(闭区间 [0,t], 新增谓词, 恰在 t 生效的卡计入);
2. **公理 B**: `CrossCards p t₁ t₂ ≥ 4`(半开)改为 `CrossCardsOC p t₁ t₂ ≥ 4`(左开右闭 (t₁,t₂], 段右端首逃时刻的卡归本段);
3. **记账层**: 新增 `crossCardsOC_add`(左开右闭可加)与 `crossCardsLe_oc_pair_le`(闭前缀 + 开闭链 ≤ 总卡数), 链 `ccChain`/望远镜改 OC 版; 闭前缀与各开闭段拼合无重叠、无遗漏, 合成 9 + 4(n−2) 不变;
4. **古典侧**: report ch3 前缀定理改为闭区间 [0,t₂] 并补弦上转向论证; 折返切分改为"闭前缀 [0,t₂] + 左开右闭逐层段 (t_j,t_{j+1}]", 与 Lean 记账逐字对齐;
5. 公理仍恰 5 条, 全项目零 sorry, `lake build` 8670 jobs 零错误(5 条非致命警告: Counting.lean 86/90/145/149 unused simp + Main.lean 119 化简建议), `#print axioms` 逐字一致。
