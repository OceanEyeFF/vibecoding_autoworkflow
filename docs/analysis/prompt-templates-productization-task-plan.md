---
title: "Prompt Templates 产品化与 Skills 分发任务规划"
status: superseded
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Prompt Templates 产品化与 Skills 分发任务规划

> 当前状态：本文保留为产品化改造的历史任务拆解叶子页，不是当前默认入口。
>
> 当前 `analysis/` 分流入口请先回到 [Analysis README](./README.md)；现行落位与兼容路径以：
>
> - [Prompt Templates Compatibility Shims](../operations/prompt-templates/README.md)
> - [Harness Operations Product Source](../../product/harness-operations/README.md)
>
> 为准。本文继续只保留 lineage / audit 价值。
>
> 原始说明：本文曾作为 `Prompt Templates` 产品化与 Skills 分发改造的 task-plan，承接当时已确认的产品前提，并把阶段判断固定为“进入实施准备”。

> 当前工作分支：`feature/prompt-templates-productization`

## 一、当前阶段判断

当前阶段应进入：

- `implementation preparation`

当前阶段不应继续：

- 开放式边界讨论
- 重新争论“这些模板是不是产品对象”
- 继续沿用旧的 `repo-local execution template layer` 解释

允许保留的讨论只限于下面三类阻塞项：

1. 8 个对象的 canonical 名称是否冻结
2. bindings 清单与变量命名是否冻结
3. `docs/operations/prompt-templates/` 迁移后保留什么形态

也就是说：

- 现在不是“继续讨论产品定位”
- 而是“先补齐实施前置决议，再开工”

## 二、规划目标

本规划只解决下面这组已确认任务：

- 把 `docs/operations/prompt-templates/` 下 8 份模板收敛为可分发的产品对象
- 为它们建立稳定的 `product/` 承接位
- 让它们进入当前 Skills 分发链路
- 抽离当前正文里只对本仓库成立的 bindings
- 重写与之冲突的 docs / governance / deploy 基线

本规划不覆盖：

- 新 runtime 的完整实现
- research train loop 的最终接入方案
- 新的 orchestrator 命名体系
- backend-specific prompt 优化策略

## 三、已冻结前提

当前执行前提已经固定为：

1. 全部模板都是产品对象。
2. 这些对象需要进入可分发的 Skills 分发流程。
3. 旧评估文档只保留为 lineage，不再作为当前入口。
4. 当前工作中的 `product family` 工作名先使用：
   - `harness-operations`

## 四、实施前置决议

下面三项已冻结，可直接作为后续实现输入：

### 1. 对象目录与 canonical 名称

冻结后的对象命名与分组如下：

- `Execution Workflow Shell`
  - `simple-workflow`
  - `strict-workflow`
- `Task Intake / Planning`
  - `task-planning-contract`
  - `execution-contract-template`
- `Harness Workflow Shell`
  - `review-loop-workflow`
  - `task-list-workflow`
- `Harness Contract / Governance Audit`
  - `harness-contract-shape`
  - `repo-governance-evaluation`

### 2. 统一 bindings 清单

冻结后的 bindings 清单如下：

- `HARNESS_STATE_FILE`
- `HARNESS_CONTRACT_FILE`
- `SCOPE_GATE_CMD`
- `BACKFILL_CMD`
- `GOVERNANCE_EVAL_CMDS`
- `SCOPE_INCLUDE`
- `SCOPE_EXCLUDE`
- `GATE_SEQUENCE`
- `GOVERNANCE_DIMENSIONS`

说明：

- `${WORKFLOW_ID}`、`${TASK_SOURCE_REF}` 属于运行期占位变量，可继续作为通用 runtime placeholders，不归类为 repo-specific bindings 清单本体。

### 3. `docs/operations/prompt-templates/` 的迁移后策略

冻结结论：

- 保留 shim 指针

选择理由：

- 可以保留旧路径的兼容跳转，避免在 docs / tests / review 流程改造期间产生断链
- 可以明确把 `docs/operations/prompt-templates/` 降级为 compatibility layer，而不是继续冒充 source-of-truth
- 比“完全退役”更稳，比“保留 usage help”更不容易把 repo-local 帮助文档重新写成对象正文

## 五、阶段拆分

### Phase 1：冻结对象与 bindings

目标：

- 把“还能继续讨论什么”收窄成最小集合
- 为后续产品骨架和 deploy 接线提供稳定输入

当前阶段完成定义：

- `T-001`
- `T-002`
- `T-003`

已在本任务规划中冻结，可直接进入 `T-101`

### Phase 2：建立 `product/harness-operations/` 骨架

目标：

- 新增 product partition
- 建立 canonical skill packages、adapter wrappers 与 manifests 承接位

### Phase 3：接入分发链与文档基线

目标：

- 让 deploy/verify 能扫描到新 partition
- 重写与旧解释冲突的 docs / governance 基线

### Phase 4：治理检查与收口

目标：

- 更新 path / semantic / deploy 相关 checks
- 跑最小验证集并完成 writeback

## 六、任务清单

### 任务ID：T-001
任务名称：冻结 8 个对象的 canonical 名称与分组
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 把评估文档中的对象分组收敛成最终可落目录名。

#### 2. 非目标（Non-goals）

- 不改 deploy 脚本
- 不建 product 目录

#### 3. 任务边界（Scope）

- In-scope：
  - `docs/analysis/prompt-templates-productization-and-skill-distribution-assessment.md`
  - 本任务规划文档
- Out-of-scope：
  - `product/`
  - `toolchain/scripts/deploy/`

#### 4. 完成标准（Exit Criteria）

- 8 个对象的 canonical 名称与分组被冻结
- 不再使用目录级模糊称呼替代对象名

### 任务ID：T-002
任务名称：冻结统一 bindings 清单与变量名
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 明确必须从正文中抽离的 repo-specific bindings 和变量命名。

#### 2. 非目标（Non-goals）

- 不实现 runtime
- 不补 backend-specific delta

#### 3. 完成标准（Exit Criteria）

- 有一份明确的 bindings 清单
- 后续 product skeleton 可直接引用该清单

### 任务ID：T-003
任务名称：决定 `docs/operations/prompt-templates/` 的迁移后保留策略
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 明确旧目录是保留 shim、保留 usage help，还是完全退役。

#### 2. 完成标准（Exit Criteria）

- 迁移后策略唯一且明确
- governance tests 可以据此改写，不再依赖猜测

### 任务ID：T-101
任务名称：建立 `product/harness-operations/` 分区骨架
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 新增 `README.md`、`skills/`、`adapters/`、`manifests/` 骨架。

#### 2. 前置依赖（Dependencies）

- `T-001`
- `T-002`

#### 3. 完成标准（Exit Criteria）

- 新 partition 骨架存在
- 目录命名与冻结对象清单一致

### 任务ID：T-102
任务名称：建立 canonical skill packages 与 backend thin wrappers
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 8 个对象建立 canonical `SKILL.md`、`references/` 与 backend adapter wrappers。

#### 2. 前置依赖（Dependencies）

- `T-001`
- `T-002`
- `T-101`

#### 3. 完成标准（Exit Criteria）

- `product/harness-operations/skills/*` 完整存在
- `agents / claude / opencode` 三路 wrappers 能被 deploy 逻辑扫描

### 任务ID：T-103
任务名称：扩展 deploy source roots 与 manifests 承接位
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 让 `adapter_deploy.py` 与 manifests 识别新 partition。

#### 2. 前置依赖（Dependencies）

- `T-101`
- `T-102`

#### 3. 完成标准（Exit Criteria）

- deploy source roots 已覆盖 `harness-operations`
- manifests 承接位已建立

### 任务ID：T-201
任务名称：重写 docs / knowledge / operations 中与旧解释冲突的基线
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 去掉“`docs/operations/prompt-templates/` 仍是 repo-local execution template layer”的主线断言。

#### 2. 前置依赖（Dependencies）

- `T-003`
- `T-101`

#### 3. 完成标准（Exit Criteria）

- 至少同步：
  - `docs/operations/prompt-templates/README.md`
  - `docs/operations/README.md`
  - `docs/knowledge/foundations/docs-governance.md`
  - `docs/knowledge/memory-side/layer-boundary.md`
  - `docs/operations/review-verify-handbook.md`

### 任务ID：T-202
任务名称：重写治理检查与相关测试
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 让 path / semantic / governance 测试不再把旧目录当 source-of-truth。

#### 2. 前置依赖（Dependencies）

- `T-103`
- `T-201`

#### 3. 完成标准（Exit Criteria）

- 至少同步：
  - `toolchain/scripts/test/path_governance_check.py`
  - `toolchain/scripts/test/governance_semantic_check.py`
  - 相关 `test_governance_*`

### 任务ID：T-301
任务名称：执行最小验证集并完成 writeback
任务类型（Task Type）：Review

#### 1. 任务目标（Goal）

- 对前述改造跑最小验证集并确认没有遗漏同步项。

#### 2. 前置依赖（Dependencies）

- `T-202`

#### 3. 验证计划（Validation Plan）

- `python3 toolchain/scripts/test/folder_logic_check.py`
- `python3 toolchain/scripts/test/path_governance_check.py`
- `python3 toolchain/scripts/test/governance_semantic_check.py`
- `python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents`
- `python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude`
- `python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode`
- 对应最小 pytest

#### 4. 完成标准（Exit Criteria）

- 必要检查通过
- 文档、代码、deploy 与治理链路对齐

## 七、执行顺序建议

当前建议严格按下面顺序推进：

1. `T-001`
2. `T-002`
3. `T-003`
4. `T-101`
5. `T-102`
6. `T-103`
7. `T-201`
8. `T-202`
9. `T-301`

说明：

- `T-001` 到 `T-003` 属于实施准备，不属于开放式讨论
- `T-101` 起进入正式改造
- 不建议在 `T-001` 到 `T-003` 未冻结前直接开始大规模迁目录

## 八、当前风险

- 如果 canonical 名称没冻结，后续目录和 adapter wrapper 很容易返工
- 如果 bindings 没冻结，迁到 `product/` 后仍然会把本仓库路径硬编码进产品正文
- 如果旧目录保留策略不明确，governance tests 和 docs rewrite 会反复打架
- 如果先改 deploy、不先改知识层断言，会形成“工具已接线、主线文档仍否认”的冲突状态

## 九、相关文档

- [Prompt Templates 产品化与 Skills 分发评估](./prompt-templates-productization-and-skill-distribution-assessment.md)
- [Prompt Templates 与 Harness Operations Package 评估（历史 lineage）](./prompt-templates-harness-operations-package-assessment.md)
- [Branch / PR 治理规则](../operations/branch-pr-governance.md)
- [Review / Verify 承接位](../operations/review-verify-handbook.md)
