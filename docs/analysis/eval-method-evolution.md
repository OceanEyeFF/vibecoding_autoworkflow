---
title: "Repo-local Eval 研究推进步骤"
status: active
updated: 2026-03-24
owner: aw-kernel
last_verified: 2026-03-24
---
# Repo-local Eval 研究推进步骤

> 目的：把当前仓库评测与调优方法后续怎么继续推进写清楚，但只作为实施路线和边界说明，不把它写成已经承诺落地的大而全平台。

## 一、当前判断

当前仓库已经有一条最小可运行的 `Memory Side` 评测线：

- `toolchain/evals/memory-side/` 提供稳定测量面
- `toolchain/scripts/research/memory_side_autoresearch.py` 提供最小 runner
- `codex` 与 `claude` CLI 都已经接进当前 runner

但这条线还只是单主题、最小闭环。

对接下来的实施路线，当前更合适的方向不是：

- 先补完整正式评测集
- 先做大量人工复核
- 先抽象成跨主题大平台

而是：

- 先让 `Claude` 与 `OpenAI API` 都能参与自动评测
- 先建立 `AI-only` 的自动判定链路
- 先把 `Memory Side` 作为单主题试点压实
- 等自动链路稳定后，再从运行日志反推正式评测集

`Task Interface` 仍然重要，但它更适合放到第二波，而不是和第一条自动化试点线并行推进。

当前默认假设还应再补一条：

- 第一波评测优先覆盖 `CLI / text-stream` 场景

原因不是因为 `CLI` 更“先进”，而是因为当前仓库实际面对的执行入口和宿主交互本来就更接近：

- `Codex CLI`
- `Claude CLI`
- `OpenAI API`

因此，第一波更适合优先选择：

- 有清晰命令入口
- 有稳定文本输出
- 有固定测试入口
- setup 成本可控

的 repo fixtures，而不是先从 GUI 或重服务依赖场景起步。

## 二、评测对象拆分

当前更适合从两个维度同时拆评测对象。

### 按主线主题拆

- `Memory Side`
- `Task Interface`

这条拆法对应仓库当前的主线分区，适合决定“先测哪条线、后测哪条线”。

### 按能力行为拆

- `write`
- `read`
- `update`
- `refinement`

这条拆法不替代 partition，而是作为评测维度补充：

- `write`
  - 更接近 `Knowledge Base` 与 `Writeback & Cleanup`
- `read`
  - 更接近 `Knowledge Base` 与 `Context Routing`
- `update`
  - 更接近 `Writeback & Cleanup` 的 mismatch 与回写判断
- `refinement`
  - 更接近 `Task Contract` 对讨论的收束质量

因此，当前更稳的写法不是把仓库主线改写成“write/read/update 系统”，而是：

- 用 partition 定义真相边界
- 用能力维度定义 benchmark 观察面

## 三、当前方法来源

后续研究可以参考两类来源，但要分层使用：

1. `karpathy/autoresearch`
   - 主要借它的研究方法
   - 核心是固定 `program`、固定场景、固定 schema 或机械指标、重复试验、统一比较
2. `uditgoenka/autoresearch`
   - 主要借它的 Claude 侧执行壳、loop、guard、logging 思路
   - 不直接把整套命令面、插件体系和大 catalog 作为本仓库主线

另外，`OpenAI API` 在这里的角色也要单独说明：

- 它是一个可并列比较的推理 backend
- 它不是本仓库新增的 repo-local skill host
- 它更适合参与自动验证与对照，而不是承载本仓库部署层语义

这里的重点不是“照搬外部仓库”，而是把其中可复用的方法压进本仓库现有分层里，再用双后端运行结果反推本仓库真正需要的测量面。

## 四、固定边界

在继续推进研究方法时，下面这些边界不能漂移：

- `docs/knowledge/` 仍然是真相层，不是实验层
- `product/` 仍然是 canonical skill 与 adapter 源码层
- `toolchain/evals/` 仍然只保存稳定测量面
- `toolchain/scripts/research/` 仍然只保存研究执行与评分入口
- `.agents/` 与 `.claude/` 仍然只是 deploy target
- `.autoworkflow/` 仍然只是运行产物目录

因此，评测方法的演进只能先从 `analysis`、`evals`、`scripts/research` 和 adapter 实现层推进，不能反过来改写真相层定义。

## 五、推进原则

后续完善评测时，优先遵守下面几条：

1. 先做自动 gate，再做正式评测集
2. 先做单主题试点，再做跨主题扩展
3. 先让 `Claude` 与 `OpenAI API` 都能跑，再谈更复杂抽象
4. 先让 AI 自动判定通过 / 失败 / 分歧，再考虑人工分析
5. 先压实 bounded tuning，再考虑更长的 autoresearch loop
6. 每一步都要能回答“如果今天停在这里，是否仍然自洽”

这里的默认前提是：评测尽量不依赖人工逐条介入。

这并不意味着“只信一个模型的主观判断”，而是意味着：

- 先用确定性规则做硬门槛
- 再让多个 AI backend 相互对照
- 分歧时保留 `inconclusive`，而不是强行给出通过结论

这里还应补一条：

- 第一波不追求大而全，而优先让少量 `CLI-first` fixture 在双后端上稳定复现

如果某一步必须先引入大量人审、先写完整评测集、或先重构成大平台才能开始，通常说明步子迈大了。

## 六、评测方法细节

在当前路线下，评测方法更适合拆成 3 层，而不是只用一个总分掩盖问题。

### 1. hard gate

负责拦截显性失败，例如：

- schema 不合法
- 输出结构漂移
- 禁止字段出现
- 路径越界
- deploy dry-run 失败

### 2. behavioral tasks

负责测单个能力行为，例如：

- 事实写入
- 基于记忆的读取与引用
- mismatch 更新
- 任务收束与优化

这一层更适合回答“这个 skill 或对象在一个任务片段中是否稳定”。

### 3. long-chain tasks

负责测多步连续任务，例如：

- 先写入
- 再改代码
- 再更新记忆
- 再接新需求
- 再收束或再回写

这一层更适合回答“系统是否能跨多个步骤保持一致，而不是越做越乱”。

当前更合适的顺序是：

- 先让 hard gate 稳定
- 再让单步 behavioral tasks 稳定
- 最后再把 long-chain tasks 提升为主要压力场景

## 七、指标体系

当前文档不应只停在 `pass / fail / inconclusive`，还应补一组更细的观察指标。

更值得先记录的是：

- fact precision
- fact recall
- redundant fact rate
- drift rate
- unnecessary read ratio
- files read
- rounds used
- token 或调用成本
- modified files count
- tests pass rate
- doc consistency

其中优先级最高的不是“写得多不多”，而是：

- 是否写对
- 是否漂移
- 是否无谓重复读取
- 是否破坏已有边界

## 八、建议推进顺序

### Phase 0. 先立自动 gate，不先立正式评测集

这一阶段先不上完整 eval set，只先建立最硬的自动失败条件：

- 固定 `JSON schema`
- 固定输出结构
- 禁止字段或禁止路径
- `adapter_deploy.py --dry-run`
- `path_governance_check.py`

这一阶段的目标是先让大量显性失败能够被脚本自动拦下，而不是先追求“场景覆盖完整”。

这一阶段的完成标志：

- 明显的结构错误、路径越界、部署错误能被稳定判成失败
- 不需要人工逐条看输出结构是否合规

### Phase 1. 先做 `Memory Side` 的双后端执行面

这一阶段先只拿 `Memory Side` 做试点，不并行拉起新主题。

优先完成：

- 同一组场景能被 `Claude` 跑
- 同一组场景也能被 `OpenAI API` 跑
- 两边都写出统一 manifest
- 两边结果都落到统一运行目录

这里的重点不是先做“完整正式评测集”，而是先把自动运行面搭起来。

这一阶段的完成标志：

- `Memory Side` 至少有一组稳定场景能被双后端重复运行
- 运行结果能被统一收集和比较

### Phase 2. 做 `AI-only judge`

这一阶段开始让评测从“能跑”进入“能自动判”。

建议至少分成三层：

1. `rule judge`
   - 负责 schema、路径边界、禁止字段、硬规则检查
2. `cross judge`
   - `Claude` 判断 `OpenAI API` 输出
   - `OpenAI API` 判断 `Claude` 输出
3. `disagreement bucket`
   - 两边判断不一致时，不给通过，标成 `inconclusive`

这一阶段的目标不是追求单一正确裁判，而是尽量减少人工介入，同时避免让单个模型独裁。

这一阶段的完成标志：

- 同一轮运行能自动得到 `pass / fail / inconclusive`
- 大部分明显问题不再需要人工翻日志判定

### Phase 3. 再做 bounded hardening 与调优

只有自动判定链路已经成立后，才值得开始调优。

这一阶段建议保持很窄：

- 固定场景
- 固定轮数
- 单变量改动
- 只调 `program.md`、adapter、backend prompt 或调用参数
- 只有 hard gate 通过且总分提升才保留

这里更接近“有边界的 autoresearch”，而不是无限自演化 loop。

这个阶段仍应主要以单步任务和短链任务为主，不应过早把长链任务当默认入口。

这一阶段的完成标志：

- 至少有一类改动能稳定提升分数
- 调优过程不会破坏当前边界和结构约束

### Phase 4. 从运行日志里反推正式评测集

等双后端运行和自动判定都稳定后，再从真实结果里沉淀本仓库自己的 eval set。

优先从下面这些来源收敛：

- 高频失败
- 高频分歧
- 容易漂移的字段边界
- `Claude` 与 `OpenAI API` 表现差异最大的任务

这一阶段的目标不是“凭空设计完美场景”，而是从真实失败面反推最有价值的稳定测量面。

这一阶段的完成标志：

- 已经能从真实日志中归纳出一批高价值正式场景
- 新评测集能覆盖之前最常见的失败模式

### Phase 5. 再把正式评测集提升为主测量面，并扩到下一主题

这时再把稳定场景正式沉淀到 `toolchain/evals/`，并逐步扩到下一主题。

推进顺序建议仍然是：

1. 先把 `Memory Side` 的正式评测集稳定下来
2. 再把同样的方法移到 `Task Interface`
3. 最后才考虑共享 runner 或跨主题统一框架

这样做可以避免在第一波自动化试点还不稳的时候，同时拉多条主线。

到这一阶段，长链任务才更适合被提升为正式评测集中的关键压力面。

## 九、当前阶段明确不做什么

按现在仓库状态，下面这些都不应当成为近期默认动作：

- 不先补一个看起来很完整但没有真实失败依据的正式评测集
- 不默认要求人逐条审输出
- 不直接把当前脚本重构成跨主题大平台
- 不默认引入无限 loop、自动提交、自动回滚
- 不把外部 `autoresearch` 仓库的命令树照搬进来
- 不在没有 hard gate 和自动 judge 的情况下比较不同 backend 的优劣
- 不在第一阶段同时并行推进 `Memory Side` 与 `Task Interface`

此外，当前也不建议：

- 一上来就为每种语言铺很多 repo fixtures
- 在没有 `CLI-first` 稳定样本前先扩到 GUI 或复杂服务型 repo

## 十、一个更稳的近期落点

如果只看近期最务实的推进，建议顺序是：

1. 先把 `Memory Side` 的 hard gate 压实
2. 让 `Claude` 与 `OpenAI API` 都能跑同一组场景
3. 建 `AI-only judge`
4. 在固定场景上做 bounded tuning
5. 再从日志里沉淀自己的正式评测集

这样做的好处是：

- 每一步都能停住
- 每一步都能自动判断
- 每一步都不会把仓库往宿主工作流系统方向推偏
- 正式评测集来自真实失败面，而不是先验想象

如果后续需要补更重的细节资产，例如基底 repo、任务模板和数据集来源，再读：

- [Repo-local Eval 基底 Repo 与任务模板设计](./eval-fixture-design.md)

## 十一、外部参考

- `karpathy/autoresearch`
  - <https://github.com/karpathy/autoresearch>
- `uditgoenka/autoresearch`
  - <https://github.com/uditgoenka/autoresearch>

## 十二、相关文档

- [Analysis README](./README.md)
- [Repo-local Eval 基底 Repo 与任务模板设计](./eval-fixture-design.md)
- [Memory Side Repo-local Auto Research Loop](./memory-side/memory-side-auto-research-loop.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side/memory-side-eval-baseline.md)
- [Task Interface Repo-local Adapter 评测基线](./task-interface/task-interface-eval-baseline.md)
