---
title: "Autoresearch：收口后中期治理任务清单"
status: superseded
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Autoresearch：收口后中期治理任务清单

> 说明：本文记录过一次“收口后中期治理”的设想；它现在只保留 lineage / audit 价值，用于解释 closeout 收起后曾经考虑过哪些后续治理方向，不再是默认入口，也不驱动当前 autoresearch 实施。

> 入口位说明：本文是 superseded 的 closeout 叶子页，并且仅供 audit / lineage 查阅；当前默认分流入口先回到 [Analysis README](./README.md)，再进入仍 active 的专题研究、phase contract 或 repo-local runbook。本文不是当前默认入口。

## 一、当前阶段定位

当前阶段不再解决 closeout 是否成立。

这个问题已经由下列承接位和验收链回答：

- [`../operations/autoresearch-closeout-decision-rules.md`](../operations/autoresearch-closeout-decision-rules.md)
- [`../operations/autoresearch-artifact-hygiene.md`](../operations/autoresearch-artifact-hygiene.md)
- [`../operations/autoresearch-closeout-entry-layering.md`](../operations/autoresearch-closeout-entry-layering.md)
- [`../operations/autoresearch-closeout-cleanup-and-retained-index.md`](../operations/autoresearch-closeout-cleanup-and-retained-index.md)
- [`../operations/autoresearch-closeout-acceptance-gate.md`](../operations/autoresearch-closeout-acceptance-gate.md)
- `.autoworkflow/closeout/autoresearch-closeout-governance-task-list-20260402/integration-acceptance.json`

当前阶段回答的是另一组问题：

- 哪些治理信息应该继续留在 `docs/knowledge/` 或 `docs/operations/` 作为长期事实
- 哪些治理信息应该前移到 `AGENTS.md` 作为 agent-facing 执行手册
- 哪些行为约束应该继续下沉为 `.codex/config.toml`、rules、skills 或 gate
- 哪些“变更说明”可以从执行证据、测试结果和回写模板自动沉淀，而不是继续写成长文

一句话概括：

- 当前主任务不是“继续补治理文档”，而是“把治理从阅读型进一步压成执行型”

## 二、当前工作原则

### 1. 长期事实保持短而稳定

- `docs/knowledge/` 只保留长期有效的 truth boundary、分层口径、模板和主线说明
- `docs/operations/` 只承接 repo-local runbook、gate、兼容层和维护动作
- 不把本来应该由工具执行的行为规则继续膨胀成说明文档

### 2. 执行规则前移到 agent-facing 入口

- [AGENTS.md](../../AGENTS.md) 继续作为本仓库 agent-facing 的最小执行入口
- 需要被 Codex/Claude/OpenCode 一致遵循的默认流程，应优先写成短规则，而不是藏在长文里
- 如果规则已经稳定到需要被工具读取或直接影响执行，应继续下沉到配置、rules、skills 或脚本

### 3. 先定义执行层 owner，再补配置层

- 只有先在 foundations 里承认某个执行层对象属于哪一层，才能把它真正接入检查链
- 例如如果要正式引入 `.codex/`，必须先处理根目录分层、folder logic allowlist 与 gate 的同步问题

### 4. 变更说明最小化，执行证据优先

- 能从 diff、测试结果、gate 结果、writeback 模板和 retained record 自动回答的问题，不再单独补成长文说明
- 文档应更多回答“长期事实是什么”，而不是重复记录“这次具体做了什么”

### 5. 多 agent 只作为编排能力

- subagent 仍然只在显式需要时使用
- 中期治理的重点是任务拆分、权限边界、验证链和收口定义，不是 agent 数量

## 三、执行顺序

当前建议按下面顺序推进：

1. `M-001`：冻结执行型治理的承接位与根目录层级口径
2. `M-101`：把 `AGENTS.md` 收成更短的 Execution Handbook
3. `M-201`：补齐 Codex project config / rules adapter layer
4. `M-301`：把 review / verify loop 收成固定 checklist、skill 或检查入口
5. `M-401`：把 writeback 与变更说明继续压成证据优先的最小输出
6. `M-501`：把上述执行层对象接入 folder logic 与 acceptance gate

说明：

- `M-001` 是后续任务的共同前置条件
- `M-101` 和 `M-301` 可以并行推进
- `M-201` 只有在 `.codex/` 的层级归属被正式接纳后才应落地
- `M-401` 应建立在模板和 writeback skill 已稳定的基础上
- `M-501` 最后负责把前面任务真正锁进自动检查，而不是只留在文档层

## 四、本轮收口标准

本轮中期治理任务只有在所有工作完成后，统一通过下面这条检查链，才算收口：

1. `python toolchain/scripts/test/folder_logic_check.py`
2. `python toolchain/scripts/test/path_governance_check.py`
3. `python toolchain/scripts/test/governance_semantic_check.py`
4. `python -m pytest toolchain/scripts/test/test_folder_logic_check.py`
5. `python -m pytest toolchain/scripts/test/test_closeout_gate_tools.py`
6. `python toolchain/scripts/test/closeout_acceptance_gate.py --json`

补充判断：

- 根目录、hidden/state/config layer 不得出现未声明对象或未建模 tracked 例外
- `AGENTS.md`、review/verify 承接位、`.codex/` 配置层如果被准入，必须同时进入文档说明和检查链
- 任何一项失败，都按“未收口”处理，不以局部通过替代整体验收

## 五、当前进度（2026-04-03）

当前统计：

- `已完成`：`5 / 6`
- `部分完成`：`1 / 6`
- `未开始`：`0 / 6`

当前可直接复核的基线：

- [AGENTS.md](../../AGENTS.md) 已收成更短的 execution handbook，并明确默认流程 `plan -> implement -> verify -> review -> writeback`。
- [review-verify-handbook.md](../operations/review-verify-handbook.md) 已作为 repo-local review / verify 承接位落盘，并由 [docs/operations/README.md](../operations/README.md) 承接。
- [root-directory-layering.md](../knowledge/foundations/root-directory-layering.md) 与 [folder_logic_check.py](../../toolchain/scripts/test/folder_logic_check.py) 已正式接纳 `.codex/` 为 repo-local execution config layer。
- [path-governance-checks.md](../operations/path-governance-checks.md)、[closeout_acceptance_gate.py](../../toolchain/scripts/test/closeout_acceptance_gate.py) 与相关测试，已经把 `AGENTS.md`、`.codex/`、folder/path/semantic 三类治理检查接进统一 gate。
- `.codex/config.toml` 与 `.codex/rules/repo.rules` 已作为最小 Codex project config / rules adapter layer 落地。
- `task-contract`、`context-entry`、`writeback-log`、`decision-record`、`module-entry` 模板已经存在，说明 writeback 与接口对象已经有结构化承接位。

### A. 当前跟踪结果：执行层承接位

- `M-001`：`已完成`
- foundations 已明确 `docs / product / toolchain / tools / hidden layers / .codex` 的分层、owner 与 folder allowlist。

### B. 当前跟踪结果：Execution Handbook

- `M-101`：`已完成`
- 根级 [AGENTS.md](../../AGENTS.md) 已收成执行手册，并显式承接默认流程、必要同步项与最小 verify / review 入口。

### C. 当前跟踪结果：Codex adapter layer

- `M-201`：`已完成`
- 当前仓库已落地 `.codex/config.toml` 与 `.codex/rules/repo.rules`，并正式纳入根目录治理和 folder logic 检查。

### D. 当前跟踪结果：Review / Verify loop

- `M-301`：`已完成`
- `docs/operations/review-verify-handbook.md` 已把 review / verify loop 收成固定承接位，`AGENTS.md` 也已引用这条复核入口。

### E. 当前跟踪结果：证据优先写回

- `M-401`：`部分完成`
- writeback 模板和 closeout 记录已经存在，但“什么必须写文档、什么只需留 gate/test/backfill 证据”的边界还没有在执行层收成短规则。

### F. 当前跟踪结果：执行层入 gate

- `M-501`：`已完成`
- 现有 gate 已覆盖 `AGENTS.md`、`.codex/`、review / verify 承接位，以及 folder/path/semantic 三类治理检查。

## 六、主任务清单

### A. 执行层承接位

#### M-001：冻结执行型治理的承接位与根目录层级口径

- 要做什么：明确“长期事实 / agent-facing 手册 / project config / rules / gate”分别由谁承接，并把 `.codex/` 是否准入根目录、属于哪一层写清。
- 依赖：无
- 完成标准：
  - foundations 明确 `.codex/` 是否属于正式受控对象
  - 如果准入，`folder_logic_check.py`、相关 README 和 gate 必须同步更新
  - 如果暂不准入，文档必须明确当前不承接 project-level Codex config

### B. Execution Handbook

#### M-101：把 `AGENTS.md` 收成更短的 Execution Handbook

- 要做什么：把当前 `AGENTS.md` 收成更接近执行手册的结构，至少显式回答：
  - 默认工作流是什么
  - 哪些任务先 plan、再实施、再验证
  - 哪些改动必须同步更新文档或检查
  - 退出前至少要跑什么
- 依赖：`M-001`
- 完成标准：
  - `AGENTS.md` 更短、更硬，减少背景解释性 prose
  - agent 进入仓库后，只读根级 `AGENTS.md` 就能知道默认执行流程和收口动作
  - 不再把需要工具执行的细节继续堆进长文

### C. Codex adapter layer

#### M-201：补齐 Codex project config / rules adapter layer

- 要做什么：在 `M-001` 允许的前提下，为 Codex 增加 repo-local project config 与 rules，承接执行层约束，例如：
  - project-scoped `config.toml`
  - command approval / sandbox rules
  - fallback filenames
  - 可复用的 review / check 行为默认值
- 依赖：`M-001`
- 完成标准：
  - 当前仓库不再只靠文档告诉 Codex 怎么做
  - 至少有一层 project-level Codex config / rules 在本仓库内可复用
  - 新增对象已进入 folder logic 与相关运行说明

### D. Review / Verify loop

#### M-301：把 review / verify loop 收成固定 checklist、skill 或检查入口

- 要做什么：把“计划、实现、验证、review、writeback”的最小回路收成固定承接位，而不是继续依赖口头提醒。
- 依赖：`M-101`
- 完成标准：
  - 至少存在一个 repo-local review 指令入口，例如 `code_review.md`、skill、checklist 或等价承接位
  - `AGENTS.md` 明确何时必须 review、何时必须跑测试、何时需要回写
  - review 行为可以被 agent 稳定复用，而不是每次重写提示词

### E. 证据优先写回

#### M-401：把 writeback 与变更说明继续压成证据优先的最小输出

- 要做什么：明确哪些结果必须写回文档，哪些结果只要留下 gate/backfill/test/evidence 即可，不再把变更级说明继续膨胀成长文。
- 依赖：`M-101`、`M-301`
- 完成标准：
  - writeback 模板与技能的使用边界更清楚
  - 对同一类变更，不再同时要求“长文说明 + gate 结果 + 手工摘要”三份重复输出
  - 当前仓库能回答“长期事实写哪里，执行证据留哪里”

### F. 执行层入 Gate

#### M-501：把执行型治理对象接入 folder logic 与 acceptance gate

- 要做什么：把 `M-001/M-101/M-201/M-301/M-401` 产生的对象接入自动检查，包括：
  - root / first-level allowlist
  - tracked exception 白名单
  - 必要的存在性检查
  - review / config / rule 承接位的最小 completeness check
- 依赖：`M-001`、`M-201`、`M-301`
- 完成标准：
  - 执行型治理对象不只是“文档里提到”，而是能被 gate 和测试发现回退
  - closeout acceptance gate 或后续治理 gate 能复跑并稳定失败于结构违规

## 七、当前明确不纳入本清单

- 下一阶段 `autoresearch` runtime、round、mutation、prompt、feedback 等实现重构
- 新一轮 P2 / P3 功能开发计划
- 继续扩写 closeout 背景说明文档
- 为了“看起来完整”补新的大总纲文档
- 无明确 owner 的新根目录对象
- 以“多 agent 更多”作为治理成熟度目标

## 八、已完成的 closeout 基线

下面这些 closeout 任务已完成，不再作为本清单的 active blocker：

- `G-001`：收口边界与例外决策口径
- `G-101`：artifact 最小留删规则
- `G-105`：一次真实清理与最小记录
- `G-201`：目录页型入口与历史 planning 退位
- `G-205`：唯一 closeout 默认入口
- `G-301`：retained artifact 统一登记
- `G-401`：可重复 closeout acceptance gate

这些内容继续由各自的 `docs/operations/` 承接位和验收记录负责，不再在本页重复展开。

## 九、相关文档

- [Autoresearch：收口治理目标](./autoresearch-closeout-governance-goals.md)
- [Analysis README](./README.md)
- [根目录分层](../knowledge/foundations/root-directory-layering.md)
- [路径与文档治理检查运行说明](../operations/path-governance-checks.md)
- [Autoresearch 收口边界与例外决策规则](../operations/autoresearch-closeout-decision-rules.md)
- [Autoresearch closeout 入口层级规则](../operations/autoresearch-closeout-entry-layering.md)
- [Autoresearch artifact 最小留删规则](../operations/autoresearch-artifact-hygiene.md)
- [Autoresearch closeout cleanup and retained index](../operations/autoresearch-closeout-cleanup-and-retained-index.md)
- [Autoresearch closeout acceptance gate](../operations/autoresearch-closeout-acceptance-gate.md)
