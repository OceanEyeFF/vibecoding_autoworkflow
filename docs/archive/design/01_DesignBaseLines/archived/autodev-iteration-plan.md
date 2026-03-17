---
title: "AutoDev 多版本迭代计划"
status: archived
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# AutoDev 多版本迭代计划

> 创建时间：2026-01-04
> 更新时间：2026-01-04（修正 v0.3 为"指令模块化"以适配 Claude Code Skill 机制）
> 核心思想：借鉴 IDEA-005 的本地化状态管理思想 + 多层回路机制

---

## 版本规划总览

| 版本 | 核心功能 | 状态管理方式 | 回路层级 | 预计实现难度 |
|------|---------|------------|---------|------------|
| **v0.1 基础版** | Phase 1-4 流程 + Level 0 | TodoWrite 内存 | Level 0 | ⭐⭐ |
| **v0.2 增强版** | + Git 检查点 + Level 1 | 本地文件缓存 (.autodev/state.json) | Level 0-1 | ⭐⭐⭐ |
| **v0.3 完整版** | + Level 2 + **指令模块化** | 模块化指令文件（手动 Read） | Level 0-2 | ⭐⭐⭐⭐ |
| **v1.0 生产版** | + Level 3 + 辅助脚本 | 脚本辅助管理 + 可靠 Git 操作 | Level 0-3 | ⭐⭐⭐⭐⭐ |

**v0.3 修正说明**：
Claude Code 的 Skill 系统不支持 `instruction_files` 元数据字段自动加载外部文件。v0.3 采用"指令模块化"策略：将详细指令拆分到 `phases/`、`gates/`、`loops/` 目录中的独立 Markdown 文件，通过在 SKILL.md 中明确写出"当 X 发生时，执行 Read(文件路径)"来手动触发指令加载。

---

## v0.1 基础版：验证可行性

### 目标
验证核心工作流是否可行，建立用户信心。

### 功能范围

#### ✅ 包含功能
1. **Phase 1: 需求精炼**
   - AskUserQuestion 澄清需求
   - 输出验收标准
   - G1 门禁检查

2. **Phase 2: 任务规划**
   - 分析项目结构（Glob, Read）
   - 拆分任务（3-7 个）
   - 创建 TodoWrite 任务列表
   - G2 门禁检查

3. **Phase 3: 迭代开发（基础循环）**
   - 逐个执行任务
   - Level 0 即时修复（最多 3 次）
   - 测试验证（G3 门禁）

4. **Phase 4: 验收提交**
   - 完整测试
   - 生成交付报告
   - Git 提交（用户确认后）

5. **基础回路**
   - Level 0：即时修复（retry ≤ 3）
   - Level 0 失败后 → **人工介入**（不做 Git 回退）

#### ❌ 暂不包含
- Git 检查点机制
- Level 1/2 回路
- 指令外置到文件
- 状态持久化

### 状态管理

**方式**：仅使用 TodoWrite（Claude Code 原生）

```javascript
// 状态存储在 TodoWrite 中
TodoWrite([
  { content: "任务1: 实现登录UI", status: "completed", activeForm: "..." },
  { content: "任务2: 实现API调用", status: "in_progress", activeForm: "..." },
  { content: "任务3: 状态管理", status: "pending", activeForm: "..." }
])
```

**局限性**：
- 无法记录 retry 次数
- 无法记录 Git commit 信息
- 中断恢复能力有限

### Level 0 即时修复流程

```
测试失败
   ↓
retry = 0
   ↓
┌──────────────────┐
│ 分析错误 → 修复  │
│ 重新测试         │ ← retry++
└──────────────────┘
   ↓
retry > 3?
   ├─ No  → 继续循环
   └─ Yes → 🚨 人工介入（输出调试受阻报告）
```

### 验收标准

- [ ] 能完整走通 Phase 1 → 2 → 3 → 4
- [ ] G1/G2/G3/G4 门禁能正确检查
- [ ] Level 0 循环能工作
- [ ] 失败 3 次后能请求人工介入
- [ ] 中断后能通过 TodoWrite 恢复基本进度

### Skill 文件修改

创建 `toolchain/skills/aw-kernel/autodev/v0.1/SKILL.md`（精简版）

---

## v0.2 增强版：Git 回退 + Level 1

### 目标
增加自动恢复能力，减少人工介入频率。

### 新增功能

#### 1. Git 检查点机制

**Phase 2 检查点**：
```bash
# Phase 2 结束时
git add -A
git stash push -m "autodev-checkpoint-phase2"
```

**任务起点记录**：
```bash
# 每个任务开始前
task_start_commit=$(git rev-parse HEAD)
# 存储到本地文件
echo "$task_start_commit" > .autodev/task-start
```

#### 2. Level 1 回路：Git 回退 + 任务重构

```
Level 0 失败 3 次
   ↓
┌────────────────────────────┐
│ Level 1: 任务重构          │
│ 1. git checkout 回到起点   │
│ 2. 分析失败模式            │
│ 3. 重构任务（拆分/换方案） │
│ 4. 更新 TodoWrite          │
│ 5. 用新方案重试（2次）     │
└────────────────────────────┘
   ↓
仍失败 → 🚨 人工介入
```

#### 3. 本地化状态管理（借鉴 IDEA-005）

**目录结构**：
```
.autodev/
├── state.json                 # 当前状态
├── phase2-checkpoint          # Phase 2 检查点 commit ID
├── task-start                 # 当前任务起点 commit ID
└── retry-log.json             # 重试历史记录
```

**state.json 格式**：
```json
{
  "version": "0.2",
  "current_phase": 3,
  "current_task": "任务2",
  "retry_count": 2,
  "failure_level": 1,
  "phase2_checkpoint": "abc123...",
  "task_start_commit": "def456...",
  "last_update": "2026-01-04T14:30:00Z"
}
```

### 状态管理策略

**写入时机**：
- Phase 转换时
- 任务状态变更时
- retry_count 增加时
- Level 切换时

**读取时机**：
- Skill 启动时（恢复状态）
- Level 1 回退前（获取 task_start_commit）
- 每 5 轮对话刷新时

**操作示例**：
```bash
# 写入状态
Bash('echo "{...json...}" > .autodev/state.json')

# 读取状态
Read('.autodev/state.json')

# 回退到任务起点
task_start=$(cat .autodev/task-start)
git checkout $task_start
git clean -fd
```

### 验收标准

- [ ] v0.1 的所有功能正常
- [ ] Phase 2 检查点能正确创建
- [ ] 任务起点能正确记录
- [ ] Level 1 回退能恢复到任务开始前
- [ ] 状态文件能正确读写
- [ ] 中断后能从 state.json 恢复完整状态

---

## v0.3 完整版：指令模块化 + Level 2

### 目标
完整实现多层回路，达到生产可用标准。

### 新增功能

#### 1. 指令模块化（借鉴 IDEA-005 思想，适配 Claude Code Skill 机制）

**目录结构**：
```
toolchain/skills/aw-kernel/autodev/
├── SKILL.md                         # 核心 Skill（简化版，含启动协议）
├── phases/
│   ├── phase-1-refinement.md        # Phase 1 详细指令
│   ├── phase-2-planning.md          # Phase 2 详细指令
│   ├── phase-3-iteration.md         # Phase 3 详细指令
│   └── phase-4-delivery.md          # Phase 4 详细指令
├── gates/
│   ├── gate-1-completeness.md       # G1 检查清单
│   ├── gate-2-executability.md      # G2 检查清单
│   ├── gate-3-testing.md            # G3 检查清单
│   └── gate-4-delivery.md           # G4 检查清单
└── loops/
    ├── loop-level-0-instant-fix.md  # Level 0 修复策略
    ├── loop-level-1-task-refactor.md # Level 1 重构策略
    ├── loop-level-2-replanning.md   # Level 2 重规划策略
    └── loop-level-3-human.md        # Level 3 人工介入协议
```

**SKILL.md 精简示例**（不使用 `instruction_files` 字段）：
```yaml
---
name: autodev
description: >
  自动化开发工作流 - 四阶段流程 + 多层回路机制
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# AutoDev 自动化开发工作流

## 启动协议（必须执行）

1. 首次启动时读取核心指令：
   ```bash
   Read("toolchain/skills/aw-kernel/autodev/phases/phase-1-refinement.md")
   ```

2. 读取 state.json 恢复状态（如存在）

3. 根据当前 Phase 读取对应的详细指令文件

4. 输出当前状态报告

## 指令刷新机制（手动触发）

**触发条件** → **刷新操作**：
- 每 5 轮对话 → Read 当前 Phase 的指令文件
- Gate 失败 → Read 对应 Gate 的检查清单 + Loop 策略文件
- 用户说"你忘了" → Read 所有相关指令文件
- 中断恢复 → Read 当前 Phase + 当前 Loop Level 的指令文件

**注意**：Claude Code 不支持自动加载 `instruction_files`，需要在 SKILL.md 中明确写出"当 X 发生时，执行 Read(文件路径)"的指令。
```

#### 2. Level 2 回路：整体重规划

```
Level 1 失败
   ↓
┌────────────────────────────────┐
│ Level 2: 整体重规划            │
│ 1. git checkout Phase2检查点   │
│ 2. 重新审视验收标准            │
│ 3. 重新拆分所有任务            │
│ 4. 请求用户确认新规划          │
│ 5. 重新进入 Phase 3            │
└────────────────────────────────┘
   ↓
仍失败 → 🚨 Level 3 人工介入
```

#### 3. 指令刷新触发器（手动 Read 实现）

| 触发条件 | 刷新内容 | 操作 |
|---------|---------|------|
| 每 5 轮对话 | 当前 Phase 指令文件 | Read("phases/phase-X-xxx.md") |
| Gate 失败 | Gate 检查清单 + Loop 策略 | Read("gates/gate-X.md") + Read("loops/loop-level-X.md") |
| 用户说"你忘了" | 全部相关指令文件 | Read 当前 Phase + Gate + Loop 所有文件 |
| 中断恢复 | 全部指令文件 | 按 state.json 状态读取对应文件 |

**实现方式**：在 SKILL.md 中明确写出触发条件和对应的 Read 操作，而非依赖元数据自动加载。

### 状态管理增强

**state.json v0.3 格式**：
```json
{
  "version": "0.3",
  "current_phase": 3,
  "current_task": "任务2",
  "retry_count": 2,
  "failure_level": 2,
  "phase2_checkpoint": "abc123...",
  "task_start_commit": "def456...",
  "instruction_refresh_count": 3,
  "last_instruction_refresh": "2026-01-04T14:25:00Z",
  "conversation_round": 12,
  "loop_history": [
    { "level": 0, "attempts": 3, "timestamp": "..." },
    { "level": 1, "attempts": 2, "timestamp": "..." }
  ],
  "last_update": "2026-01-04T14:30:00Z"
}
```

### 验收标准

- [ ] v0.2 的所有功能正常
- [ ] 模块化指令文件能正确创建和读取（手动 Read 方式）
- [ ] Level 2 回路能正确执行
- [ ] 指令刷新机制能工作（通过手动 Read 触发）
- [ ] state.json 包含完整的循环历史
- [ ] SKILL.md 主文件精简，详细指令分离到模块文件中

---

## v1.0 生产版：辅助脚本 + 完整 Level 3

### 目标
达到生产环境可用标准，提供最佳用户体验。

### 新增功能

#### 1. 辅助脚本：`autodev-helper.sh`

```bash
#!/bin/bash
# AutoDev 辅助脚本

AUTODEV_DIR=".autodev"
STATE_FILE="$AUTODEV_DIR/state.json"

case "$1" in
  init)
    # 初始化 AutoDev 目录
    mkdir -p "$AUTODEV_DIR/instructions"
    echo '{"version":"1.0","current_phase":1}' > "$STATE_FILE"
    echo "✅ AutoDev initialized"
    ;;

  checkpoint)
    # 创建 Phase 2 检查点
    git add -A
    STASH_ID=$(git stash create)
    echo "$STASH_ID" > "$AUTODEV_DIR/phase2-checkpoint"
    echo "✅ Checkpoint created: $STASH_ID"
    ;;

  task-start)
    # 记录任务起点
    COMMIT=$(git rev-parse HEAD)
    echo "$COMMIT" > "$AUTODEV_DIR/task-start"
    echo "✅ Task start: $COMMIT"
    ;;

  rollback-task)
    # Level 1 回退
    if [ ! -f "$AUTODEV_DIR/task-start" ]; then
      echo "❌ No task checkpoint found"
      exit 1
    fi
    COMMIT=$(cat "$AUTODEV_DIR/task-start")
    git checkout "$COMMIT"
    git clean -fd
    echo "✅ Rolled back to task start: $COMMIT"
    ;;

  rollback-phase2)
    # Level 2 回退
    if [ ! -f "$AUTODEV_DIR/phase2-checkpoint" ]; then
      echo "❌ No Phase 2 checkpoint found"
      exit 1
    fi
    STASH_ID=$(cat "$AUTODEV_DIR/phase2-checkpoint")
    git stash apply "$STASH_ID"
    echo "✅ Rolled back to Phase 2 checkpoint"
    ;;

  state)
    # 读取状态
    if [ -f "$STATE_FILE" ]; then
      cat "$STATE_FILE" | jq '.'
    else
      echo "❌ No state file found"
    fi
    ;;

  update-state)
    # 更新状态（从 stdin 接收 JSON）
    cat > "$STATE_FILE"
    echo "✅ State updated"
    ;;

  retry-inc)
    # retry_count++
    CURRENT=$(cat "$STATE_FILE" | jq '.retry_count // 0')
    NEW=$((CURRENT + 1))
    cat "$STATE_FILE" | jq ".retry_count = $NEW" > "$STATE_FILE.tmp"
    mv "$STATE_FILE.tmp" "$STATE_FILE"
    echo "$NEW"
    ;;

  *)
    echo "Usage: $0 {init|checkpoint|task-start|rollback-task|rollback-phase2|state|update-state|retry-inc}"
    exit 1
    ;;
esac
```

#### 2. Skill 中调用脚本

```markdown
## Phase 2 检查点创建

```bash
Bash("./autodev-helper.sh checkpoint")
```

## 记录任务起点

```bash
Bash("./autodev-helper.sh task-start")
```

## Level 1 回退

```bash
Bash("./autodev-helper.sh rollback-task")
```

## 更新状态

```bash
# 构造新状态 JSON
new_state='{"version":"1.0","current_phase":3,...}'
echo "$new_state" | Bash("./autodev-helper.sh update-state")
```

## 增加重试计数

```bash
retry_count=$(Bash("./autodev-helper.sh retry-inc"))
```
```

#### 3. Level 3 人工介入增强

提供更详细的诊断信息：
```markdown
## 🚨 需要人工介入

**循环历史**：
- Level 0: 尝试 3 次 → 失败（TypeError）
- Level 1: 任务重构 → 尝试 2 次 → 失败（仍然 TypeError）
- Level 2: 整体重规划 → 尝试 1 次 → 失败（依赖冲突）

**Git 状态**：
- 当前分支：feature/login
- Phase 2 检查点：abc123...
- 最后任务起点：def456...

**可能的根因（AI 推测）**：
1. 验收标准可能与现有架构冲突
2. 技术栈限制未被充分考虑
3. 需要引入新依赖但被约束禁止

**建议的行动**：
🔸 选项A：调整验收标准，简化需求
🔸 选项B：允许引入必要的依赖
🔸 选项C：更换技术方案（需要详细讨论）
🔸 选项D：暂停此功能
```

### 验收标准

- [ ] v0.3 的所有功能正常
- [ ] 辅助脚本能正确执行所有操作
- [ ] Level 3 人工介入提供详细诊断
- [ ] 状态管理完全可靠（无遗忘风险）
- [ ] 中断恢复 100% 准确
- [ ] 支持多个并行 AutoDev 会话（通过不同目录）

---

## 实施路线图

### Week 1: v0.1 基础版
- [ ] 创建 `toolchain/skills/aw-kernel/autodev/v0.1/SKILL.md`
- [ ] 实现 Phase 1-4 基础流程
- [ ] 实现 Level 0 循环
- [ ] 用户测试 + 收集反馈

### Week 2: v0.2 增强版
- [ ] 创建 `.autodev/` 目录结构
- [ ] 实现状态文件读写
- [ ] 实现 Git 检查点
- [ ] 实现 Level 1 回路
- [ ] 用户测试 + 验证恢复能力

### Week 3: v0.3 完整版
- [ ] 提取指令到外部文件
- [ ] 精简 Skill Prompt
- [ ] 实现 Level 2 回路
- [ ] 实现指令刷新机制
- [ ] 用户测试 + 性能调优

### Week 4: v1.0 生产版
- [ ] 开发 autodev-helper.sh 脚本
- [ ] 集成脚本到 Skill
- [ ] 完善 Level 3 诊断
- [ ] 编写用户文档
- [ ] 最终验收 + 发布

---

## 关键设计决策

### 1. 为什么分多个版本？

- **降低风险**：先验证核心流程可行性
- **快速迭代**：每个版本都能交付可用功能
- **用户反馈**：逐步收集真实使用场景
- **技术验证**：逐步验证 LLM 的能力边界

### 2. 状态管理演进路径

| 版本 | 状态存储 | 可靠性 | 复杂度 |
|------|---------|-------|--------|
| v0.1 | TodoWrite 内存 | 低 | 低 |
| v0.2 | .autodev/state.json | 中 | 中 |
| v0.3 | 外部指令 + state.json | 高 | 高 |
| v1.0 | 脚本辅助管理 | 极高 | 中（脚本封装） |

### 3. 回路层级演进

| 版本 | 回路层级 | 自动恢复能力 | 人工介入频率 |
|------|---------|------------|------------|
| v0.1 | Level 0 | 无 | 高 |
| v0.2 | Level 0-1 | 任务级 | 中 |
| v0.3 | Level 0-2 | 项目级 | 低 |
| v1.0 | Level 0-3 | 完整诊断 | 极低 |

---

## 总结

这个多版本迭代计划的核心思想：

1. **IDEA-005 的本地化缓存** → 解决状态管理和指令遗忘问题
2. **渐进式增强** → 每个版本都可用，逐步增加复杂度
3. **快速验证** → 先验证核心假设，再投入完整开发
4. **用户导向** → 基于真实反馈调整方向

浮浮酱建议主人从 **v0.1 基础版**开始，验证核心流程可行后，再决定是否继续 v0.2/v0.3 的开发喵～ ฅ'ω'ฅ
