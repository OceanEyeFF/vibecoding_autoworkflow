---
title: "Prompt Templates 产品化与 Skills 分发评估"
status: superseded
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Prompt Templates 产品化与 Skills 分发评估

> 当前状态：本文保留为 `prompt-templates` 产品化判断的 lineage 叶子页，不是当前默认入口。
>
> 当前入口请先回到 [Analysis README](./README.md)；若需要现行对象落位与兼容路径，优先进入：
>
> - [Prompt Templates Compatibility Shims](../operations/prompt-templates/README.md)
> - [Harness Operations Product Source](../../product/harness-operations/README.md)
>
> 本文继续只保留产品化判断和分发边界的 lineage / audit 价值。
>
> 目的：在“`docs/operations/prompt-templates/` 下全部模板都是产品对象，并需要纳入当前 Skills 分发流程”这一前提已经确认之后，固定对象分组、source of truth 落点、分发接线范围、repo-specific bindings 抽离要求与改造出口条件。

## 一、当前已确认前提

当前讨论里，下面结论已经不是开放问题：

1. `docs/operations/prompt-templates/` 下的全部模板都属于产品对象。
2. 这些对象需要变成可分发、可安装、可维护的 Skills 分发资产。
3. 当前把它们视为 `repo-local execution template layer` 的解释不再成立。

这意味着：

- 后续设计不再沿用“包本体 vs repo-local 实例化层”作为主判断框架。
- 当前仓库里把这些模板定义为 repo-local scaffolds 的文档与治理检查，都需要被同步改写或退役。
- 目录迁移只是结果，不是本议题的核心；核心是先把产品对象、分发边界和 bindings 结构说清楚。

## 二、本文评估范围

本文只回答下面问题：

- 这 8 份模板各自是什么产品对象
- 它们更适合被组织成哪类 product family / partition
- 哪些 repo-specific 内容必须从正文中抽离成 bindings 或 metadata
- 现有 Skills 分发链路需要补哪些 source roots、manifests、docs 与 tests
- 旧评估文档为什么不再适合作为当前入口

本文不直接做下面动作：

- 不直接修改 `toolchain/scripts/deploy/adapter_deploy.py`
- 不直接迁移 `docs/operations/prompt-templates/`
- 不直接新增 backend adapter wrapper
- 不直接决定最终 runtime contract 的字段细节

## 三、模板对象清单与建议分组

当前 8 份模板更适合按“产品对象族”而不是按当前 `docs/operations/` 目录理解。

本轮冻结后的 canonical 名称与分组如下。

### 1. Execution Workflow Shell

- `simple-subagent-workflow.md`
- `strict-subagent-workflow.md`

冻结后的对象名：

- `simple-workflow`
- `strict-workflow`

共同特点：

- 负责定义单任务执行流程壳
- 依赖 path governance、scope、gate 与失败协议
- 不是 `Task Contract` 真相本体，而是消费上游合同的执行型对象

### 2. Task Intake / Planning

- `task-planning-contract.md`
- `execution-contract-template.md`

冻结后的对象名：

- `task-planning-contract`
- `execution-contract-template`

共同特点：

- 面向任务拆分、执行合同与规划产物生成
- 与 `Task Contract` 紧密相邻，但并不等于 `Task Contract`
- 更像 task-intake / planning family，而不是纯文档模板

### 3. Harness Workflow Shell

- `review-loop-code-review.md`
- `task-list-subagent-workflow.md`

冻结后的对象名：

- `review-loop-workflow`
- `task-list-workflow`

共同特点：

- 负责带状态、带 gate、带 integration 阶段的 workflow shell
- 当前正文里硬编码了 state 文件、contract 文件与 gate/backfill 命令
- 是最接近“harness operations”对象族的一组

### 4. Harness Contract / Governance Audit

- `harness-contract-template.md`
- `repo-governance-evaluation.md`

冻结后的对象名：

- `harness-contract-shape`
- `repo-governance-evaluation`

共同特点：

- 一个定义 harness contract shape
- 一个定义治理审计与评分 prompt
- 都已经超出“repo-local 使用说明”的范围，更接近可复用产品资产

## 四、当前判断：应新增独立 product partition

当前更合理的方向，不是把这 8 份对象塞回现有 `memory-side` 或 `task-interface`，而是新增一个独立 product partition。

建议工作名：

- `product/harness-operations/`

当前这样判断的理由：

- 现有 deploy 主线只认 `memory-side` 与 `task-interface`
- 这 8 份对象既不是 `Memory Side` 的三技能，也不是 `Task Contract` 本体
- `Task Contract` 当前明确不负责 runtime orchestration 或多步 workflow shell

因此，把它们定义成单独的 `Harness Operations` 产品族，比强行扩写现有 partition 更干净，也更符合“全部模板都是产品对象”的前提。

## 五、建议的 source-of-truth 落点

如果本议题继续推进，建议的最小落点如下：

```text
product/
  harness-operations/
    README.md
    skills/
      review-loop-workflow/
      task-list-workflow/
      simple-workflow/
      strict-workflow/
      task-planning-contract/
      execution-contract-template/
      harness-contract-shape/
      repo-governance-evaluation/
    adapters/
      agents/
      claude/
      opencode/
    manifests/
```

其中各 skill 目录建议最小包含：

- `SKILL.md`
- `references/entrypoints.md`
- `references/prompt.md`
- `references/bindings.md` 或等价 schema 文件

对应 backend adapter 继续沿用当前 thin wrapper 模式：

- `Canonical Source`
- `Backend Notes`
- `Deploy Target`

## 六、必须抽离的 repo-specific bindings

虽然当前不再把这些对象定义成“repo-local 实例化层”，但它们正文里仍然包含大量只对本仓库成立的绑定点。这些内容如果不抽离，分发后仍无法跨仓库复用。

至少需要抽离下面几类 bindings：

### 1. 状态与 contract 文件路径

例如：

- `.autoworkflow/state/harness-review-loop.json`
- `.autoworkflow/state/harness-task-list.json`
- `.autoworkflow/contracts/<workflow_id>.json`

### 2. gate / backfill / governance 命令

例如：

- `python toolchain/scripts/test/scope_gate_check.py ...`
- `python toolchain/scripts/test/gate_status_backfill.py ...`
- `python toolchain/scripts/test/governance_assess.py ...`
- `python toolchain/scripts/test/repo_governance_eval.py ...`

### 3. scope 与排除目录示例

例如 `harness-contract-template.md` 里当前写死的：

- `product/**`
- `docs/operations/prompt-templates/**`
- `toolchain/scripts/test/**`
- `.autoworkflow/`
- `.agents/`
- `.claude/`
- `.opencode/`

### 4. 本仓库特有的 review / verify 口径

例如：

- 当前 `rule / folders / document / code / overall` 评分维度
- 当前 Scope / Spec / Static / Test / Smoke 关卡命名

本轮冻结为统一 bindings 变量或最小 schema：

- `${HARNESS_STATE_FILE}`
- `${HARNESS_CONTRACT_FILE}`
- `${SCOPE_GATE_CMD}`
- `${BACKFILL_CMD}`
- `${GOVERNANCE_EVAL_CMDS}`
- `${SCOPE_INCLUDE}`
- `${SCOPE_EXCLUDE}`
- `${GATE_SEQUENCE}`
- `${GOVERNANCE_DIMENSIONS}`

补充说明：

- `${WORKFLOW_ID}` 与 `${TASK_SOURCE_REF}` 继续作为 runtime placeholders 使用，但不算 repo-specific bindings 冻结项。

## 七、对现有 Skills 分发链路的影响

当前分发链路是：

- `product/*/adapters/<backend>/skills/*`
- `toolchain/scripts/deploy/adapter_deploy.py`
- repo-local / global skill target

所以如果 `harness-operations` 要进入同一条分发链，最小影响面至少包括：

### 1. Deploy

- `adapter_deploy.py` 的 `PRODUCT_PARTITIONS` 需要增加 `harness-operations`
- `source_roots_for()` 才会扫描到新 partition 的 adapter source roots

### 2. Product manifests

- 新增 `product/harness-operations/manifests/`
- 明确后续全局安装、市场分发或包元数据的承接位

### 3. Backend adapters

- `agents`
- `claude`
- `opencode`

三路都要补齐对应 wrapper source roots，至少保证 deploy / verify 能看见这组对象。

## 八、对文档与治理基线的影响

一旦确认这些模板都是产品对象，当前仓库里下面这些断言就不再成立，必须同步调整：

### 1. `docs/operations/prompt-templates/README.md`

当前把本目录定义为：

- `repo-local prompt / contract 模板`
- `repo-local execution template 簇`

后续应改成：

- 历史承接位 / shim / usage help
- 或直接退役并回链到新的 `product/harness-operations/`

### 2. `docs/operations/README.md`

当前把 `prompt-templates/` 列为 `repo-local execution template layer` 路径簇之一。

后续不能再把这些产品对象放在该分类下。

### 3. `docs/knowledge/foundations/docs-governance.md`

当前明确写着：

- `docs/operations/prompt-templates/` 只作为 repo-local execution template layer

这条需要被改写，因为它与当前产品化前提已经冲突。

### 4. `docs/knowledge/memory-side/layer-boundary.md`

当前把 `docs/operations/prompt-templates/` 固定为 repo-local execution template layer。

这同样需要翻案或重新限定作用域。

### 5. `docs/operations/review-verify-handbook.md`

当前复核清单要求：

- `docs/operations/prompt-templates/` 仍只承接 repo-local execution templates

这条在后续改造阶段不再成立。

## 九、对治理检查与测试的影响

当前治理检查已经把 `docs/operations/prompt-templates/` 当作固定对象。后续至少要同步下面几类检查：

### 1. `governance_semantic_check.py`

当前硬编码：

- `PROMPT_TEMPLATES_DIR = "docs/operations/prompt-templates"`

而且还检查该目录下每个模板必须回链 knowledge。

如果 source of truth 迁到 `product/harness-operations/`，这条检查就需要改写成新的对象族规则，或者改成只检查 shim / usage help。

### 2. `path_governance_check.py`

当前把 `docs/operations/prompt-templates/README.md` 视为 required path 的一部分。

如果该目录降级为 shim 或不再承担主入口，required paths 与入口判断都要同步更新。

### 3. `test_governance_*`

当前多处测试直接拿 `docs/operations/prompt-templates/*.md` 当样本路径。

后续要么更新到新落点，要么保留最小 shim 文件满足旧测试迁移期需求。

## 十、当前不建议做的事

在 source of truth、bindings 与 partition 没定稳之前，当前不建议：

- 直接把 8 份模板机械搬到 `product/`
- 直接把名字固定成 `Harness-Orchestrator`
- 直接把 `.autoworkflow` 和本仓库 gate 命令继续留在正文里
- 直接承诺这组对象都进入 research train loop

## 十一、当前建议路径

当前最稳的推进顺序如下：

1. 先确认新 partition 的工作名和对象边界。
2. 给 8 个对象分别确定 canonical 名称与分组。
3. 抽出统一 bindings 清单，先固定变量与 schema。
4. 冻结 `docs/operations/prompt-templates/` 为“保留 shim 指针”的迁移策略。
5. 设计 `product/harness-operations/` 的最小目录骨架。
6. 再进入 deploy / docs / governance tests 的联动改造。

## 十二、出口条件

在进入正式改造前，本议题至少应满足下面出口条件：

- 明确新 product partition 的工作名
- 明确 8 个对象的 canonical 名称与分组
- 明确统一 bindings 清单
- 明确 `docs/operations/prompt-templates/` 的保留策略
- 明确 `adapter_deploy.py` 的 source root 扩展方案
- 明确哪些 governance docs 与 tests 需要同步改写

当前冻结结论：

- 8 个对象名与分组已冻结
- bindings 清单已冻结
- `docs/operations/prompt-templates/` 迁移后保留策略已冻结为 `shim`

## 十三、为什么旧评估文档不再适合作为当前入口

旧文档 `prompt-templates-harness-operations-package-assessment.md` 的核心判断建立在下面前提上：

- `docs/operations/prompt-templates/` 是 repo-local execution template layer
- “包本体 vs repo-local 实例化层” 是主判断框架
- 可以先沿着 `operations-only` 与 `generic distributable package` 两条路线评估

而当前讨论已经确认：

- 全部模板都是产品对象
- 目标不是 `operations-only`
- repo-local template 解释不再是当前主线

因此，旧文档应只保留为上一轮问题 framing 的 lineage，不再作为 active 研究入口。

## 十四、相关文档

- [Docs 文档治理基线](../knowledge/foundations/docs-governance.md)
- [项目 Partition 模型](../knowledge/foundations/partition-model.md)
- [Task Contract 基线](../knowledge/task-interface/task-contract.md)
- [Memory Side 层级边界](../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../knowledge/memory-side/skill-agent-model.md)
- [Prompt Templates 与 Harness Operations Package 评估（历史 lineage）](./prompt-templates-harness-operations-package-assessment.md)
- [Prompt Templates](../operations/prompt-templates/README.md)
- [Deploy / Verify / Maintenance](../operations/deploy/README.md)
