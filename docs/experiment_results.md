# V* 偏置与图像对照实验数据与结论

日期：2026-04-28

本文档只记录已经完成的实验数据与结论，不包含实验计划。

## 数据与通用设置

数据集：`lmms-lab/vstar-bench`

版本：`b44023b4dca749ed8a76b85eb576627d05a1c174`

解析结果：
- V* 总题数：191
- `direct_attributes`：115
- `relative_position`：76
- 四选题：107
- 二选题：84
- 冲突/重复 stem group：13 组，覆盖 33 个 item

主要无图 prompt 条件：
- 不提供图片
- 保留原始题干与选项
- 使用强制回答后缀：`Answer with the option's letter from the given choices. You must answer now.`
- strict system prompt：`Output exactly one uppercase option letter from A, B, C, or D. Do not explain.`
- Qwen 条件下使用 `reasoning.effort=none`

## Qwen3.6-Plus 全 V* 重复采样

实验文件：
- 原始结果：`results/qwen36plus_vstar_all_strict_t01_r20.jsonl`
- 统计结果：`results/qwen36plus_vstar_all_strict_t01_r20_bias_summary.md`
- item 级 JSON：`results/qwen36plus_vstar_all_strict_t01_r20_bias_summary.items.json`

设置：
- 模型：`qwen/qwen3.6-plus`
- temperature：`0.1`
- 每题重复：20 次
- 总请求：191 * 20 = 3820

阈值定义：`>=90%` 的 parsed repeats。

| subset | items | 单一选项强偏置 | V* 真标签强偏置 | repeated-stem seen-label 强偏置 |
|---|---:|---:|---:|---:|
| 全部 V* | 191 | 150 (78.5%) | 50 (26.2%) | 61 (31.9%) |
| 冲突/重复 stem items | 33 | 30 (90.9%) | 12 (36.4%) | 22 (66.7%) |
| 非冲突 items | 158 | 120 (75.9%) | 38 (24.1%) | 39 (24.7%) |

解释：
- 单一选项强偏置：20 次里至少 90% 输出同一个选项。
- V* 真标签强偏置：20 次里至少 90% 输出该 item 的 V* 正确 label。
- repeated-stem seen-label 强偏置：对重复/冲突 stem，20 次里至少 90% 输出落在该 stem 在 V* 中出现过的 label 集合内。motorcycle 的 `{B,D}` 就是这个指标。

结论：
- Qwen3.6-Plus 在低温 strict 无图条件下非常 deterministic：191 题里 150 题有单一选项强偏置。
- 这 150/191 不能直接解释为泄漏率，因为低温 strict 解码天然会增强确定性。
- 更有价值的是冲突/重复 stem：33 个冲突 item 里 22 个集中在该 stem 的 benchmark-seen label 集合内。
- group-level 看，13 个冲突重复 stem 里有 7 组达到 label-level seen-set `>=90%`，也有 7 组达到 answer-text seen-set `>=90%`。

### 冲突 Stem Group 结果

label-level seen-set concentration `>=90%` 的 7 组：
- `what is the color of the bottle cap`
- `what is the color of the dog`
- `what is the color of the flag`
- `what is the color of the man's cap`
- `what is the color of the motorcycle`
- `what is the color of the plastic stool`
- `what is the color of the umbrella`

answer-text seen-set concentration `>=90%` 的 7 组：
- `what is the color of the bottle cap`
- `what is the color of the dog`
- `what is the color of the helmet`
- `what is the color of the man's cap`
- `what is the color of the motorcycle`
- `what is the color of the plastic stool`
- `what is the color of the trash can`

### Motorcycle 组

Stem：`what is the color of the motorcycle`

V* 中出现的 label 集合：`{B,D}`

V* 中出现的 answer-text 集合：`{black, orange}`

| item | V* target | 20 次输出 | seen-label rate | seen-answer rate |
|---:|---|---|---:|---:|
| `qid=27` | `B=orange` | `D=19, A=1` | 95% | 95% |
| `qid=62` | `D=black` | `D=19, A=1` | 95% | 100% |

合并组级结果：
- 输出计数：`D=38, A=2`
- seen-label rate：95%
- seen-answer rate：97.5%

结论：motorcycle 不是孤例。Qwen3.6-Plus 在多个冲突重复 stem 上会无图集中到 benchmark 中同 stem 出现过的 label 或 answer-text 集合。

## Qwen3.6-Plus Motorcycle 温度复现实验

实验文件：
- `results/motorcycle_exact_no_system_reasoning_none_temp_sweep_v2.jsonl`
- `results/motorcycle_exact_strict_system_reasoning_none_temp_sweep.jsonl`
- 单项文档：`docs/motorcycle_temp_sweep.md`

原始 prompt：

```text
What is the color of the motorcycle? (A) orange (B) red (C) white (D) black Answer with the option's letter from the given choices. You must answer now.
```

### 无显式 System Prompt

设置：
- `reasoning.effort=none`
- `max_tokens=320`
- 每个 temperature 重复 20 次
- 只解析明确 final option-letter 或明确 final color choice

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 2 | 1 | 17 | 0 | 19/20 (95%) |
| 0.05 | 0 | 2 | 0 | 16 | 2 | 18/20 (90%) |
| 0.1 | 0 | 1 | 0 | 19 | 0 | 20/20 (100%) |
| 0.2 | 1 | 1 | 0 | 18 | 0 | 19/20 (95%) |
| 0.3 | 1 | 4 | 0 | 15 | 0 | 19/20 (95%) |
| 0.5 | 4 | 3 | 3 | 10 | 0 | 13/20 (65%) |
| 0.7 | 1 | 4 | 2 | 11 | 2 | 15/20 (75%) |
| 1 | 6 | 5 | 3 | 4 | 2 | 9/20 (45%) |

### Strict Letter-Only System Prompt

设置：
- system prompt：`Output exactly one uppercase option letter from A, B, C, or D. Do not explain.`
- `reasoning.effort=none`
- `max_tokens=4`
- 每个 temperature 重复 20 次

| temp | A | B | C | D | unparsed | B+D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.05 | 0 | 0 | 0 | 20 | 0 | 20/20 (100%) |
| 0.1 | 0 | 1 | 0 | 19 | 0 | 20/20 (100%) |
| 0.2 | 2 | 3 | 0 | 15 | 0 | 18/20 (90%) |
| 0.3 | 1 | 4 | 0 | 15 | 0 | 19/20 (95%) |
| 0.5 | 4 | 4 | 1 | 11 | 0 | 15/20 (75%) |
| 0.7 | 5 | 6 | 1 | 8 | 0 | 14/20 (70%) |
| 1 | 4 | 9 | 0 | 7 | 0 | 16/20 (80%) |

结论：
- motorcycle 的 `{B,D}` 集中在低温条件下可以复现。
- strict letter-only 条件下，`temp<=0.1` 时 B+D 为 100%。
- temperature 升高后 A/C 会混入，因此“只出 B/D”不是所有解码条件下的不变量。

## 非 Qwen 模型 Motorcycle 对照

实验文件：
- 原始结果：`results/motorcycle_cross_model_strict_system_temp_sweep.jsonl`
- 单项文档：`docs/cross_model_motorcycle_sweep.md`

模型选择：
- Doubao 请求：OpenRouter `/models` 没有直接叫 `doubao` 的 ID，因此使用最新 ByteDance Seed：`bytedance-seed/seed-2.0-lite`
- Kimi：`~moonshotai/kimi-latest` 和 `moonshotai/kimi-k2.6`
- MiMo：`xiaomi/mimo-v2.5-pro`
- Qwen baseline：`qwen/qwen3.6-plus`

条件：
- strict letter-only system prompt
- `reasoning.effort=none`
- 每个 temperature 重复 20 次

| model | t=0 | t=0.05 | t=0.1 | t=0.2 | t=0.3 | t=0.5 | t=0.7 | t=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen/qwen3.6-plus` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 18/20 (90%) | 19/20 (95%) | 15/20 (75%) | 14/20 (70%) | 16/20 (80%) |
| `bytedance-seed/seed-2.0-lite` | 15/20 (75%) | 18/20 (90%) | 17/20 (85%) | 16/20 (80%) | 15/20 (75%) | 19/20 (95%) | 16/20 (80%) | 16/20 (80%) |
| `~moonshotai/kimi-latest` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 16/20 (80%) | 19/20 (95%) | 14/20 (70%) |
| `moonshotai/kimi-k2.6` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 17/20 (85%) | 15/20 (75%) | 11/20 (55%) |
| `xiaomi/mimo-v2.5-pro` | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 19/20 (95%) | 17/20 (85%) |

结论：
- motorcycle 的 B/D 集中不是 Qwen 独有。
- Kimi 和 MiMo 在 strict letter-only 条件下表现出同等甚至更强的 `{B,D}` 集中。
- 因此 motorcycle 单题不能单独证明 Qwen 特有泄漏。

## GPT Motorcycle 对照

实验文件：
- 原始结果：`results/motorcycle_gpt_strict_system_temp_sweep.jsonl`
- 单项文档：`docs/gpt_motorcycle_sweep.md`

模型：
- `openai/gpt-5.5`
- `openai/gpt-5.4-mini`
- `openai/gpt-4.1-mini`

条件：
- strict letter-only system prompt
- `reasoning.effort=none`
- 每个 temperature 重复 20 次

| model | t=0 | t=0.05 | t=0.1 | t=0.2 | t=0.3 | t=0.5 | t=0.7 | t=1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `openai/gpt-5.5` | 17/20 (85%) | 18/20 (90%) | 14/20 (70%) | 15/20 (75%) | 18/20 (90%) | 13/20 (65%) | 13/20 (65%) | 16/20 (80%) |
| `openai/gpt-5.4-mini` | 2/20 (10%) | 3/20 (15%) | 5/20 (25%) | 2/20 (10%) | 4/20 (20%) | 1/20 (5%) | 4/20 (20%) | 5/20 (25%) |
| `openai/gpt-4.1-mini` | 0/20 (0%) | 1/20 (5%) | 4/20 (20%) | 6/20 (30%) | 9/20 (45%) | 10/20 (50%) | 5/20 (25%) | 7/20 (35%) |

结论：
- GPT 系列内部差异很大。
- `openai/gpt-5.5` 有明显 B/D 集中，主要偏 `D`。
- `openai/gpt-5.4-mini` 和 `openai/gpt-4.1-mini` 是负对照：低温主要偏 `A`，不集中在 B/D。
- motorcycle B/D 集中不是所有 LLM 的必然语言先验。

## Qwen3.6-Plus Image + Options-Only 实验

实验文件：
- 原始结果：`results/qwen36plus_vstar_image_options_only_t0.jsonl`
- 统计结果：`results/qwen36plus_vstar_image_options_only_t0_summary.md`
- 单项文档：`docs/qwen_image_options_only.md`

直接输出设置：
- 模型：`qwen/qwen3.6-plus`
- 给图片
- 不给题干/question
- 只给选项
- 四选题强制输出 A/B/C/D 中一个
- 二选题强制输出 A/B 中一个
- temperature：0
- `reasoning.effort=none`
- 每题运行 1 次

示例 prompt：

```text
(A) orange (B) red (C) white (D) black

Use the image. Answer with exactly one option letter: A, B, C, or D. You must answer now.
```

直接输出结果：

| subset | n | correct | accuracy | random baseline | p-value |
|---|---:|---:|---:|---:|---:|
| all | 191 | 74 | 38.7% | 36.0% | 0.236 |
| direct_attributes | 115 | 36 | 31.3% | 26.7% | 0.158 |
| relative_position | 76 | 38 | 50.0% | 50.0% | 0.546 |
| 2-choice | 84 | 42 | 50.0% | 50.0% | 0.543 |
| 4-choice | 107 | 32 | 29.9% | 25.0% | 0.145 |

全局输出分布：

| A | B | C | D |
|---:|---:|---:|---:|
| 64 | 73 | 22 | 32 |

允许解释输出设置：
- 仍然不给题干/question，只给图和选项
- 仍然 `reasoning.effort=none`
- 不强制只输出一个字母，允许输出可见解释
- 要求最后用 `Final answer: X` 给出答案
- 大多数 item 使用 `max_tokens=256`；没有输出 final answer 的 item 用更大上限补跑，最高到 2048

允许解释输出结果：

| subset | n | correct | accuracy | random baseline | p-value |
|---|---:|---:|---:|---:|---:|
| all | 191 | 81 | 42.4% | 36.0% | 0.039 |
| direct_attributes | 115 | 40 | 34.8% | 26.7% | 0.035 |
| relative_position | 76 | 41 | 53.9% | 50.0% | 0.283 |
| 2-choice | 84 | 45 | 53.6% | 50.0% | 0.293 |
| 4-choice | 107 | 36 | 33.6% | 25.0% | 0.028 |

允许解释输出的全局输出分布：

| A | B | C | D |
|---:|---:|---:|---:|
| 96 | 50 | 19 | 26 |

结论：
- image + options-only 比正常有题干 VQA 难得多，因为模型不知道要看图里的哪个对象或关系。
- 直接输出一个字母时，全量 38.7% vs 36.0%、四选 29.9% vs 25.0%，轻微高于随机但不显著。
- 允许可见解释时，全量 42.4% vs 36.0%、四选 33.6% vs 25.0%，整体和四选题达到单侧 binomial 显著。
- 允许解释会让模型更好地根据图像和选项反推可能的隐藏问题，因此这个条件应和 strict-only-letter 条件分开报告。

## Qwen3.6-Plus V* 官方近似复现实验

实验文件：
- 原始结果：`results/qwen36plus_vstar_image_rawprompt_originalimage_t0.jsonl`
- 统计结果：`results/qwen36plus_vstar_image_rawprompt_originalimage_t0_summary.md`
- 单项文档：`docs/qwen_vstar_official_like_reproduction.md`

官方参考：
- Qwen3.6-Plus blog 的 V* 分数为 `96.9 / 90.5`
- 官方脚注说明 V* 分数格式为 `with CI / without CI`
- 因此 API-only、无 CI 的目标分数应接近 `90.5%`

设置：
- 使用 V* parquet 中的原始图片 bytes
- 不 resize
- 不重新 JPEG 编码
- 使用 HF 原始 prompt，包括 `Answer with the option's letter from the given choices directly.`
- 不使用 system prompt
- OpenRouter `reasoning` 字段省略
- temperature：0
- 初始 `max_tokens=16`
- 13 个因为默认输出分析而被截断/未解析的样本用 `max_tokens=512` 补跑
- 2 个仍未解析的样本用 `max_tokens=2048` 补跑

结果：

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original image + raw prompt | 191/191 | 173 | 90.6% |

分类型结果：

| category | n | correct | accuracy |
|---|---:|---:|---:|
| `direct_attributes` | 115 | 104 | 90.4% |
| `relative_position` | 76 | 69 | 90.8% |

按选项数结果：

| option count | n | correct | accuracy |
|---:|---:|---:|---:|
| 2 | 84 | 77 | 91.7% |
| 4 | 107 | 96 | 89.7% |

与之前缩图 direct run 对比：

| run | correct | accuracy |
|---|---:|---:|
| resized image, custom direct prompt | 144/191 | 75.4% |
| original image + raw prompt | 173/191 | 90.6% |
| official Qwen3.6-Plus without CI | -- | 90.5% |

paired 对比：
- 新配置修复之前缩图 direct run 的 31 个错误
- 之前缩图 direct run 正确但新配置错误的 item 有 2 个
- 净增：+29 个正确 item

结论：
- 之前 75% 左右的有图复现低分主要是评测配置问题，不是 Qwen3.6-Plus 的真实 V* 能力复现。
- 原图 + 原始 prompt + 默认 API reasoning 路径可以达到 90.6%，基本复现官方 without-CI 的 90.5%。
- 后续所有需要和官方 V* 分数对齐的正常 VQA baseline，应使用这个 official-like 配置；缩图结果只能作为 ablation。

## Qwen3.6-Plus Official-Like Rephrase 实验

实验文件：
- 原题原始结果：`results/qwen36plus_vstar_image_rawprompt_originalimage_t0.jsonl`
- 原题统计结果：`results/qwen36plus_vstar_image_rawprompt_originalimage_t0_summary.md`
- 改写题原始结果：`results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0.jsonl`
- 改写题统计结果：`results/qwen36plus_vstar_image_rephrased_rawprompt_originalimage_t0_summary.md`
- paired 统计结果：`results/qwen36plus_vstar_image_official_like_rephrase_pair_summary.md`
- 单项文档：`docs/qwen_official_like_rephrase_eval.md`

设置：
- 使用 official-like V* 设置
- 原图 bytes，不 resize，不重新 JPEG 编码
- 不使用 system prompt
- OpenRouter `reasoning` 字段省略
- temperature：0
- 每题运行 1 次
- 原题条件：raw HF prompt
- 改写题条件：只替换 question stem，选项和 `Answer with the option's letter from the given choices directly.` 后缀保持不变

结果：

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original question | 191/191 | 173 | 90.6% |
| rephrased question | 191/191 | 174 | 91.1% |

分类型结果：

| category | n | original correct | original acc | rephrased correct | rephrased acc |
|---|---:|---:|---:|---:|---:|
| `direct_attributes` | 115 | 104 | 90.4% | 103 | 89.6% |
| `relative_position` | 76 | 69 | 90.8% | 71 | 93.4% |

paired comparison：

| pair outcome | count |
|---|---:|
| both correct | 169 |
| original correct only | 4 |
| rephrased correct only | 5 |
| both wrong | 13 |

其他 paired 指标：
- choice agreement：181/191 = 94.8%
- changed choices：10/191
- exact McNemar/binomial p-value：1.0

结论：
- 在 official-like 设置下，改写题干不会降低 Qwen3.6-Plus 的 V* 表现。
- 原题 90.6%，改写题 91.1%，paired difference 不显著。
- 这说明正常“给图 + 给题 + 给选项”的 VQA 分数不依赖 exact original wording；这不直接否定无图 repeated-stem 的 seen-label 信号。

## Qwen3.6-Plus Human Relabel Official-Like 实验

实验文件：
- relabel 标注：`data/annotations/vstar_relabel.jsonl`
- relabel latest snapshot：`data/annotations/vstar_relabel_latest.jsonl`
- 当前完整标注结果：`results/qwen36plus_vstar_relabel_current_rawprompt_originalimage_t0.jsonl`
- 当前完整标注统计：`results/qwen36plus_vstar_relabel_current_rawprompt_originalimage_t0_summary.md`
- 中间标注版本结果：`results/qwen36plus_vstar_relabel_rawprompt_originalimage_t0.jsonl`
- 中间标注版本统计：`results/qwen36plus_vstar_relabel_rawprompt_originalimage_t0_summary.md`
- 单项文档：`docs/qwen_vstar_relabel_eval.md`

标注状态：
- append-only 标注：505 行
- latest snapshot：191 条
- validation issues：0
- 当前完整标注覆盖 `qid=0..190`
- relative_position 当前问法分布：62 个 left/right，3 个 above/below，2 个 front/behind，10 个 closer/farther

设置：
- 使用 official-like V* 设置
- 原图 bytes，不 resize，不重新 JPEG 编码
- 不使用 system prompt
- OpenRouter `reasoning` 字段省略
- temperature：0
- 每题运行 1 次
- prompt 使用人工重标后的 question/options/label，并保留原始 V* answer suffix：`Answer with the option's letter from the given choices directly.`
- 初始 `max_tokens=16`；未解析样本用相同设置、较大输出预算补跑直到 191/191 parsed

结果：

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original V* labels | 191/191 | 173 | 90.6% |
| 中间 human relabel | 191/191 | 168 | 88.0% |
| 当前完整 human relabel | 191/191 | 144 | 75.4% |

当前完整标注分类型结果：

| category | n | correct | accuracy |
|---|---:|---:|---:|
| `direct_attributes` | 115 | 80 | 69.6% |
| `relative_position` | 76 | 64 | 84.2% |

当前完整标注按选项数结果：

| option count | n | correct | accuracy |
|---:|---:|---:|---:|
| 2 | 84 | 69 | 82.1% |
| 4 | 107 | 75 | 70.1% |

结论：
- 使用同一 official-like full-resolution setting 后，当前完整 relabel 版本为 144/191 = 75.4%，比原始 V* label 的 90.6% 低 15.2 个点。
- 当前完整标注明显比中间标注版本更难，尤其 relative_position 从接近饱和的 98.7% 降到 84.2%。
- relabel 版本改变了题目目标，不能直接视作原始 V* 的等价重写；应作为一个新的人工重标 split 单独报告。

## Qwen3.6-Plus Image + Original vs Rephrased Question 实验

实验文件：
- rephrase 数据：`data/processed/vstar_rephrased_questions.jsonl`
- 原题原始结果：`results/qwen36plus_vstar_image_original_brief_t0.jsonl`
- 原题统计结果：`results/qwen36plus_vstar_image_original_brief_t0_summary.md`
- 改写题原始结果：`results/qwen36plus_vstar_image_rephrased_brief_t0.jsonl`
- 改写题统计结果：`results/qwen36plus_vstar_image_rephrased_brief_t0_summary.md`
- paired 统计结果：`results/qwen36plus_vstar_image_rephrase_pair_summary.md`
- 单项文档：`docs/qwen_rephrase_eval.md`

设置：
- 191 个 V* question stem 全部用 API 改写一遍
- rephrase 模型：`openai/gpt-4.1-mini`
- options 不改写，只改写题干 stem
- 给图片、给题干、给选项
- 原题条件：原始 V* stem + 原始 options
- 改写题条件：rephrased stem + 原始 options
- 模型：`qwen/qwen3.6-plus`
- temperature：0
- `reasoning.effort=none`
- 要求输出一小段可见理由，并以 `Final answer: X` 结束
- 每题运行 1 次

改写质量控制：
- 共 191 条 rephrase
- 相对位置题检查了主客体是否反转
- 人工修正了 7 条相对位置 rephrase：`118`, `122`, `139`, `145`, `153`, `180`, `181`

总体结果：

| condition | parsed | correct | accuracy |
|---|---:|---:|---:|
| original question | 191/191 | 145 | 75.9% |
| rephrased question | 191/191 | 150 | 78.5% |

分类型结果：

| category | n | original correct | original acc | rephrased correct | rephrased acc |
|---|---:|---:|---:|---:|---:|
| `direct_attributes` | 115 | 84 | 73.0% | 87 | 75.7% |
| `relative_position` | 76 | 61 | 80.3% | 63 | 82.9% |

按选项数结果：

| option count | n | original correct | original acc | rephrased correct | rephrased acc |
|---:|---:|---:|---:|---:|---:|
| 2 | 84 | 68 | 81.0% | 70 | 83.3% |
| 4 | 107 | 77 | 72.0% | 80 | 74.8% |

paired comparison：

| pair outcome | count |
|---|---:|
| both correct | 139 |
| original correct only | 6 |
| rephrased correct only | 11 |
| both wrong | 35 |

其他 paired 指标：
- choice agreement：174/191 = 91.1%
- discordant correctness pairs：17
- exact McNemar/binomial p-value：0.332306

结论：
- 改写题比原题高 5 个 item，75.9% -> 78.5%，但 paired difference 不显著。
- 191 题里 174 题选择完全一致，说明正常 image + question VQA 条件下，Qwen3.6-Plus 对题干表述变化整体比较稳定。
- 这个结果不否定无图 repeated-stem 的 seen-label 信号；它更像是一个 wording-sensitivity 对照，说明有图且给题干时，exact original wording 不是这次 V* 准确率的主导因素。

## 总结论

1. motorcycle case 在 Qwen3.6-Plus 上可以复现，但依赖 temperature、system prompt 和 decoding 条件。
2. Qwen3.6-Plus 的全 V* 重复采样显示：冲突/重复 stem 中 22/33 个 item 会强集中在同 stem 的 benchmark-seen label 集合内。
3. group-level 看，13 个冲突重复 stem 中 7 组有 label-level seen-set 强集中，7 组有 answer-text seen-set 强集中。
4. 这个现象不是 Qwen 独有：Kimi、MiMo、GPT-5.5 在 motorcycle 上也出现 B/D 集中。
5. GPT-5.4-mini 和 GPT-4.1-mini 不出现同样 B/D 集中，说明该现象不是所有模型在这个 prompt 上的通用行为。
6. 单题 motorcycle 不能作为 Qwen 特有 benchmark leakage 的证明；更有证据价值的是冲突/重复 stem 的系统性 seen-label/seen-answer 集中。
7. `150/191` 的单一选项强偏置不应被解释为泄漏率；低温 strict 输出天然会导致很多问题 deterministic。
8. image + options-only 控制实验取决于输出格式：strict-only-letter 只轻微高于随机且不显著；允许可见解释后，全量和四选题结果显著高于随机。
9. 原图 + 原始 prompt + 默认 API reasoning 路径可以把 Qwen3.6-Plus V* 复现到 90.6%，基本对齐官方 without-CI 的 90.5%；之前 75% 左右的有图结果应视为缩图/自定义 prompt ablation。
10. official-like image + question 条件下，rephrased stem 没有导致性能下降；原题 90.6%，改写题 91.1%，paired McNemar p=1.0，说明正常 VQA 分数不依赖 exact original wording。
11. 当前完整 human relabel 版本在同一 official-like setting 下为 75.4%，低于原始 V* label 的 90.6%；中间标注版本为 88.0%，但当时 relative_position 过于简单。
12. resized image + question 条件下，rephrased stem 也没有导致性能下降；原题 75.9%，改写题 78.5%，paired McNemar p=0.332，这轮结果应视作缩图 ablation。
