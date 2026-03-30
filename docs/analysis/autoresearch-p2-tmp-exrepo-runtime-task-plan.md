---
title: "Autoresearch P2：TMP Exrepo 运行时迁移与维护脚本任务规划"
status: active
updated: 2026-03-30
owner: aw-kernel
last_verified: 2026-03-30
---
# Autoresearch P2：TMP Exrepo 运行时迁移与维护脚本任务规划

> 说明：本文基于当前 `exrepo input hygiene` 施工记录与最新决策收敛结果，固定一条新的两阶段执行路径：
>
> 1. 保留现有 `candidate worktree` 生命周期
> 2. 把 exrepo 执行根迁到 OS 级 `/tmp`
> 3. 通过绝对路径重写后的 materialized suite 驱动 `baseline / run-round / replay`
> 4. 单独补一份 `/tmp` exrepo 维护脚本，负责初始 clone 与 reset
>
> 本文目标是产出可直接分发给执行 Agent 的任务单元，不要求执行阶段再补隐含设计。

## 一、规划目标

本规划只解决当前这组已确认边界：

- 不废弃现有 `worktree` 生命周期
- 不再让 `candidate worktree` 自己解析仓库根目录下的 `.exrepos`
- 把 exrepo 运行时位置固定到 OS 级 `/tmp`
- 用绝对路径重写后的 suite 作为 `baseline / round / replay` 的统一执行输入
- 新增一个显式维护脚本来管理 `/tmp` 下的 exrepo clone 与 reset

本规划不覆盖：

- `worktree_manager.py` 的生命周期重构
- worker contract schema 重设计
- selector / feedback ledger / replay 规则改模
- prompt 文本迭代
- `.exrepos/` 内容本身的批量修复

## 二、两阶段执行策略

### Phase 1：最小改动接入 TMP Exrepo 运行时

目标：

- 在不改 `worktree` 主链的前提下，把 exrepo 输入从“当前工作树下的 `.exrepos`”切换为“`/tmp` 下的稳定 exrepo 根”
- 让 `baseline / run-round / replay` 统一消费 materialized suite
- 把 authority 继续留在 `.autoworkflow/`，不把 `/tmp` 当真相层

### Phase 2：补齐 TMP Exrepo 维护脚本

目标：

- 提供独立脚本管理 `/tmp` exrepo 的 clone / reset / prepare
- 明确 destructive action 的边界，只允许触达 `/tmp` exrepo 根
- 把维护步骤从 `autoresearch` 主流程里解耦出来，避免 runner 侧职责膨胀

## 三、任务清单

### 当前进度（2026-03-30）

- `T-001` 已完成并入库：
  - 已新增 `toolchain/scripts/research/exrepo_runtime.py`
  - 已补 `test_exrepo_runtime.py` 与 `test_run_skill_suite.py` 的 deterministic 覆盖
  - helper contract 已冻结：稳定 `/tmp` exrepo 根目录、deterministic materialized suite 路径、`repo` 与 `prompt_file / eval_prompt_file` 的绝对路径重写、且不原地修改源 suite
- `T-002` 已完成并入库：
  - `baseline`、`run-round`、`replay` 已统一消费 materialized suite
  - materialized suite 已落到 run-local artifact，而不是 authority 状态
  - P2 preflight 仍锚定原始 contract suite
  - `worktree_manager.py`、authority 字段、decision / replay 规则未改
- `T-003` 已完成并入库：
  - `test_exrepo_runtime.py` 已覆盖 YAML / JSON suite 的路径重写与源 manifest 不变性
  - `test_run_skill_suite.py` 已覆盖 materialized suite 在 direct runner 侧的绝对路径消费
  - `test_run_autoresearch.py` 已覆盖 baseline 对 materialized suite 的消费与原始 contract suite preflight 锚点
  - `test_autoresearch_round.py` 已覆盖 round / replay lane 的 suite 物化，以及 replay 执行失败后的 discard 语义
- `T-004` 已完成并入库：
  - `docs/operations/autoresearch-minimal-loop.md`
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
  - `docs/analysis/README.md`
  - `docs/analysis/autoresearch-p2-exrepo-input-hygiene-task-plan.md`
  - 已对齐 `/tmp exrepo + materialized suite` 的当前运行事实，并把旧的 hygiene 规划退役为 lineage
- Phase 2 当前已有窄前体实现，但不等于任务合同已闭环：
  - `toolchain/scripts/research/manage_tmp_exrepos.py` 已存在，并可按 `exrepo.txt` 执行 repo-list 驱动的 clone / pull / reset-then-pull
  - `toolchain/scripts/research/test_manage_tmp_exrepos.py` 已存在，并覆盖 parse、clone、pull、reset-then-pull 与主入口失败返回码
  - 这些现状只能证明 Phase 2 已有前体，不足以自动判定 `T-101` 或 `T-102` 已按本文任务合同完成
- `T-103` 已完成并入库，但只承接当前已实现的维护脚本形状：
  - 已新增 `docs/operations/tmp-exrepo-maintenance.md`
  - 已更新 `docs/operations/README.md`
  - 已更新 `docs/operations/research-cli-help.md`
  - 已更新 `toolchain/scripts/research/README.md`
  - 当前文档只描述 repo-list 驱动的真实 CLI，不把 `init / reset / prepare` 未来形状写成已完成事实
- 当前仍待完成：
  - `T-101` TMP exrepo 维护脚本的 full-contract 收口
  - `T-102` TMP exrepo 维护脚本的 git 安全与回归测试收口

### 任务ID：T-001
任务名称：实现 TMP Exrepo 根目录与 suite 物化 helper
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 提供一套共享 helper，能稳定计算 OS 级 `/tmp` exrepo 根目录，并把原始 suite 物化为可执行的 materialized suite。
- 物化结果必须把 `repo` 改写为绝对路径，并保持 `prompt_file / eval_prompt_file` 的绝对路径语义一致。
- 结果必须可供后续 `baseline / run-round / replay` 直接消费，而不依赖 candidate worktree 下的 `.exrepos`。

#### 2. 非目标（Non-goals）

- 不实现 exrepo 的 clone / fetch / reset
- 不改 `worktree_manager.py`
- 不改 worker contract schema
- 不改 selector、decision、replay 规则
- 不原地修改输入 suite 文件

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/common.py`
  - 新增 `toolchain/scripts/research/exrepo_runtime.py`
  - 如有必要，`toolchain/scripts/research/run_skill_suite.py` 中与共享 resolver 对接的最小改动
- Out-of-scope：
  - `toolchain/scripts/research/worktree_manager.py`
  - `toolchain/scripts/research/autoresearch_worker_contract.py`
  - `toolchain/evals/fixtures/schemas/`
  - `.exrepos/` 目录内容
  - `.autoworkflow/` 现有运行产物

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/common.py`
  - `toolchain/scripts/research/run_skill_suite.py`
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `docs/operations/autoresearch-minimal-loop.md`
- 可选参考文件：
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
- 不需要读取的区域（如果有）：
  - `product/`
  - `docs/knowledge/`
  - `toolchain/scripts/deploy/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：共享 helper 新增 + 小范围接线
- 先冻结 helper contract，再实现文件重写逻辑
- suite 物化结果建议采用确定性路径与命名，避免后续 round/replay 再做路径猜测
- 先做单个 suite 的小范围 deterministic 验证，再交给 `autoresearch` 主流程消费

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：high
- 原因：这是整条方案的共享路径合同，后续多个任务都依赖它；一旦 helper 语义漂移，后续 integration 与脚本都会返工

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 1 / Phase 1

#### 8. 风险与不确定性（Risks）

- `/tmp` 根路径命名不稳定，导致后续脚本与 runner 之间出现第二套路径规则
- helper 如果把 `/tmp` 路径写成 authority，会污染恢复语义
- YAML/JSON suite 重写时可能遗漏 `prompt_file / eval_prompt_file`
- 若 materialized suite 路径设计不稳定，后续测试会很脆

#### 9. 验证计划（Validation Plan）

- Static：
  - `python3 -m py_compile` 覆盖新增 helper 文件
- Test：
  - 新增 helper 级 deterministic 测试
  - 覆盖 YAML 和 JSON suite 的绝对路径重写
- Runtime：
  - 可以做单 suite 物化 smoke test，不需要跑 live backend
- 是否可以做 smoke test：
  - 可以

#### 10. 完成标准（Exit Criteria）

- 已有共享 helper 能返回稳定的 `/tmp` exrepo 根路径
- helper 能把 suite 物化为新的 materialized suite，且 `repo` 为绝对路径
- 不会原地改写源 suite
- 相关静态检查和测试通过

#### 11. 失败协议（Failure Handling）

- 如果实现需要修改 `worktree_manager.py` 或 worker contract schema，必须停止
- 如果必须把 `/tmp` 路径写入长期 authority 状态，必须停止并报告
- 如果无法在当前 runner 边界内稳定表达 materialized suite，允许请求更多上下文，但不能自行扩到 selector 或 prompt 层

### 任务ID：T-002
任务名称：让 autoresearch baseline 和 round/replay 消费 materialized suite
任务类型（Task Type）：Refactor

#### 1. 任务目标（Goal）

- 让 `baseline`、`run-round`、`replay` 都通过 materialized suite 执行，从而不再依赖 candidate worktree 对 `.exrepos` 的本地可见性。
- 结果必须保持当前 `worktree` 生命周期、round authority、decision 语义不变。

#### 2. 非目标（Non-goals）

- 不新增新的 round 状态
- 不修改 `prepare-round / promote-round / discard-round / cleanup-round` 的语义
- 不改 worker prompt 或 prompt 内容
- 不自动触发 exrepo clone / reset

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - 如有必要，`toolchain/scripts/research/run_autoresearch_loop.py` 的最小兼容改动
  - 允许读取并调用 `toolchain/scripts/research/exrepo_runtime.py`
- Out-of-scope：
  - `toolchain/scripts/research/worktree_manager.py`
  - `toolchain/scripts/research/autoresearch_selector.py`
  - `toolchain/scripts/research/autoresearch_feedback_distill.py`
  - `toolchain/scripts/research/tasks/*.md`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `toolchain/scripts/research/run_autoresearch_loop.py`
  - `toolchain/scripts/research/worktree_manager.py`
  - `docs/operations/autoresearch-minimal-loop.md`
- 可选参考文件：
  - `toolchain/scripts/research/README.md`
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
- 不需要读取的区域（如果有）：
  - `product/`
  - `.agents/`
  - `.claude/`
  - `.opencode/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：局部重构 + 保守接线
- 先接 baseline，再接 `run-round`，最后处理 replay
- materialized suite 建议写到 run-local artifact 目录中，便于审计与复现
- 保持 P2 preflight 继续校验原始 contract suite，不把 preflight 语义转移到 `/tmp`

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：high
- 原因：该任务同时影响 `baseline`、`round`、`replay` 三条执行路径，且必须保证 authority 语义不漂移

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-001
- 可并行任务：
  - T-101 可在 T-001 完成后并行启动，但不得依赖本任务未冻结的 runner 细节
- 是否属于某个批次（Batch）：Batch 1 / Phase 1

#### 8. 风险与不确定性（Risks）

- baseline 与 round/replay 若消费两套不同 suite 语义，会导致结果不可比
- replay 若继续消费原始 suite，会留下隐蔽回归
- 如果 materialized suite 落点设计错误，可能破坏现有 artifact 可读性
- `run_autoresearch_loop.py` 如果存在隐式路径假设，可能在后期暴露

#### 9. 验证计划（Validation Plan）

- Static：
  - `python3 -m py_compile` 覆盖修改文件
- Test：
  - 更新 `test_run_autoresearch.py`
  - 更新 `test_autoresearch_round.py`
  - 如有必要，更新 `test_run_autoresearch_loop.py`
- Runtime：
  - 可做 mocked runner 的 deterministic smoke
  - 不要求在本任务里跑 live backend
- 是否可以做 smoke test：
  - 可以

#### 10. 完成标准（Exit Criteria）

- `baseline`、`run-round`、`replay` 已统一消费 materialized suite
- candidate worktree 不再因为缺少 `.exrepos/<name>` 而成为执行前提
- `worktree_manager.py` 无改动或仅零语义兼容改动
- 相关静态检查和测试通过

#### 11. 失败协议（Failure Handling）

- 如果要改动 `round.json`、`runtime.json`、`worker-contract.json` 的 authority 字段，必须停止
- 如果必须新增第二套 stop gate 或 decision 规则，必须停止
- 若发现 replay 无法在不改 authority 的前提下复用 materialized suite，必须先报告阻塞点

### 任务ID：T-003
任务名称：为 TMP Exrepo 运行时迁移补齐 deterministic 测试
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 为 `/tmp` exrepo 根解析、suite 绝对路径重写、baseline/round/replay 接入补齐 deterministic 自动测试。
- 结果必须能把“路径重写成功”和“runner 结果正确消费”区分开，而不是只测单一 happy path。

#### 2. 非目标（Non-goals）

- 不新增 live backend 验证
- 不重写现有 smoke 测试框架
- 不把测试扩展到 prompt 行为层

#### 3. 任务边界（Scope）

- In-scope：
  - 新增 `toolchain/scripts/research/test_exrepo_runtime.py`
  - `toolchain/scripts/research/test_run_skill_suite.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - 如有必要，`toolchain/scripts/research/test_run_autoresearch_loop.py`
- Out-of-scope：
  - 所有 `product/` 测试
  - live acceptance matrix
  - `.autoworkflow/` 真实 run 产物回放

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/test_run_skill_suite.py`
  - `toolchain/scripts/research/test_run_autoresearch.py`
  - `toolchain/scripts/research/test_autoresearch_round.py`
  - `toolchain/scripts/research/test_run_autoresearch_loop.py`
  - T-001 / T-002 涉及的新 helper 与接线代码
- 可选参考文件：
  - `toolchain/scripts/research/test_autoresearch_p2_smoke.py`
  - `toolchain/scripts/research/test_autoresearch_p1_3_smoke.py`
- 不需要读取的区域（如果有）：
  - `docs/`
  - `product/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：先补 helper 单测，再补 integration 测试
- 优先用本地临时 git repo / fixture 验证路径逻辑，不依赖真实 `.exrepos`
- 对 replay 路径单独给出非 happy path 用例，避免只测 baseline

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：主要是 deterministic fixture 与断言设计，逻辑不小，但上下文收敛

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-001、T-002
- 可并行任务：
  - T-004 可在测试接口稳定后并行启动
- 是否属于某个批次（Batch）：Batch 1 / Phase 1

#### 8. 风险与不确定性（Risks）

- 现有测试可能强绑定 `run_dir/worktrees/round-001` 之类路径假设
- 如果 fixture 依赖真实 `.exrepos` 目录，测试会变得脆弱
- 可能遗漏 replay 或 loop wrapper 的回归面

#### 9. 验证计划（Validation Plan）

- Static：
  - `python3 -m py_compile` 覆盖新增测试文件
- Test：
  - 运行相关 `unittest` 文件
  - 必须覆盖 helper、baseline、run-round、replay 至少四类断言
- Runtime：
  - 不要求 live runtime
- 是否可以做 smoke test：
  - 可以，deterministic smoke 即可

#### 10. 完成标准（Exit Criteria）

- 新 helper 和接入点已有 deterministic 自动测试
- baseline / round / replay 路径都有覆盖
- 相关测试通过且没有新增 flaky 依赖

#### 11. 失败协议（Failure Handling）

- 如果测试只能通过真实 `/tmp` 全局目录才能成立，必须停止并改回隔离 fixture
- 如果要引入 live backend 才能断言核心逻辑，必须停止并报告测试分层问题
- 若发现现有测试体系无法表达必要断言，允许新增专用测试文件，但不得顺手重构整套测试框架

### 任务ID：T-004
任务名称：更新运行文档并退役旧的 exrepo 输入卫生计划
任务类型（Task Type）：Document

#### 1. 任务目标（Goal）

- 让 repo-local runbook、research README 和 `analysis` 入口文档反映新的 `/tmp exrepo + materialized suite` 路径。
- 把旧的 `exrepo input hygiene` 规划退役为 lineage，避免同时存在两份“当前执行规划”。

#### 2. 非目标（Non-goals）

- 不新增主线知识文档
- 不改 prompt 文本
- 不写实现细节冒充当前事实

#### 3. 任务边界（Scope）

- In-scope：
  - `docs/operations/autoresearch-minimal-loop.md`
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
  - `docs/analysis/README.md`
  - `docs/analysis/autoresearch-p2-exrepo-input-hygiene-task-plan.md`
- Out-of-scope：
  - `docs/knowledge/`
  - `product/`
  - `.agents/`

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/operations/autoresearch-minimal-loop.md`
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
  - `docs/analysis/README.md`
  - `docs/knowledge/foundations/docs-governance.md`
- 可选参考文件：
  - 本规划文档
  - T-001 / T-002 的最终实现
- 不需要读取的区域（如果有）：
  - `docs/reference/`
  - `docs/archive/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：实现后再更新文档，避免写假规则
- 先更新 runbook，再更新脚本 README，最后调整 `analysis/README.md` 和旧规划状态
- 只描述代码已经成立的行为，不补愿景性说明

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：上下文不复杂，但需要严格遵守 docs 治理和状态语义

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-002、T-003
- 可并行任务：
  - T-103 可在 Phase 2 后续文档层与本任务顺序衔接，但不建议并行改同一文件
- 是否属于某个批次（Batch）：Batch 1 / Phase 1

#### 8. 风险与不确定性（Risks）

- 文档容易误写成“废弃 worktree”
- 旧规划若不退役，会留下双主线入口
- 研究 README 的 count 和入口规则容易漏改

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行现有 docs/path 检查脚本（若适用）
- Test：
  - 不要求新增代码测试
- Runtime：
  - 不要求 runtime 验证
- 是否可以做 smoke test：
  - 可以做文档链接与路径检查 smoke

#### 10. 完成标准（Exit Criteria）

- runbook 已说明 `/tmp exrepo + materialized suite` 路径
- `analysis/README.md` 已把本规划列为当前执行入口
- 旧的 `autoresearch-p2-exrepo-input-hygiene-task-plan.md` 已改成 `status: superseded`
- 文档检查通过，且不再出现双主线执行规划

#### 11. 失败协议（Failure Handling）

- 如果实现尚未稳定，禁止提前更新为“已成立”事实
- 如果需要把研究结论直接升格到 `docs/knowledge/`，必须先停并确认
- 若发现入口页 count 或状态难以对齐，必须报告具体冲突文件

### 任务ID：T-101
任务名称：实现 TMP Exrepo 维护脚本的 init/reset/prepare CLI
任务类型（Task Type）：Implement

#### 0. 当前状态（2026-03-30）

- 仓库里已经有 `toolchain/scripts/research/manage_tmp_exrepos.py` 这个窄前体脚本。
- 当前真实 CLI 形状仍是 repo-list 驱动同步：
  - `--repo-list`
  - `--repo-root`
  - `--temp-root`
- 当前真实行为是：
  - 目标 repo 缺失时执行 clone
  - 目标 repo 已存在时先尝试 `git pull`
  - `git pull` 失败时执行 `git reset --hard` 后重试 `git pull`
- 但当前实现还不能按本文合同宣称 `T-101` 已完成，因为下面这些点尚未被代码证明：
  - `init / reset / prepare` 子命令形状
  - 按 suite 清单推导 repo 集合
  - “回到远端默认分支最新 HEAD” 这一更强 reset 语义
  - 更明确的 `/tmp` 根路径保护 contract

#### 1. 任务目标（Goal）

- 新增一个独立维护脚本，能在 `/tmp` 下初始化 exrepo 根目录、为缺失 repo 做初始 clone，并把已有 repo reset 到远端默认分支的最新 HEAD。
- 脚本必须支持按显式 repo 名或按 suite 清单推导 repo 集合。

#### 2. 非目标（Non-goals）

- 不把 clone/reset 逻辑隐式塞回 `run_autoresearch.py`
- 不修改 `.exrepos/` 源仓库内容
- 不在本任务中自动接入 `autoresearch` 主流程
- 不处理 prompt、selector 或 worktree 逻辑

#### 3. 任务边界（Scope）

- In-scope：
  - 新增 `toolchain/scripts/research/manage_tmp_exrepos.py`
  - `toolchain/scripts/research/exrepo_runtime.py` 中允许复用的 tmp-root helper
  - 如有必要，`toolchain/scripts/research/common.py` 的共享常量
- Out-of-scope：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/autoresearch_round.py`
  - `.exrepos/` 目录内容
  - 任何 `product/` 文件

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/common.py`
  - T-001 中新增的 `toolchain/scripts/research/exrepo_runtime.py`
  - `toolchain/scripts/research/run_skill_suite.py`
  - `docs/operations/research-cli-help.md`
- 可选参考文件：
  - `toolchain/scripts/README.md`
  - `toolchain/scripts/research/README.md`
- 不需要读取的区域（如果有）：
  - `product/`
  - `docs/knowledge/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：新增独立 CLI 脚本
- 子命令建议至少固定为：
  - `init`
  - `reset`
  - `prepare`
- 先实现 repo 集合解析，再实现 clone/reset，再补安全边界
- destructive git 动作必须只允许作用于 `/tmp` exrepo 根之下

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：high
- 原因：涉及 git clone/fetch/reset/clean 的安全边界，不能把 destructive 行为扩散到源仓库或用户工作树

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-001
- 可并行任务：
  - T-002 可与本任务并行，但双方不得同时改同一 helper 语义
- 是否属于某个批次（Batch）：Batch 2 / Phase 2

#### 8. 风险与不确定性（Risks）

- seed repo 缺少 `origin` remote 或 `origin/HEAD`
- reset 逻辑如果路径保护不严，可能误触非 `/tmp` 仓库
- suite 解析与 repo 名解析若不一致，会出现两套 repo 集合语义
- clone 依赖网络与远端状态，执行环境可能需要额外权限

#### 9. 验证计划（Validation Plan）

- Static：
  - `python3 -m py_compile` 覆盖新脚本
- Test：
  - 必须新增 deterministic 测试
  - 覆盖 repo 名模式与 suite 模式两类输入
- Runtime：
  - 可做本地临时 git 仓库 smoke test
- 是否可以做 smoke test：
  - 可以

#### 10. 完成标准（Exit Criteria）

- 脚本能初始化 `/tmp` exrepo 根目录
- `init` 能为缺失 repo 创建 clone
- `reset` 能将已有 repo fetch 并回到远端默认分支最新 HEAD
- `prepare` 能组合执行缺失 clone 与已有 repo reset
- 脚本只作用于 `/tmp` exrepo 根，相关验证通过

#### 11. 失败协议（Failure Handling）

- 如果必须对 `.exrepos/` 源仓库执行 destructive git 命令，必须停止
- 如果默认分支无法稳定解析，必须 fail closed 并报告具体 repo
- 如果脚本需要自动写入 `autoresearch` authority 文件，必须停止

### 任务ID：T-102
任务名称：为 TMP Exrepo 维护脚本补齐 git 安全与回归测试
任务类型（Task Type）：Implement

#### 0. 当前状态（2026-03-30）

- 仓库里已经有 `toolchain/scripts/research/test_manage_tmp_exrepos.py`。
- 当前已被测试覆盖的真实行为包括：
  - repo list 解析
  - duplicate local target 拒绝
  - 缺失 repo clone
  - 已有 repo pull
  - pull 失败后的 reset-then-pull
  - 主入口在 repo sync 失败时返回非零
- 但当前实现还不能按本文合同宣称 `T-102` 已完成，因为下面这些断言尚未被测试证明：
  - suite-driven repo 选择
  - 明确的 `/tmp` 路径保护
  - `origin` 缺失或默认分支解析失败的 fail-closed 语义
  - 与 `T-101` full-contract 目标一一对应的安全边界回归

#### 1. 任务目标（Goal）

- 为 `manage_tmp_exrepos.py` 补齐 deterministic 自动测试，覆盖 clone、reset、suite-driven repo 选择和路径保护。
- 结果必须验证脚本只会触达 `/tmp` exrepo 根，并能在失败时明确报错。

#### 2. 非目标（Non-goals）

- 不跑真实外网 clone
- 不要求 live acceptance matrix
- 不测试 prompt 或 eval 输出

#### 3. 任务边界（Scope）

- In-scope：
  - 新增 `toolchain/scripts/research/test_manage_tmp_exrepos.py`
  - 如有必要，补充 `toolchain/scripts/research/test_run_skill_suite.py` 的兼容断言
- Out-of-scope：
  - 其他 runner integration 测试重构
  - live backend 测试

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/manage_tmp_exrepos.py`
  - `toolchain/scripts/research/test_run_skill_suite.py`
  - T-001 中的 tmp-root helper
- 可选参考文件：
  - `toolchain/scripts/research/test_run_backend_acceptance_matrix.py`
- 不需要读取的区域（如果有）：
  - `docs/`
  - `product/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：临时 git repo fixture + 纯本地回环测试
- 优先验证路径保护与 fail-closed，再验证 happy path
- 对 `origin` 缺失、默认分支无法解析、脏 repo reset 三类风险分别给独立用例

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：测试设计需覆盖 git 边界，但上下文集中

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-101
- 可并行任务：
  - T-103 可在脚本 CLI 形状稳定后并行起草文档
- 是否属于某个批次（Batch）：Batch 2 / Phase 2

#### 8. 风险与不确定性（Risks）

- git fixture 如果依赖系统默认分支命名，测试可能在不同环境不稳定
- 如果测试直接使用真实 `/tmp` 全局目录，可能造成污染
- suite-driven repo 解析若和脚本实现耦合过深，测试可读性会下降

#### 9. 验证计划（Validation Plan）

- Static：
  - `python3 -m py_compile` 覆盖新增测试文件
- Test：
  - 运行 `test_manage_tmp_exrepos.py`
  - 相关单测需覆盖失败场景
- Runtime：
  - 不要求真实网络 clone
- 是否可以做 smoke test：
  - 可以，用本地裸仓库和临时目录

#### 10. 完成标准（Exit Criteria）

- 维护脚本关键路径已有 deterministic 自动测试
- clone / reset / prepare / fail-closed 行为都有断言
- 测试通过且不依赖真实外网

#### 11. 失败协议（Failure Handling）

- 如果测试必须访问真实远端才能成立，必须停止
- 如果路径保护无法在测试中稳定表达，必须先报告并收窄脚本边界
- 若 fixture 需要修改源 `.exrepos/`，必须停止

### 任务ID：T-103
任务名称：为 TMP Exrepo 维护脚本补齐 runbook 与 CLI 文档
任务类型（Task Type）：Document

#### 0. 当前状态（2026-03-30）

- 当前仓库已经在下面这些入口里提到 `manage_tmp_exrepos.py`：
  - `docs/operations/tmp-exrepo-maintenance.md`
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
- `docs/operations/README.md` 也已经把这份 runbook 挂到最近入口。
- 因此，`T-103` 当前已承接“给现有维护脚本补 runbook 与入口文档”这一文档目标。
- 但这不反向证明 `T-101` 或 `T-102` 已闭环；如果后续维护脚本 CLI 形状继续变化，`T-103` 仍需跟随同步。

#### 1. 任务目标（Goal）

- 给 `/tmp` exrepo 维护脚本补一份 repo-local runbook 和 CLI 说明，明确初始化、reset、prepare 和安全边界。
- 文档必须能被后续执行 Agent 直接引用，不依赖聊天上下文。

#### 2. 非目标（Non-goals）

- 不新增 `docs/knowledge/` 主线规则
- 不描述尚未实现的自动触发逻辑
- 不把 `/tmp` 当 authority 描述

#### 3. 任务边界（Scope）

- In-scope：
  - 新增 `docs/operations/tmp-exrepo-maintenance.md`
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
  - 如有必要，`docs/README.md` 或 `docs/operations/README.md` 的最近入口更新
- Out-of-scope：
  - `docs/knowledge/`
  - `product/`
  - 历史分析文档的大范围重写

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `docs/operations/research-cli-help.md`
  - `toolchain/scripts/research/README.md`
  - `docs/knowledge/foundations/docs-governance.md`
  - `toolchain/scripts/research/manage_tmp_exrepos.py`
- 可选参考文件：
  - `docs/operations/autoresearch-minimal-loop.md`
- 不需要读取的区域（如果有）：
  - `docs/reference/`
  - `docs/archive/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：新增 runbook + 局部入口更新
- 文档先写安全边界，再写命令示例，再写常见失败场景
- 所有命令示例都应以代码真实参数为准

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：主要是文档治理与入口更新，逻辑相对收敛

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-101、T-102
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 2 / Phase 2

#### 8. 风险与不确定性（Risks）

- 容易把脚本描述成“runner 自动流程的一部分”，与当前边界不符
- 新增 runbook 后若不更新入口，仍会产生孤儿文档
- 命令示例如果未同步实现，会误导后续 Agent

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行文档链接或路径检查（如适用）
- Test：
  - 不要求新增代码测试
- Runtime：
  - 不要求 runtime 验证
- 是否可以做 smoke test：
  - 可以做文档路径与命令参数核对 smoke

#### 10. 完成标准（Exit Criteria）

- `/tmp` exrepo 维护脚本已有专用 runbook
- CLI 帮助文档和脚本 README 已同步更新
- 入口页已能找到新文档
- 文档检查通过

#### 11. 失败协议（Failure Handling）

- 如果脚本 CLI 尚未稳定，禁止先写死命令语义
- 如果需要把维护脚本提升为默认主线入口，必须先停止并确认
- 若新增文档无法挂到最近入口，必须先修入口再结束任务

## 四、任务依赖图

文字依赖关系如下：

- T-001 是整份规划的共享起点，先冻结 `/tmp exrepo + materialized suite` 的运行时合同
- T-002 依赖 T-001，负责把 helper 接入 `baseline / run-round / replay`
- T-003 依赖 T-001 和 T-002，负责把运行时迁移的行为固化为 deterministic 自动测试
- T-004 依赖 T-002 和 T-003，负责把文档入口与旧规划状态同步到位
- T-101 依赖 T-001，只依赖 `/tmp` 根目录合同，不依赖 T-002 的 runner integration 完成
- T-102 依赖 T-101
- T-103 依赖 T-101 和 T-102

## 五、推荐执行顺序（Batch 划分）

### Batch 1：Phase 1 最小运行时改动

1. T-001
2. T-002
3. T-003
4. T-004

### Batch 2：Phase 2 维护脚本与配套文档

1. T-101
2. T-102
3. T-103

## 六、可并行执行的任务组

- 组 A：
  - T-001
  - 说明：必须单独先做，不建议并行
- 组 B：
  - T-002
  - T-101
  - 说明：两者都依赖 T-001，但应通过共享 helper contract 解耦；如果 helper 语义未冻结，不应并行
- 组 C：
  - T-003
  - T-103
  - 说明：T-003 属于 Phase 1，T-103 属于 Phase 2；只有在 T-101/T-102 已稳定后，才允许与 T-003 的尾声阶段错峰并行

## 七、高风险任务列表

- T-001：共享 helper 会决定整条路径合同，设计漂移会放大返工
- T-002：同时触达 baseline、run-round、replay 三条执行路径，最容易引入隐蔽回归
- T-101：涉及 clone/fetch/reset/clean 的 destructive git 边界，必须严格限定在 `/tmp` 根下
- T-102：如果测试夹具不稳，会把 Phase 2 变成脆弱工具链

## 八、推荐整体执行策略

- 先完成 Phase 1，再进入 Phase 2，不要反过来
- 先修输入执行层，不碰 `worktree` 生命周期和 authority 层
- 不要把 `/tmp` 当状态真相层；authority 继续留在 `.autoworkflow/`
- suite materialization 必须先于 maintenance 脚本大规模扩展，否则会出现“脚本先做出来，但 runner 还没统一消费”的半成品状态
- 维护脚本应保持显式调用，不要在本轮规划中顺手塞进 `autoresearch` 自动流程

## 九、与旧规划的关系

- 本文接管当前 `exrepo input hygiene` 规划的执行入口角色
- 旧文档 `autoresearch-p2-exrepo-input-hygiene-task-plan.md` 继续保留为 lineage，但不再作为当前默认施工入口
