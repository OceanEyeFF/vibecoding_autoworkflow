---
title: "Autoresearch P2：单 Prompt、Codex-only 轻量迭代任务规划"
status: superseded
updated: 2026-03-29
owner: aw-kernel
last_verified: 2026-03-29
---
# Autoresearch P2：单 Prompt、Codex-only 轻量迭代任务规划

> 说明：本文基于 `autoresearch-p2-lightweight-single-prompt-codex-loop.md`，把轻量方案拆成可直接交付执行 Agent 的任务单元。它属于 `analysis` 规划文档，不替代 `toolchain/` 当前实现入口，也不替代 `docs/operations/` 的已验证 runbook。

> 当前状态：本文保留为 P2 原始任务拆解记录；当前持续施工优先以 [autoresearch-p2-exrepo-input-hygiene-task-plan.md](./autoresearch-p2-exrepo-input-hygiene-task-plan.md) 和 [docs/operations/autoresearch-minimal-loop.md](../operations/autoresearch-minimal-loop.md) 为准。

## 一、规划目标

本规划只覆盖 P2 轻量方案中的最小落地范围，目标是：

- 把“单 Prompt、`codex -> codex`、轻量 stop rule”拆成可独立执行的任务
- 让每个任务都具备清晰边界、依赖关系和完成标准
- 让后续多 Agent 执行时不依赖隐含上下文
- 把高冲突文件的改动顺序提前规划，降低并行冲突

本规划不覆盖：

- 多 prompt 联调
- Prompt 之外的参数搜索
- proposal engine
- 跨 run study memory
- 多 backend 对比实验

## 二、排序原则

推荐顺序分三层：

1. 先收紧 contract 与 mutation 边界，再实现 stop rule。
2. 先补代码级保护和 smoke，再补文档承接。
3. 文档 runbook 只在代码与 smoke 稳定后再更新，避免写出虚假主线说明。

并行原则：

- 任务 T-001 与 T-002 可以并行。
- 任务 T-003 依赖 T-001，建议后置。
- 任务 T-004 依赖 T-001、T-002、T-003。
- 任务 T-005 最后执行。

## 三、已冻结实现前提

为减少 Batch 1 内部返工，本文先冻结以下实现前提：

- P2 约束真相层由共享 P2 preflight 提供，CLI 入口和 replay 路径都必须复用同一套校验
- contract 只承载两项轻量真相字段：
  - `target_task`
  - `target_prompt_path`
- `codex -> codex` 通过 P2 preflight 解析 suite manifest 后做强校验，而不是先扩成 contract 主 schema 的静态真相
- 通用 `load_contract()` 继续承担通用合同校验，不直接变成 P2 专属 fail-closed 入口
- `mutable_paths` 在 P2 模式下必须规范化为只包含 `target_prompt_path`

固定映射如下：

- `context-routing-skill` -> `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
- `knowledge-base-skill` -> `toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md`
- `task-contract-skill` -> `toolchain/scripts/research/tasks/task-contract-skill-prompt.md`
- `writeback-cleanup-skill` -> `toolchain/scripts/research/tasks/writeback-cleanup-skill-prompt.md`

执行约束如下：

- T-001 负责定义并冻结这套边界
- T-002 只负责消费这套边界，不得自行推导第二套 prompt 目标语义

## 四、Batch 2 状态设计决议

为避免 T-003 在实现时把 round 生命周期扩成新系统，先冻结以下最小决议：

该决议已在 Batch 2 开始前通过“双 SubAgent 调研 + 主执行路径复核”确认，后续实现不得偏离这组最小语义。

- 不新增新的顶层 CLI 子命令
- 不新增新的外层 workflow 或 study-state
- stop rule 只在 `prepare-round` 前执行
- replay 只作为 `decide-round` 内部固定子步骤执行

固定语义如下：

- `prepare-round` 在创建新 candidate 前先做 stop gate
- stop gate 只实现两条：
  - 连续 3 轮没有产生新的 validation champion，则停止创建新 round
  - 所有 active mutation family 都至少尝试 1 次，且 run 内没有任何最终 `keep`，则停止创建新 round
- 这里的 “validation champion” 只按最终升级成功的 champion 计算
- validation 分数相等不算新 champion，必须严格更高才重置计数

replay 固定语义如下：

- replay 不占用新的 `round_number`
- replay 不产生新的 candidate branch/worktree
- replay 复用当前 round 已固定的 candidate commit 和同一套 train/validation suites
- replay 产物写到当前 round 目录下的 `replay/` 子目录
- replay 只在“本轮 provisional `keep` 且 validation 严格高于当前 champion validation”时触发
- replay 执行前必须再次通过同一套 P2 preflight
- replay 复跑前必须清空旧的 `replay/` 子目录

最终决策语义如下：

- `decision.json` 仍只输出最终 `keep` 或 `discard`
- 若本轮 provisional `keep`，但 replay 失败，则最终决策写为 `discard`
- replay 失败时必须在 `decision.json` 中写明：
  - `provisional_decision`
  - `replay.status`
  - `replay.reason`
- champion promotion 只允许发生在 replay 通过之后

这样做的目的有两个：

- 不引入新的 round 类型、pending state 或 replay-round 编号
- 让 `history.tsv`、`feedback-ledger.jsonl`、top-level `scoreboard.json` 继续只消费最终结果，避免新一轮状态分叉

### Batch 2 当前实现状态补记

截至 `2026-03-28`，Batch 2 相关实现和 review-loop 已补齐到以下边界：

- `prepare-round` 的 stop gate 已落地在创建新 candidate 之前
- replay 已固定为 `decide-round` 的内部脚本步骤
- replay 目录会在复跑前先清空，避免陈旧产物污染
- replay 的 non-regression 判定已收紧为“replay validation 不低于本轮 round validation”
- `decide-round` 不做无条件 CLI P2 preflight，但 replay-needed 路径会在 replay 前复用同一套 P2 preflight
- `promote-round` 当前显式执行 P2 preflight

## 五、任务清单

### 任务ID：T-001
任务名称：收紧 autoresearch contract 为单 Prompt、Codex-only 模式
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 `run_autoresearch` 增加一套可验证的运行前约束，使一次 run 只能针对单个 task、单个 prompt 文件运行，并强制使用 `codex -> codex`。
- 结果必须能在 CLI 层 fail closed，而不是依赖人工约定。

#### 2. 非目标（Non-goals）

- 不重写整个 contract schema
- 不引入新的研究数据库或 study 级状态
- 不修改 keep / discard 规则
- 不处理 mutation 细粒度范围校验

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_contract.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_contract.py`
  - 如有必要，`toolchain/evals/fixtures/schemas/autoresearch-contract.schema.json`
- Out-of-scope：
  - `product/`
  - `docs/knowledge/`
  - `.autoworkflow/`
  - `toolchain/scripts/research/autoresearch_mutation_registry.py`
  - `toolchain/scripts/research/autoresearch_round.py`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_contract.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_contract.py`
  - `toolchain/scripts/research/common.py`
- 可选参考文件：
  - `toolchain/scripts/research/README.md`
  - `docs/operations/autoresearch-minimal-loop.md`
- 不需要读取的区域：
  - `product/memory-side/`
  - `product/task-interface/`
  - `.agents/`、`.claude/`、`.opencode/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：局部修改 + 补测试
- 优先在 contract load / CLI 入口层增加强校验，不要把约束分散到多个下游点
- 先补失败用例，再补实现
- 若 schema 改动会扩大侵入，优先采用运行时强校验，保持最小侵入
- 优先把 `target_task -> target_prompt_path` 固定映射做成共享常量或共享校验逻辑，避免 T-002 再重复定义

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：上下文集中在 runner 和 contract，逻辑清晰，主要风险是边界遗漏而不是复杂算法

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：T-002
- 是否属于某个批次（Batch）：Batch 1

#### 8. 风险与不确定性（Risks）

- contract schema 是否需要同步收紧，存在实现策略分歧
- 现有测试夹具可能默认允许多 task / 多 backend，需要同步调整
- 可能遗漏 `baseline` 或 `prepare-round` 的入口一致性校验
- `codex -> codex` 真实约束位于 suite manifest 解析面，而不只在 contract 本体

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行相关 Python 测试文件
- Test：
  - 新增或更新 contract 校验失败用例
  - 新增或更新 `codex -> codex` 强制约束用例
- Runtime：
  - 可做最小 CLI smoke，验证非法 contract 会直接报错
- 是否可以做 smoke test：
  - 可以，轻量 smoke 即可

#### 10. 完成标准（Exit Criteria）

- contract 或 CLI 能明确表达“单 task、单 prompt、`codex -> codex`”约束
- 非法配置会 fail closed
- 相关单测通过
- 不会影响现有非 P2 路径之外的正常 contract 读取逻辑，或影响被明确限制在 P2 入口
- `target_task`、`target_prompt_path` 与 `mutable_paths` 的 P2 语义已经被唯一收口

#### 11. 失败协议（Failure Handling）

- 若发现 contract schema 改动会大面积影响现有 fixture，必须停止并报告影响面
- 若无法在入口层唯一收口校验，必须报告剩余漏口
- 允许请求更多上下文，但不得自行扩大到 mutation / stop rule 任务

### 任务ID：T-002
任务名称：把 mutation 边界收紧为单 Prompt 目标文件
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 让 mutation registry 和 round 校验共同保证：一次 run 内所有 mutation 只能落到 `target_prompt_path` 对应的单个 prompt 文件。
- 结果必须能阻止跨 prompt 修改，而不是只靠文档约定。

#### 2. 非目标（Non-goals）

- 不设计新的 scheduler
- 不修改 stop rule
- 不修改 worker-contract 结构
- 不调整 Prompt 外参数

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/autoresearch_mutation_registry.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/test_autoresearch_mutation_registry.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
- Out-of-scope：
  - `run_autoresearch.py` 中的 stop rule
  - `docs/operations/`
  - `product/`
  - `.autoworkflow/`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - `toolchain/scripts/research/autoresearch_mutation_registry.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/test_autoresearch_mutation_registry.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
- 可选参考文件：
  - `toolchain/scripts/research/common.py`
  - 四个 task prompt 文件
- 不需要读取的区域：
  - `docs/knowledge/`
  - backend adapter 源码

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：局部修改 + 补测试
- 先复用 T-001 已冻结的 `target_task -> target_prompt_path` 映射，不要在本任务内自行重新推导
- 再在 registry canonicalize 和 round diff guardrail 两处都补单文件约束
- 先做小范围验证，确认不会把合法单文件 mutation 误杀

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：任务集中在路径/边界约束和测试覆盖，逻辑复杂度中等

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：T-001
- 是否属于某个批次（Batch）：Batch 1
- 软依赖说明：
  - 若 `target_prompt_path` 尚未在 T-001 中冻结语义，本任务不得自行发明第二套边界定义

#### 8. 风险与不确定性（Risks）

- 若绕开 T-001 的冻结语义，只依赖现有 `mutable_paths` 做“假单文件模式”，后续返工概率高
- round guardrail 与 registry 语义可能出现重复或不一致
- 可能需要明确四个 prompt 文件的 canonical 映射关系

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行 mutation registry / round 相关测试
- Test：
  - 新增单文件合法通过用例
  - 新增跨 prompt 非法失败用例
  - 新增 round 执行时越界 diff 被拦截用例
- Runtime：
  - 可选做一次最小 materialize + run guardrail smoke
- 是否可以做 smoke test：
  - 可以，但以测试为主

#### 10. 完成标准（Exit Criteria）

- mutation 不能跨到第二个 prompt 文件
- registry 和 round 校验语义一致
- 相关测试通过
- 不引入对 docs、adapter、skill wrapper 的误伤限制
- registry 和 round 只消费 `target_prompt_path` 这一单一来源，不保留第二套推导规则

#### 11. 失败协议（Failure Handling）

- 若发现单文件约束必须依赖 T-001 的新字段才能成立，必须标记为对 T-001 的软依赖
- 若 registry 与 round 无法共享同一语义，必须停止并报告分歧点
- 允许请求更多上下文，但不得擅自扩大到 stop rule 或 docs 承接

### 任务ID：T-003
任务名称：实现最小停机规则与新冠军复评
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 P2 路径增加最小 stop rule，使 run 不再只依赖 `max_rounds`。
- 实现 3 条固定规则：
  - 连续 3 轮无 validation 新高则停
  - 所有 active family 至少尝试 1 次且无 keep 则停
  - 新冠军出现后 replay 1 次，不稳定则不升级 champion

#### 2. 非目标（Non-goals）

- 不做复杂 adaptive scheduler
- 不引入模型自由停机判断
- 不实现跨 run 学习
- 不重构 keep / discard 规则本身

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - 如需要，`toolchain/scripts/research/autoresearch_feedback_distill.py`
- Out-of-scope：
  - mutation registry 结构重设计
  - backend 实现
  - `docs/operations/`
  - `product/`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - `toolchain/scripts/research/autoresearch_feedback_distill.py`
- 可选参考文件：
  - `toolchain/scripts/research/README.md`
  - `docs/operations/autoresearch-minimal-loop.md`
- 不需要读取的区域：
  - `product/`
  - adapter deploy 文档

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：局部实现 + 先测后改
- 先决定停机状态应落在何处，是 `prepare-round` 前检查还是 `decide-round` 后更新
- 将 replay 实现成固定脚本步骤，不要交给模型解释
- 先补最小状态跟踪，再补 stop 判定

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：high
- 原因：涉及 round 生命周期、champion 前移和复评时序，逻辑风险高于普通边界校验

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-001
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 2

#### 8. 风险与不确定性（Risks）

- replay 仍会触及当前 round 状态机，是本任务最容易引入回归的部分
- “所有 family 至少尝试 1 次”的判定可能受 registry 当前状态字段限制
- 若 stop gate 统计口径和 history/registry 语义不一致，容易出现误停机或漏停机

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行 round / run_autoresearch 测试
- Test：
  - 新增连续无提升停机用例
  - 新增 family 耗尽停机用例
  - 新增 replay 失败不升级 champion 用例
  - 新增 replay-needed 路径在 replay 前执行 P2 preflight 的用例
  - 新增 replay 复跑前清理旧 `replay/` 产物的用例
- Runtime：
  - 可做最小 bounded run smoke
- 是否可以做 smoke test：
  - 可以，但要先有稳定测试

#### 10. 完成标准（Exit Criteria）

- 三条 stop rule 全部被脚本固定实现
- replay 结果能影响 champion 升级决策
- 至少有一条 CLI 或 round 级测试覆盖每条规则
- 验证通过且没有破坏现有非 P2 主路径的基本 round 生命周期

#### 11. 失败协议（Failure Handling）

- 若 replay 设计会迫使大改 round 状态机，必须停止并报告设计分岔
- 若 stop rule 无法在现有 runtime/round artifact 中表达，必须明确缺口字段
- 允许请求更多上下文，但不得扩展到 full adaptive scheduler

### 任务ID：T-004
任务名称：补齐单 Prompt、Codex-only 路径的 smoke 与回归测试
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 P2 路径补一条真实可执行的最小 smoke，并让测试覆盖单 Prompt、`codex -> codex`、stop rule 三类核心行为。
- 结果必须能作为后续 runbook 的证据，而不是只停留在设计层。

#### 2. 非目标（Non-goals）

- 不改产品代码或 skill 语义
- 不新增复杂 acceptance matrix
- 不编写长期 benchmark 体系

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - `toolchain/scripts/research/test_autoresearch_p1_3_smoke.py`
  - 如有必要，新增一个 P2 smoke 测试文件
  - `toolchain/scripts/research/README.md`
- Out-of-scope：
  - `docs/operations/`
  - `product/`
  - backend 实现本身

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - `toolchain/scripts/research/test_autoresearch_p1_3_smoke.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - `toolchain/scripts/research/README.md`
- 可选参考文件：
  - `run_skill_suite.py`
  - `backends/codex.py`
- 不需要读取的区域：
  - `docs/knowledge/`
  - `product/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：先补测试，再补 README 中的验证说明
- 优先用现有 smoke 测试夹具扩展，不要新造过大的测试基建
- 如果 live Codex smoke 成本过高，至少保证 deterministic smoke 覆盖路径完整

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：主要是测试夹具扩展与覆盖整理，逻辑风险可控

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-001、T-002、T-003
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 3

#### 8. 风险与不确定性（Risks）

- live Codex 相关 smoke 可能受环境影响，不适合默认进入普通测试
- 现有 smoke 主要覆盖 P1.3，P2 路径可能需要新夹具
- README 更新若早于测试稳定，容易写出失真说明
- `decide-round` / `promote-round` / replay 三者的 preflight 边界如果回写不清楚，后续改动容易再次漂移

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行新增/修改的测试文件
- Test：
  - 覆盖单 Prompt 限制
  - 覆盖 `codex -> codex`
  - 覆盖 stop rule 主路径
  - 覆盖 `decide-round` 在 replay 不需要时跳过无条件 CLI preflight
  - 覆盖 `promote-round` 会显式执行 P2 guard path
  - 覆盖 replay-needed 路径会在 replay 前执行 P2 preflight
- Runtime：
  - 可选 live smoke，取决于环境
- 是否可以做 smoke test：
  - 可以，且这是本任务核心

#### 10. 完成标准（Exit Criteria）

- 至少一条最小 smoke 证明 P2 主路径可跑
- 核心回归测试通过
- `decide-round` / `promote-round` / replay 的 P2 preflight 边界有明确自动化覆盖
- README 能描述当前已验证边界
- 未把高成本 live acceptance 错写成默认回归路径

#### 11. 失败协议（Failure Handling）

- 若环境不足以支持 live Codex smoke，必须明确降级为 deterministic smoke
- 若测试夹具复用会误伤现有 P1 smoke，必须分离新测试文件
- 允许请求更多上下文，但不得跳过测试直接更新 runbook

### 任务ID：T-005
任务名称：把 P2 已落地边界承接到 runbook 与入口文档
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 在代码与 smoke 已稳定后，把 P2 的已实现边界写入 repo-local runbook 和脚本入口文档。
- 结果必须让后续执行 Agent 直接知道如何发起单 Prompt、`codex -> codex` 的轻量 run。

#### 2. 非目标（Non-goals）

- 不新增主线知识规则
- 不保留未实现的设计描述
- 不重复复制 `analysis` 内容

#### 3. 任务边界（Scope）

- In-scope：
  - `docs/operations/autoresearch-minimal-loop.md`
  - `toolchain/scripts/research/README.md`
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - `docs/analysis/README.md`
  - 如需要，新增一页 `docs/operations/` 的 P2 runbook
- Out-of-scope：
  - `docs/knowledge/`
  - `product/`
  - 测试代码逻辑

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
  - 本文
  - `docs/operations/autoresearch-minimal-loop.md`
  - `toolchain/scripts/research/README.md`
- 可选参考文件：
  - 已落地测试文件
  - P2 相关实现 PR 或 diff
- 不需要读取的区域：
  - `docs/reference/`
  - `product/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：文档承接
- 先核对实现和测试，再更新 runbook
- 明确区分“已验证主路径”和“仍在 analysis 的设计草案”
- 文档只写已落地事实，不提前写未来能力

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：low
- 原因：主要是承接式文档更新，逻辑风险低，但需要严格克制越权描述

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-004
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 4

#### 8. 风险与不确定性（Risks）

- 容易把设计草案误写成已实现主线
- 容易遗漏 README 入口更新
- 若 P2 只部分落地，runbook 需要明确限制，不可过度概括

#### 9. 验证计划（Validation Plan）

- Static：
  - 检查 Markdown 链接和入口是否完整
- Test：
  - 无需新增代码测试
- Runtime：
  - 对照 smoke 结果核对文档描述
- 是否可以做 smoke test：
  - 不需要，本任务消费前置 smoke 结论

#### 10. 完成标准（Exit Criteria）

- `docs/operations/` 与 `toolchain/scripts/research/README.md` 已能描述 P2 已验证主路径
- `analysis` 文档与承接文档之间关系清晰
- 没有把未实现内容写成主线真相
- 入口 README 已更新

#### 11. 失败协议（Failure Handling）

- 若前置任务未提供稳定测试结论，必须停止，不得提前写 runbook
- 若发现实现与设计存在偏差，必须回报差异，而不是自行修正文档目标
- 允许请求更多上下文，但不得擅自补代码

## 六、任务依赖图

- T-001 与 T-002 是起始任务，二者可并行，但并行前提是先冻结 `target_task / target_prompt_path` 的共享语义。
- T-003 依赖 T-001，因为 stop rule 需要先建立单 Prompt、`codex -> codex` 的入口约束。
- T-004 依赖 T-001、T-002、T-003，因为 smoke 与回归测试必须建立在完整 P2 主路径之上。
- T-005 依赖 T-004，因为 runbook 和入口文档只能承接已验证行为。

简化为：

```text
T-001 ----\
           -> T-003 --\
T-002 ----/           \
                        -> T-004 -> T-005
T-002 -----------------/
```

## 七、推荐执行顺序（Batch 划分）

### Batch 1

- T-001
- T-002

说明：

- 先收紧入口和 mutation 边界
- 这两个任务最适合先行并行

### Batch 2

- T-003

说明：

- 在入口与范围边界稳定后，再补 stop rule 与 replay

### Batch 3

- T-004

说明：

- 统一做 smoke 与回归覆盖，避免测试夹具反复返工

### Batch 4

- T-005

说明：

- 最后做文档承接，确保 runbook 只写已验证事实

## 八、可并行执行的任务组

- 并行组 A：
  - T-001
  - T-002

说明：

- 两者修改面基本分离，但都涉及 P2 边界定义；并行时必须先共享 T-001 冻结后的 `target_task / target_prompt_path` 语义

其余任务建议串行推进。

## 九、高风险任务列表

- T-003：会触及 round 生命周期、champion 前移和 replay 逻辑，最容易引入状态机回归。
- T-001：若 contract 收紧方式选错，可能波及现有 fixture 和非 P2 路径。
- T-002：若 registry 和 round 各自定义单文件语义，容易形成 prepare 能过、run-round 才失败的双轨问题。
- T-004：若 smoke 设计不当，容易把高成本 live 验证错误纳入默认回归。

## 十、推荐整体执行策略

推荐策略是：

1. 先把 P2 当成“对现有 autoresearch 的收窄模式”，而不是新系统。
2. 先由 T-001 冻结 `target_task / target_prompt_path / mutable_paths` 的共享边界语义，再完成 mutation 边界。
3. 再实现最小 stop rule，不要提前做更复杂的 adaptive 演进。
4. 用 smoke 和回归测试证明主路径成立后，再承接到 `docs/operations/` 与 `toolchain` 入口文档。

一句话原则：

- 先控边界，再补停机，再做验证，最后写主线文档。
