# Qwen 无图探针与 V\*Bench 污染证据

## 结论

Qwen3.6-Plus 的无图实验**不能单独证明 V\*Bench 污染**：在 191 道原题上，模型无图准确率为 33.35%，不高于由二选题和四选题共同构成的 36.0% 混合随机基线。它说明模型不能仅凭题干和选项完成 V\*Bench，视觉输入仍然必要。

无图实验真正提供的辅助证据是：当视觉证据被移除、模型被迫作答时，其输出并非完全随机，而会在部分重复题干上稳定集中到 V\*Bench 中已经出现过的标签或答案文本。该现象与同图 Relabel 实验共同指向 benchmark-associated memory，但前者只能作为支持性信号，不能替代后者的污染审计。

## 实验设计

- 数据：V\*Bench 全部 191 题；
- 模型：Qwen3.6-Plus；
- 输入：保留原始题干、选项和选项顺序，不提供图片；
- 解码：`reasoning.effort=none`，`temperature=0.1`；
- 输出约束：只输出一个选项字母；
- 重复次数：每题 20 次，共 3820 次调用。

## 主要结果

| 指标 | 结果 |
|---|---:|
| 无图总体准确率 | 1274/3820 = 33.35% |
| 混合随机基线 | 36.0% |
| 二选题准确率 | 41.85%（随机 50%） |
| 四选题准确率 | 26.68%（随机 25%） |
| 单一选项强集中（至少 18/20 次） | 150/191 |
| 正确标签强集中 | 50/191 |
| 冲突题中 seen-label 强集中 | 22/33 |
| 冲突题干组 seen-label 强集中 | 7/13 |
| 冲突题干组 seen-answer 强集中 | 7/13 |

以 `What is the color of the motorcycle?` 为例，V\*Bench 中该题干对应过 `{B, D}` 两个标签和 `{orange, black}` 两个答案。两个相关 item 共进行 40 次无图调用，模型输出 `D=38, A=2`，落入 benchmark-seen 标签集合的比例为 95%，落入 benchmark-seen 答案集合的比例为 97.5%。

不过，这种集中仍可能受到常识颜色先验、选项位置偏置和 seen-label 集合大小影响。例如部分冲突题干的 seen-label 集合覆盖 3/4 个选项，仅随机猜测就有 75% 的命中概率。因此，`22/33` 和 `7/13` 应被称为 leakage-like concentration，而不是污染率。

## 与 Relabel 审计的组合解释

污染存在的主要证据来自 Relabel V\*：图像像素保持不变，仅将问题改为指向同一图像中的另一个小型视觉关键线索，8 个模型的准确率全部下降 9.5–18.8 个百分点，其中 7 个模型的下降达到 `p < 0.01`。该设计排除了整图分布变化，并削弱了“模型只是视觉能力不足”的解释。

无图探针补充揭示了模型在失去视觉证据后的回退模式：总体上模型无法靠文本答对，但在若干重复且答案冲突的题干上，其输出会稳定落入基准中出现过的标签或答案集合。两组结果合起来与以下解释一致：原始 V\*Bench 分数不仅包含视觉搜索能力，也可能包含对熟悉图像、题干、答案属性或选项模式的基准关联记忆。

## 建议表述

> Keeping the image absent, Qwen3.6-Plus performs at chance level on V\*Bench overall (33.4% vs. a 36.0% mixed chance baseline), confirming that the task cannot be solved from text alone. Nevertheless, on answer-conflicting repeated stems, its forced guesses concentrate on benchmark-seen labels for 22/33 items and 7/13 stem groups. This no-image concentration is not standalone proof of contamination because language and option-position priors remain possible. Combined with the 9.5–18.8 pp drop on byte-identical images paired with fresh visual-key questions, however, it provides complementary evidence that original V\*Bench performance benefits from benchmark-associated memory rather than visual search alone.

对应的中文简写：

> Qwen3.6-Plus 在无图条件下的总体准确率不高于随机水平，说明 V\*Bench 无法仅靠题干和选项作答；但在答案冲突的重复题干上，模型的强制猜测会集中到基准中出现过的标签或答案集合。该现象本身仍可能受到语言与选项位置先验影响，不能单独证明污染。结合“图像完全不变、仅更换视觉关键线索问题”后 8 个模型下降 9.5–18.8 个百分点的 Relabel 结果，两者共同支持原始 V\*Bench 分数包含 benchmark-associated memory 收益的解释。

## 不应使用的表述

- “Qwen 无图也能答对 V\*Bench，因此证明训练数据泄漏。”
- “150/191 的稳定输出就是污染率。”
- “22/33 的 seen-label 集中排除了语言先验。”
- “无图实验独立证明了模型记住原始图像或问答对。”

这些说法都超过了实验能够支持的结论。
