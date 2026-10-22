# 自锚效应与定型：长上下文如何把语言模型变成复读机

**The Self-Anchor Effect: longer context makes an LLM more like itself — and less alive**

```
作者：许致嘉（架构与判据设计）／AI 编程助手（代码实现）
状态：实验记录（开放，可直接引用本仓库的 commit 时间作为在先证据）
日期：2026-10-22
★ 本仓库只放**方法 + 判据 + 合成数据**。不含任何真实用户语料。
```

---

## 一句话结论

> **上下文窗口不是"误差的乘数"，而是"自锚的强度"。**
> 窗口越大，模型越像它自己 —— 用词更稳、套话更多、漂移更小。
> 因此"漂移有界"不是因为误差被截断，而是因为它被自己钉住了。

## 我们的发现了一个反直觉的方向

一个很自然的直觉是：**上下文越长，误差累积越多，模型越漂。**
我们按这个直觉做了可证伪的预言，然后**被自己的实验打翻了**：

| 历史窗口 | 套话率（重复句占比） | 用词自相似度（首末两段 Jaccard） |
|---|---|---|
| 8 轮 | **22%** | 0.300 |
| 20 轮 | 29% | 0.331 |
| 50 轮 | **50%** | **0.523** |

```
预言：窗口越大 → 套话率应下降、漂移应上升
实测：两条全部反向 —— 窗口越大，越像自己，越定型
```

**机理**：自回归生成里，上下文的作用是**模板**，不是**乘数**。
模型看到自己刚说过"拖鞋在门口，饭在桌上等你"，下一轮会**模仿这个句式**，
而不是在它上面继续犯错。

> **误差不会相乘，误差会被模仿。**

## 一个立刻可用的"反定型"判据

既然定型来自"逐字自锚"，那么一条判据就能把它按住：

```
判据：与最近 N 句的最大相似度 ≥ 0.72 → 驳回
      驳回时**点名**那一句：「你刚才说过『……』，换一种说法」
      三次仍复读 → 判死
```

| 指标 | 无判据 | **有判据** |
|---|---|---|
| 套话率 | 29% | **2%** |
| 判死 | — | **0 次** |
| 重写 | — | 31 次（60 回合，约一半） |
| 不同说法 | 71/100 | **59/60** |

**代价是延迟，不是命**：点名之后它确实改得动，熔断根本用不上。

## 但我们只治到"词"，没治到"活法"

被鞭子逼出来的新句子：

```
碗在桌上／毛巾在盆里／草稿纸摊着／手柄在桌上／被子掀开／枕头放平／眼药水在桌上
```

**换了物件，没换关系** —— 全部仍是"某样东西 + 给你留着"。

> 判据：**"不重复"和"有新意"是两件事。** 鞭子能逼它换词，逼不出它换活法。

## 另一个可行的方向：把记忆折叠起来

每 N 轮把"旧锚点 + 最近 N 轮"压成一段 ≤150 字的事实锚点，
锚点中**禁止出现任何对话原句**，然后清空 raw 历史：

| 指标 | 无固化 | 有固化 |
|---|---|---|
| 套话率 | 29% | **15%** |
| 锚点字数 | — | 147 → 140 → 140（不膨胀） |
| 上下文 | 持续增长 | 每次折叠后 4 行 |
| 记忆保真（3 个早期事实） | — | **1/3** |

**它压掉一半套话，代价是记忆有损且有偏**：记住主线（考试、失眠），丢掉琐事（食堂、收拾房间）。

> 判据：**"记住主题"和"记住那天"是两件事。**

---

## English summary (for timestamping)

We report a counter-intuitive result about long-context LLM agents.

**Hypothesis tested (and falsified).** We predicted that a longer conversation history
would amplify error accumulation, raising both repetition and drift. We ran the same
persona for 100 rounds at three history windows and measured (a) repetition rate — the
fraction of replies that duplicate an earlier reply — and (b) lexical self-similarity
between the first and last quarters of the session.

**Result.** Both predictions were reversed:

| History window | Repetition rate | Self-similarity |
|---|---|---|
| 8 turns | 22% | 0.300 |
| 20 turns | 29% | 0.331 |
| 50 turns | **50%** | **0.523** |

**Mechanism.** In autoregressive decoding, the context acts as a *template*, not a
*multiplier*: the model imitates its own recent phrasing rather than compounding error on
top of it. **Errors are not multiplied — they are imitated.** Drift is bounded not because
the chain is truncated, but because the model is pinned to itself.

**A cheap countermeasure.** A rejection rule — "max similarity to the last N replies
≥ 0.72 → reject, quote the offending line back, allow 3 attempts" — reduces the repetition
rate from **29% to 2%** with **0 hard failures** (31 rewrites over 60 turns).

**Limitation.** The rule operates at the lexical level only: the model swaps objects but
keeps the same relational template ("something + waiting for you"). *Not repeating ≠
having something new to say.*

**Memory consolidation** (folding history into a ≤150-word fact anchor with no verbatim
quotes) halves repetition (29% → 15%) and bounds the context, but is lossy and biased:
it keeps the main thread (exams, insomnia) and drops one-off events (canteen queue,
tidying the room). *Remembering the theme is not remembering the day.*

---

## 复现

```
code/漂移实验.py      100 轮，每 10 轮问同一句，测漂移与套话率
                      python 漂移实验.py 100 20    # 100 轮，窗口 20
code/记忆固化.py       每 N 轮折叠成锚点，测套话率与记忆保真
                      python 记忆固化.py 60 20
code/反定型实验.py     近 N 句相似度 ≥0.72 即驳回，测套话/判死/重写
                      python 反定型实验.py 60 20
data/                 上述运行产生的原始 JSON（合成场景，无真实用户内容）
```

**依赖**：Python 3.14，仅标准库；模型经 HTTP 调用（任意 chat-completions 兼容端点）。

## 数据与伦理

```
· 全部场景为合成（"高数／食堂／宿舍"一类日常句），**不含任何真实用户对话**。
· 本仓库不包含任何模型权重、任何用户标识、任何真实语料。
· n 很小（每档 1 次运行、60–100 轮），结论应视为方向性而非定量。
```

## 如果要用

```
文档：CC BY 4.0     代码：MIT
引用请带上本仓库的 commit hash（那就是时间戳）。
```
