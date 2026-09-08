/-
组合层公理 —— 恰 5 条 (设计文档 `Q2_lean_baseline_plan.md` v4.4 第 2 节; 签名逐字照抄, 不增删)。
其中公理 A 为前缀形式(v4.5 修订: 闭区间): `base_nine` 断言第 2 层首次逃出时刻 t 及之前的闭区间 [0, t] 卡数 ≥ 9。

五条公理 A–E 均为栅栏几何的古典事实, 同源同地位: 显式声明、不在 Lean 内证明。
docstring 指向 report.tex / Q2_global_reduction_draft.md 的精确位置; 不引用任何第三问文件。
-/
import Q2Formal.Model

/-- 公理 A = 第一问 (report.tex Theorem 1, 第 341–343 行; 下界论证第 369–391 行:
    净转角 ⌈30.85°/5°⌉ + ⌈8.32°/5°⌉ = 7 + 2 = 9)。
    前缀局部化形式(v4.5 修订: 闭区间): 第 2 层首次逃出时刻 t 及之前的卡数 ≥ 9。
    古典真值: 第一次转向 (≥30.85°, 7 卡) 严格先于 t; "走廊→出射"的第二次转向 (≥2β, 2 卡)
    必发生在 ≤ t 时刻 —— 直线穿行时严格 < t, 恰在门缝弦上转向时 = t。v4.4 的半开形式
    在 "弦上大转角转向" 路径下为假 (合法反例: 走廊下降线直抵门缝弦 s* = 9.13 处一次
    转向 34.2° 穿出, 该卡恰在 t 生效, 半开前缀仅 7 卡 < 9), 故 v4.5 改为闭区间
    CrossCardsLe, 恰在 t 生效的卡计入前缀。 -/
axiom base_nine : ∀ (p : Plan) (t : ℝ), Valid 2 p → FirstEscape p 2 t → CrossCardsLe p 0 t ≥ 9

/-- 公理 B = 逐层穿越 ≥ 4 卡 (v4.2: 按 FirstEscape 首次时刻陈述, 显式参数版;
    v4.5 修订: 区间由半开 [t₁, t₂) 改为左开右闭 (t₁, t₂] —— 段右端 t₂ = 首次逃出
    第 k+1 层的时刻, 该时刻的卡 (含弦上转向) 归入本层段; 每层 4β 转向 (下降+回升,
    或弦上大转角) 全部落在 (t₁, t₂] 内; 与闭前缀 [0, t₀] 拼合无重叠、无遗漏。
    古典背书: report.tex 第 459–470 行门到门 4β + 草稿 v0.3 第 3 节绕行 ≥4β)。 -/
axiom layer_four : ∀ (p : Plan) (k : ℕ) (t₁ t₂ : ℝ), 2 ≤ k → Valid (k+1) p →
                     FirstEscape p k t₁ → FirstEscape p (k+1) t₂ →
                     CrossCardsOC p t₁ t₂ ≥ 4

/-- 公理 C = 栅栏嵌套 (不透明谓词 Escaped 的古典事实; README 第 6.2 条绑定)。 -/
axiom escape_nested : ∀ (p : Plan) (k : ℕ) (t : ℝ),
                        Escaped p (k+1) t → Escaped p k t

/-- 公理 D = 古典事实 F1 (v4.3 由 README 事实升级为公理; 栅栏几何, 与 C 同源):
    首次穿越时刻存在 (折线 + 闭栅栏)。 -/
axiom first_exists : ∀ (p : Plan) (k : ℕ), (∃ t, Escaped p k t) →
                       (∃ t, FirstEscape p k t)

/-- 公理 E = 古典事实 F2 (同源): 外栅栏首次逃出严格晚于内栅栏 (连续性)。 -/
axiom first_order : ∀ (p : Plan) (k : ℕ) (t₁ t₂ : ℝ),
                      FirstEscape p (k+1) t₂ → FirstEscape p k t₁ → t₁ < t₂
