# VLB Deep Dive — How Dynamic V* Differs

Date: 2026-05-04
Source: Yang et al., "Dynamic Multimodal Evaluation with Flexible Complexity by
Vision-Language Bootstrapping," arXiv 2410.08695 v1, ICLR 2025 Oral
(submission 1837, OpenReview `X1OfiRYCLn`). All page/section/table references
below are against arXiv v1.

---

## 1. Motivation — what VLB claims to solve

### 1.1 Static benchmark + 固定复杂度

VLB introduces two paired complaints in Section 1 (paper p.1, Figure 1(b)):

> "existing benchmarks for LVLMs are manually collected. Once constructed,
> they are static with a fixed complexity, making them inadequate to keep
> pace with the rapid development of LVLMs."

"Fixed complexity" 在文中是字面意义的 "题目难度刻在数据里、模型变强后题目不变"。
他们没有把 fixed complexity 操作化为某种 difficulty score；它就是
"benchmark 是常量，模型是变量" 的另一种说法 (Section 1, p.2)。

### 1.2 Data contamination (他们怎么定义)

Section 3 (p.4) 给了两个清晰的可计算定义：

1. **Image-only contamination**: 用 CLIPScore 算 benchmark 图与
   pre-training 图的相似度，超过 0.9 即视为 contaminated。Pre-training 池是
   LAION-100M / CC3M / COCO-Caption。最高观察到 84.46% (image-only)。
2. **Image-text contamination**: 在 CLIPScore>0.9 配对里再用 GPT-4 判断
   "答案是否能从训练图的 caption 里直接推出"。最高 33.13%。

值得一记：他们**没有**区分 memorization / paraphrase leakage / image leakage 这
三种污染机制，把它们都折叠进上面两个 bucket。"Memorization" 这个词在正文里没有
出现；他们就是 "图相似 + 答案从训练 caption 可推" 这套代理指标。

### 1.3 为什么"现有补救方案不够"

VLB 在 Section 2 (Related Work, p.3) 把 paraphrase / MMStar / 手工标注的对策
都简单点过。原文承袭 Zhu et al. 2024b 的 paraphrase 思路放进 ℒ₁，其余
batch 都不展开论证。可以读出的隐含 argument 是 "单一 paraphrase 维度
不够 cover 视觉模态污染"——但这并没有作为对比实验呈现，所以严格意义上
是 motivation 性的论断而不是实证结论。

---

## 2. Method — bootstrapping pipeline

### 2.1 输入 / seed corpus

输入是 VQA 三元组 `Eₛ = (I, Q, A)`（Section 4.1, p.5）。
Seed benchmark 选取：单策略实验上 SEEDBench (10% 子集) / MMBench (30% 子集) /
MME 全集；组合策略实验扩到 MMBench / MM-Vet / LLaVABench 全集
(Section 5.1, p.6)。Appendix A.13 还把 V₁/V₂/V₃ 扩到 COCO-Caption 6 个 VLM
做 image-captioning 任务的健全性检查 (Table 15, p.21)。

### 2.2 全部 bootstrapping operations

**Image-side (3 个，Section 4.2, p.5)：**

| Op   | 难度 | 机制 |
|------|------|------|
| 𝒱₁ Add New Objects     | Hard | GPT-4V 看图后返回 "(object name, bbox)"，bbox→mask，喂给 PowerPaint inpaint |
| 𝒱₂ Remove Existing     | Easy | SAM 切全图 mask→编号→GPT-4V 用 SoM (Set-of-Mark) prompting 选可移除编号→PowerPaint 抹掉 |
| 𝒱₃ Expand (Outpaint)   | Hard | 默认外扩比 r=1.5；ablation 跑 1.25/1.5/1.75/2.0 |

**Language-side (4 个，Section 4.3, p.6)：**

| Op   | 难度 | 机制 |
|------|------|------|
| ℒ₁ Word Substitution   | Hard | 同义词替换，沿用 Zhu et al. 2024b |
| ℒ₂ Sentence Rephrasing | Hard | GPT-4V 角色扮演 (researcher / casual user) 改写 Q |
| ℒ₃ Add Relevant Ctx    | Easy | GPT-4V 生成 image caption 拼到 Q 前；约束"加了 caption 也不能直接答出" |
| ℒ₄ Add Irrelevant Ctx  | Hard | GPT-4V 生成与图相关但与 Q 无关的干扰 caption 拼到 Q 前 |

**改的"复杂度"轴**：𝒱 改的是 visual attention（加噪声物体 / 删掉细节 /
改 FoV），ℒ 改的是 linguistic understanding（同义词陌生度、句法风格、
辅助 vs 干扰 context）。两个轴正交。

### 2.3 Judge / consistency module (Section 4.4, p.7)

- 模型：**InternVL-2** (开源 LVLM)，一个 judge 跑全部策略。
- 输入：原 `Eₛ = (I, Q, A)` + 变体 `E_d = (𝒱(I), ℒ(Q), A)` + "我做了什么修改"的描述。
- 检查：**A 是否对 E_d 仍然正确**——以原 answer 为锚点的 binary "Yes/No"
  adversarial check (借自 MPA, Zhu et al. 2024a)。
- 重试策略：No → 重生 → 最多 5 次 → 仍 No 则**回退原样本**(fall back
  to vanilla)。VLB 不会因"判官说 No"就丢掉 item。
- Ground-truth 设置：**保留原 answer**。Judge 不重新推 GT；它只是
  consistency gate。题面 (Q 或 I) 改了，A 不动。整个方法依赖 "操作不破坏
  A" 这一前提；fail case 被五次重试 + 回退兜底。

### 2.4 复杂度组合 (Section 4.5, p.7)

两类组合：
1. **Paired multimodal**: 1 个 𝒱ᵢ × 1 个 ℒⱼ → 12 种 dyadic 组合。
2. **Multi-strategy**: 同模态内层叠，例如 `E_d = (𝒱₃(𝒱₁(I)), ℒ₄(Q), A)`。

每个原子算子有 hard/easy 标签，组合后的 hard 算子数 0→3 单调地把
benchmark 拉难（Figure 6, p.9）。最难: 𝒱₁+ℒ₄；最易: 𝒱₂+ℒ₃。

### 2.5 已记录的 quality gate / failure mode

- **失败回退**: judge 五连 No 后用原样本，不输出失败 item。
- **A.14 (p.22)** 显式承认 𝒱₁ 之前 fail 率最高，原因是 PowerPaint 加进的
  物体偶尔挡住 Q 相关的核心物体（Figure 15: laptop 挡住 cat、balloon
  挡住人脸）。Judge module 把这些过滤掉，但承认这是 𝒱₁ 的固有 mode。
- A.10 (p.20) 用一个事后分析: 算 `CLIPScore(原图, 新图)`，
  分桶 0.8150 / 0.8776 / 0.9502，新旧 CLIPScore 越远 → 模型 accuracy drop
  越大 (Table 12)。这是事后相关性分析，不是闸口。

---

## 3. Experiments and findings

### 3.1 Models evaluated (Section 5.1, p.7)

GPT-4o, Claude-3.5-Sonnet, DeepSeek-VL, TransCore-M, Monkey-Chat,
LLaVA-NeXT-Vicuna-7B, Qwen-VL-Chat, XComposer2, Yi-VL-34B, InternVL-2.
注意 **InternVL-2 既是 judge 也是 evaluatee**——这是论文里没解决的循环
（reviewer 9VUpWclmsE 在 weakness 3 里点了，rebuttal 没消除）。

### 3.2 Drop magnitudes by complexity tier (Tables 1-3)

- **𝒱₁** drops 4-7%，**𝒱₃** drops 1-4%，**𝒱₂** 持平或微涨 0.3-1.3%
  (Table 1, p.8)。
- **ℒ₁/ℒ₂** drops 0.4-3.6%，**ℒ₃** boost +0.5-+11.5%，**ℒ₄** 最狠
  (e.g. Qwen-VL-Chat on MME 跌 35.08%) (Table 2, p.8)。
- **组合 (Table 3, p.8)**：MMBench 上 𝒱₁+ℒ₄ 把 GPT-4o 从 85.27→79.55%、
  InternVL-2 从 86.78→78.00%；𝒱₂+ℒ₃ 反向：GPT-4o 86.32%、InternVL-2 88.17%。
- **3 个 hard 串联** (𝒱₁+𝒱₃+ℒ₄, Figure 6 p.9) 把 SEEDBench accuracy 再压
  10+ pp。
- **任务敏感度** (Figure 9, p.9)：Instance Interaction、Text Understanding、
  Spatial Relation 在 hard 变体下掉得最厉害。这是 **VLB 在 V*-style 任务上
  最相关的发现**——但他们没在 V*-bench 自身上跑过。

### 3.3 Contamination reduction methodology (Figure 8, p.9)

**实证测量**，不是定义性主张。流程：
1. 取最难变体 (𝒱₁+𝒱₃+ℒ₄ 的 image 部分)。
2. 重新跑 Section 3 的 image-text contamination 检测（CLIPScore 0.9 →
   GPT-4 答案可推性）。
3. 与 vanilla 对比。例：MME 上 image-text contamination 从 33.13% 降到 7.93%。

Appendix A.12 (Tables 13/14, p.21) 给了 image-only 和 text-only 同方向的下降
（例如 LAION 100M vs MMBench: vanilla 0.8574 → ℒ₁..ℒ₄ 0.7846/0.7238/
0.7165/0.6985）。

**注意**：所谓 "降污染" 其实就是 "新生成的图、新生成的句子和 LAION
caption 不再 match 0.9 CLIPScore 阈值"。任何足够强的 perturb 都会做到这一点；
论文没有证明 contamination 下降 = 真实 leakage 下降，这是定义带来的
tautology。

### 3.4 Human evaluation (Appendix A.5, p.16)

**有**。设置：
- 7 个原子策略 × 3 个 benchmark × 100 sample = **2,100 sample**。
- **20 名本科以上学历评审员**，每人独立评，>50% 多数投票判一致；平票判
  ambiguous（不一致）。
- 评审任务：图变体上原 A 是否仍然成立 (𝒱) / 改写后 Q 与原 Q 是否等价 (ℒ)。
- 结果 (Figure 11, p.17)：图策略平均 96%、文本策略平均 97% 通过率。
- A.11 (Table 10, p.18) 还报了 **judge 之前** 的人评通过率作 ablation。
- 但**没有跨组合的 human eval**——reviewer wrZv4nRtkH 的 weakness 2 直接点
  到这一点：error 在多策略串联时是否累积，未测。

---

## 4. Limitations — 文中承认 + 我们能补刀的

### 4.1 作者明说

只有 A.14 (p.22) 一句承认：𝒱₁ 加物体可能遮挡核心元素，需要 judge module
filter。Section 6 "Conclusion and Discussion" (p.10) 没有 Limitations 小节。
也就是论文**没有**正经讲限制。Reviewers (尤其 9VUpWclmsE 评分 6) 抱怨过这一点。

### 4.2 评审已经提出的 (我们应该预期再被问)

来自 OpenReview `X1OfiRYCLn` 公开评审：

1. **Generator-randomness variance** (reviewer wrZv4nRtkH W1)：同一 (I,Q,
   strategy) 两次跑出的 dynamic sample 可以不同，论文没报这个 variance。
   作者 rebuttal 引用 generator 是 deterministic seed，但正文未加。
2. **组合一致性** (wrZv4nRtkH W2)：Figure 11 只评原子策略，没有 𝒱₁+𝒱₃+ℒ₄
   这种串联的人评。
3. **Tool dependence** (wrZv4nRtkH W3, 9VUpWclmsE W3)：换 SAM/PowerPaint/
   GPT-4V 是否结论稳定。论文没做。
4. **LVLM 跌分原因不可解释** (9VUpWclmsE W4)：跌就是跌，论文没区分
   "题真的更难" 和 "生成器留下了 detection shortcut"。
5. **判官循环** (9VUpWclmsE W3 隐含)：InternVL-2 既是 judge 又被评测。
6. **veracity verification** (n8kuPaceeP, weakness 全文核心)：
   "How do we verify the original test cases have been **loyally**
   modified in the way we want?" 即使 A 还成立，新图新题是否真的
   测同一种能力。这是最尖锐的反问。

### 4.3 我们能补的（对评 reviewer 习惯切的角度）

- **Detection-shortcut control 缺失**：VAE-based 修图会留下整图频域
  shift（参见 `generation_design.md` 3.2 引用的 vlm-edit-detect /
  global-artifacts 文献）。论文没用 detection-shortcut probe 过滤
  样本，也没汇报"如果只让 VLM 看图分类 vanilla vs dynamic 的 AUC"这种
  控制实验。
- **Cross-generator transfer 缺失**：他们只跑 PowerPaint。SDXL inpaint /
  FLUX.1 Fill 上结论是否一致——没有。
- **Reproducibility variance 缺失**：正文唯一的 variance 信息就是 Table 12
  那 3 桶 CLIPScore vs accuracy 趋势线。每个 (sample, strategy) 重生 N 次
  对结论的影响 (人话 "重新打榜结论是否漂移") 没数据。
- **Skill preservation 缺失**：他们 verify 的是 "answer 还成立"，
  **不**是 "测同一种能力"。一个原本测 spatial relation 的题，加上
  irrelevant context 后变成测 instruction-following + spatial relation——
  人评说"两题等价"也只是说 A 不变，不证明 skill 维度不变。
- **V* 完全在 VLB 视野之外**：paper 全文未提 V*-bench / GQA / 高分辨率小
  目标视觉搜索。仅在 Figure 9 看到 "Spatial Relation" 类目掉分大，是间接
  证据；正面没做。

---

## 5. Differentiation: Dynamic V* vs VLB

读 `annotation_spec.md` + `generation_design.md` 后核对四个差异点：

### 5.1 Pre-annotated insertable + anchor inventory with metadata

**VLB 完全没有**。VLB 的 𝒱₁ 让 GPT-4V 在生成时**实时**回 "(object,
bbox)"——没有人工 annotation，没有 region 元数据，没有 V*-style 难度筛选
（"小、外围、可遮挡"）。GPT-4V 选的是 GPT-4V 觉得 "可加" 的位置，会被
GPT-4V 自己的 saliency bias 主导（论文 A.14 自己的 fail case：加 laptop
挡 cat、加 balloon 挡 face，就是 GPT-4V 选的位置太靠中央/太大）。

我们的 anchor + insertable schema 引入：
- 强制覆盖每个 V* original target；
- "small / peripheral / cluttered" 选区准则（annotation_spec.md L23-26 /
  L41-43）；
- `position_relation` 八关系作为后续 question generation 的几何输入；
- `allowed_categories / forbidden_categories` 把生成空间限制到 plausible
  本地分布。

**判定**: 真差异，**没法被说成是 re-skin VLB**。VLB 的 𝒱₁ 是 closed-loop
generator 给自己出题；我们是 human-curated metadata-driven generator。
Reviewer 不能合理把这两件事划等号。

### 5.2 FLUX.1 Fill, anchor-aware mask

VLB 用 PowerPaint (Zhuang et al., 2023, SD1.5-based)。FLUX.1 Fill (BFL,
2024-11) 是一代以后的 inpainting model，small-mask 质量明显更好，且我们用
`padding_mask_crop` 控制小目标 — 这一切 VLB 都没做。
**Anchor-aware mask** (在 inpaint mask 里把 anchor 的 overlap 像素清零，
强制保留遮挡关系) 也是 VLB 完全没有的——VLB 的 mask 来自 GPT-4V 的 bbox
直接转换，完全无 anchor 概念。

**判定**: 真差异，但**单凭"换了更新的 inpaint 模型"会被 reviewer 当作
incremental**。要把 anchor-aware mask 拎到台前作为方法贡献：声称
"box-level occlusion preservation 是新机制，VLB 的 occlusion 是 fail mode
(A.14)"。这条能站住。

### 5.3 Programmatic question generation from sampled metadata + bbox geometry (no judge)

VLB 的题面来自 vanilla `(Q, A)` + judge 检查 A 仍成立。**它不生成新题**，
只是在保 A 不变的前提下扰动 I 或 Q。

我们做的是从 metadata + bbox 几何 (transitive closure of `in_front_of`,
左/右/上/下从 xyxy 计算) **程序化合成新题**。其优点：
- GT 是从坐标和 metadata 推出来的，不需要 judge 模块——本质上是
  rule-based 的；
- 没有"answer drift"风险，也不会触发 VLB 的"5 次回退"漏出未过滤样本；
- 题型可枚举（direct attribute / relative position / depth ordering），
  天然带难度刻度。

**判定**: 真差异，且攻击面比 VLB 小——VLB 完全是判官闸口的安全网哲学，
我们是判官 unnecessary 的构造性哲学。Reviewer 不能合理说这是 re-skin。
但要写清楚这条**只在我们 metadata schema 充分丰富时成立**——这是 spec
的主要风险面。

### 5.4 V* high-res small-target focus

VLB 默认在 SEEDBench/MMBench/MME 上跑，全是普通分辨率 multi-task VQA；论文
**全文未提小目标 / 高分辨率**，也没在 V*-bench / V*-Bench-2 上跑。这是
真空地带——我们就是第一个把 dynamic eval 推到 V*-style 高分辨率小目标
search 任务上的工作。

**判定**: 真差异，且是定位优势。但 reviewer 一定会问 "你是否在 VLB
strategies 上也复现了一遍 baseline" — 我们应该把 VLB 的 𝒱₁/𝒱₂/𝒱₃ 在 V* 上
原样复跑一组作为 anchor，然后展示 anchor-aware metadata pipeline 的边
际增益。

---

## 6. 总评 + 投稿建议

### 6.1 哪些 reviewer 会说 "这就是 VLB 重做"

最薄的两条是：

- **"换了更新的 inpaint 模型 (FLUX vs PowerPaint)"** 单点：reviewer
  会说 incremental。必须配 anchor-aware mask + V* 高分辨率才能撑起来。
- **"加了 metadata schema"** 单点：reviewer 可能说 VLB 的 prompt 也算
  "metadata"。我们必须强调 metadata 是**人工预标注 + 跨 run 复用 + 驱动
  question generation**，而不是 generator-time 的 throwaway prompt。

最强的两条是：
- **No-judge programmatic Q generation** (5.3)：与 VLB 哲学正交，
  reviewer 不可能合理说同源。
- **V* small-target high-res 定位** (5.4)：VLB 视野空白。

### 6.2 关键缺口

我们的 spec **暂时没有覆盖** VLB 已经报过的两件事，要补：
1. **跨 generator 健全性 (cross-generator transfer)**：除了 FLUX.1 Fill 主
   pipeline，做一组 SDXL Inpaint 0.1 的复跑（generation_design.md 6.1
   已经预留 fallback），并报告同一 (image, region, attrs) 在两个 generator
   下 LVLM accuracy 是否一致。VLB 没做，我们做了就是直接的方法学贡献。
2. **Detection-shortcut control**：跑一个 "只看图猜 vanilla vs dynamic" 的
   probe 实验 (Qwen / 不同家族 VLM 各一个)，证明 dynamic V* 的 AUC≈0.5。
   VLB 完全没做这一项控制。

### 6.3 minimum 差异化 paragraph

> If we publish, the *minimum* set of differentiators that survives reviewer
> scrutiny is: **(a) human-curated insertable+anchor inventory with V*-style
> small/peripheral/cluttered selection criteria** that VLB's GPT-4V loop
> demonstrably cannot reproduce (A.14 fail-cases are the proof point);
> **(b) programmatic, judge-free question generation from bbox geometry +
> sampled metadata**, which makes ground truth constructive rather than
> verified post-hoc and therefore eliminates the answer-drift fail mode that
> forces VLB to fall back to vanilla after 5 retries; and **(c) the V*
> high-resolution small-target regime that VLB never enters**, supported by
> a same-image VLB-style 𝒱₁ baseline to prove the marginal value of
> anchor-aware metadata. FLUX.1 Fill alone, anchor-aware mask alone, or
> "metadata-driven" alone are each individually too thin and will be read as
> re-skinned VLB; the three combined are not. To pre-empt the strongest
> reviewer attack, we additionally need a cross-generator (FLUX vs SDXL)
> transferability table and an AI-edit detection-shortcut control —
> both gaps VLB also has, but our paper is the one being reviewed.
