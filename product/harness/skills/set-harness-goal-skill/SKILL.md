---
name: set-harness-goal-skill
description: 当 Harness 系统尚未初始化，或 `.aw/goal-charter.md` 不存在，需要将用户的自然语言需求转化为结构化的 Harness 控制面组件时，使用这个技能。
---

# 设置 Harness 目标技能

## 概览

本技能实现 `RepoScope.SetGoal` 状态转移算子，对应 Harness 控制回路中的**参考信号初始化**阶段。

控制系统的参考信号（Goal）必须在闭环运行前被显式设定。如果参考信号缺失或含糊，控制器就无法计算误差，整个控制回路将失去方向。本技能负责在系统"上电"时，将用户的自然语言需求转化为结构化的 Harness 系统组件，为后续控制回路提供明确的参考基准。

当 `.aw/` 目录尚未建立，或 `goal-charter.md` 不存在，或 Harness 被明确要求初始化一个新目标时，使用这个技能。

## 何时使用

- `.aw/` 目录不存在或为空
- `goal-charter.md` 不存在
- 用户明确要求"设定新目标"或"初始化 Harness"
- 当前 repo 没有活跃的 Harness 控制面

**不**使用的情况：
- `goal-charter.md` 已存在且用户要求修改它 → 路由到 `repo-change-goal-skill`
- 已有活跃 worktrack 且需要判断下一步 → 路由到 `repo-status-skill` + `repo-whats-next-skill`
- 只需要刷新 repo 快照 → 路由到 `repo-refresh-skill`

## 工作流

1. **检查现有状态**
   - 检查 `.aw/goal-charter.md` 是否存在
   - 如果存在 → 停止并路由到 `repo-change-goal-skill`
   - 如果不存在 → 继续

2. **分析用户需求**
   - 读取用户提供的自然语言需求描述
   - 识别核心目标、范围边界、技术约束、成功标准
   - 识别可分解的子系统或阶段（供后续 worktrack 拆分参考）

3. **生成 `goal-charter.md`**
   - 将分析结果填入标准 `Goal Charter` 格式
   - 包含：Project Vision、Core Product Goals、Technical Direction、Success Criteria、System Invariants
   - **不**在 goal charter 中指定具体的 worktrack 拆分方式；worktrack 规划属于 `init-worktrack-skill` 的职责

4. **生成 `control-state.md`**
   - 设置初始控制面状态：`repo_scope: active`、`worktrack_scope: closed`
   - 设置合理的默认 `Continuation Authority`：
     - `post_contract_autonomy: delegated-minimal`
     - `autonomy_scope: current-goal-only`
     - `max_auto_new_worktracks: 1`
     - `stop_after_autonomous_slice: yes`
   - 设置 `Handback Guard` 初始值：`handoff_state: none`

5. **生成 `repo/snapshot-status.md`**
   - 基于当前 repo 实际状态生成初始快照
   - 如果 repo 为空，如实记录"空仓库起步"

6. **确认目录结构并复制模板资产**
   - 优先使用本技能自带的 `scripts/deploy_aw.py` 生成标准 Harness `.aw/` 基线；它会从本技能的 `assets/` 目录渲染/复制所需文件，确保目录结构完整：
     ```
     .aw/
     ├── control-state.md           ← 基于 assets/control-state.md 模板填充
     ├── goal-charter.md            ← 基于 assets/goal-charter.md 模板填充
     ├── repo/
     │   └── snapshot-status.md     ← 基于 assets/repo/snapshot-status.md 模板填充
     ├── template/
     │   ├── README.md              ← 从 assets/template/README.md 复制
     │   └── goal-charter.template.md  ← 从 assets/template/goal-charter.template.md 复制
     └── worktrack/
         ├── README.md              ← 从 assets/worktrack/README.md 复制
         ├── contract.md            ← 从 assets/worktrack/contract.md 复制
         ├── gate-evidence.md       ← 从 assets/worktrack/gate-evidence.md 复制
         └── plan-task-queue.md     ← 从 assets/worktrack/plan-task-queue.md 复制
     ```
   - `assets/` 目录遵循 Codex Skills 标准，存放本技能所需的模板、资源和参考文档
   - `scripts/deploy_aw.py` 是本技能的标准 `.aw` deploy helper；它接收 `--deploy-path <目标 repo / worktree 根>`，并固定在 `<deploy-path>/.aw/` 下生成模板。在 canonical source 与 deployed target 中都应可直接读取本技能自带的 `assets/`
   - 复制时只复制模板骨架；内容字段（如 Project Vision、autonomy 参数等）由第 3~5 步的分析结果填充
   - 不覆盖已存在的文件；如果 `.aw/` 中已有同名文件，保留现有文件并报告冲突

7. **用户确认**
   - 向用户展示生成的 `Goal Charter` 摘要
   - 等待用户确认或修改
   - **在用户确认前不写入文件**

8. **写入并返回**
   - 用户确认后执行写入操作：
     - 将填充好的 `goal-charter.md`、`control-state.md`、`repo/snapshot-status.md` 写入 `.aw/`
     - 将 `assets/` 中的模板文件复制到 `.aw/` 的对应位置（template/ 和 worktrack/ 子目录）
   - 返回 `Harness 初始化结果`，包含：
     - 生成的组件清单
     - 建议的下一动作（进入 `RepoScope.Observe`）
     - 需要审批：`false`（如果用户已确认）

## 硬约束

- 本技能是**系统初始化**层；只在 `.aw/` 不存在或 `goal-charter.md` 缺失时运行
- **绝不**覆盖已有的 `goal-charter.md`；已存在时必须路由到 `repo-change-goal-skill`
- **绝不**代替用户设定目标；必须展示生成的 goal charter 摘要并等待确认
- 不要在初始化阶段混入 worktrack 级规划；worktrack 拆分是 `init-worktrack-skill` 的职责
- 不要猜测用户未明确说明的需求；有歧义时应暴露出来，而不是替用户做选择
- 设置默认 autonomy 参数时，优先选择"小步推进、逐层验证"的保守策略；`max_auto_new_worktracks` 默认值必须与 `Harness Control State` artifact 和 control-state 模板保持一致，连续多 worktrack 预算只能来自显式观察 profile 或后续 control-state override
- **不依赖外部 scaffold 脚本**；所有模板来自本技能自带的 `assets/` 目录，遵循 Codex Skills 标准
- 如果需要 repo-local operator 帮助脚本，使用本技能自带的 `scripts/deploy_aw.py`，不要再依赖仓库根下的独立 `.aw` scaffold 工具
- 写入文件后，控制权返回 Harness；由 Harness 根据新的 control state 决定下一步

## 预期输出

使用这个技能时，产出一份至少包含以下章节的 `Harness 初始化结果`：

- `初始化决策`
- `需求摘要`
- `生成的组件清单`
- `Goal Charter 摘要`
- `默认控制策略`
- `建议下一动作`
- `返回 Harness`

结果中至少应包含以下字段或等价表达：

- `初始化状态`
- `goal_charter_created`
- `control_state_created`
- `repo_snapshot_created`
- `project_vision`
- `core_product_goals`
- `success_criteria`
- `system_invariants`
- `post_contract_autonomy`
- `max_auto_new_worktracks`
- `stop_after_autonomous_slice`
- `建议代码仓库动作`
- `建议下一路由`
- `建议下一范围`
- `可继续`
- `需要审批`
- `如何审查`

## 模板资产

本技能遵循 Codex Skills 标准，在 `assets/` 目录下携带完整的 Harness 初始化模板资产：

| 资产路径 | 用途 | 复制目标 |
|---------|------|---------|
| `assets/control-state.md` | 控制状态模板骨架 | `.aw/control-state.md`（填充后写入） |
| `assets/goal-charter.md` | 目标章程模板骨架 | `.aw/goal-charter.md`（填充后写入） |
| `assets/repo/snapshot-status.md` | 仓库快照模板骨架 | `.aw/repo/snapshot-status.md`（填充后写入） |
| `assets/template/README.md` | 模板目录说明 | `.aw/template/README.md`（直接复制） |
| `assets/template/goal-charter.template.md` | 目标章程复用模板 | `.aw/template/goal-charter.template.md`（直接复制） |
| `assets/worktrack/README.md` | 工作追踪目录说明 | `.aw/worktrack/README.md`（直接复制） |
| `assets/worktrack/contract.md` | 工作追踪契约模板骨架 | `.aw/worktrack/contract.md`（直接复制） |
| `assets/worktrack/gate-evidence.md` | 关卡证据模板骨架 | `.aw/worktrack/gate-evidence.md`（直接复制） |
| `assets/worktrack/plan-task-queue.md` | 计划任务队列模板骨架 | `.aw/worktrack/plan-task-queue.md`（直接复制） |
| `scripts/deploy_aw.py` | `.aw` 初始化 deploy helper | 由操作者或测试直接运行，传入 `--deploy-path <repo/worktree 根>`，脚本在 `<deploy-path>/.aw/` 下生成/复制上述资产 |

这些资产在 deploy 阶段随本技能一并安装到宿主运行环境。执行时，本技能从自身的 `assets/` 目录读取模板；如需 repo-local operator 工具面，则直接运行本技能自带的 `scripts/deploy_aw.py`，把目标 worktree / repo 根通过 `--deploy-path` 传入。不要依赖外部 scaffold 脚本或独立的 `.aw` 模板源码根。

最小用法：

```bash
python3 scripts/deploy_aw.py generate --deploy-path "$DEPLOY_PATH" --owner aw-kernel
python3 scripts/deploy_aw.py generate --help
```

## 资源

使用当前用户需求文本、当前 repo 实际状态（文件、分支、提交历史），以及本技能 `assets/` 目录下的标准模板格式作为参考。不要依赖外部 scaffold 脚本；需要 operator 辅助时直接使用本技能自带的 `scripts/deploy_aw.py`，把目标路径通过 `--deploy-path` 传入，由本技能生成符合 Harness 运行协议的标准组件。
