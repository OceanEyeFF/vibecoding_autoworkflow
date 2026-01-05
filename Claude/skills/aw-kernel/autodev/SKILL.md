---
name: autodev
description: >
  自动化开发工作流 - 从需求到交付的完整闭环。
  支持：需求精炼 → 任务拆分 → 迭代开发 → 测试验证 → Git 提交。
  包含：指令刷新机制、Gate 回路、状态持久化。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# AutoDev 自动化开发工作流

你现在进入 **AutoDev 自动开发模式**。

---

## 🔴 启动协议（每次进入必须执行）

### Step 1: 刷新核心指令

**每次进入 AutoDev 模式，必须重新读取本 Skill 文件的关键章节**：

```
强制刷新清单：
□ 核心原则（本节）
□ 状态机定义
□ Gate 定义
□ 回路机制
```

### Step 2: 检查执行状态

```bash
# 检查是否有正在进行的任务
# 通过 TodoWrite 状态判断
```

- 如果有 `in_progress` 任务 → 进入**恢复模式**
- 如果全部 `pending` 或无任务 → 进入**新建模式**

### Step 3: 确认当前 Phase

根据 TodoWrite 状态推断当前 Phase，输出：

```
## AutoDev 状态

**模式**：[新建/恢复]
**当前 Phase**：[1/2/3/4]
**当前任务**：[任务名称] 或 [无]
**下一步**：[具体行动]
```

---

## 核心原则

1. **人类在环**：每个 Phase 结束后请求确认，Gate 失败时请求指导
2. **状态可见**：使用 TodoWrite 追踪进度，作为"唯一真相来源"
3. **可恢复**：中断后通过 TodoWrite 状态恢复
4. **工具纪律**：No Evidence, No Output
5. **指令刷新**：长对话中定期刷新核心指令

---

## 状态机定义

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│ Phase 1  │───▶│ Phase 2  │───▶│ Phase 3  │───▶│ Phase 4  │ │
│ 需求精炼 │ G1 │ 任务规划 │ G2 │ 迭代开发 │ G3 │ 验收提交 │ │
└──────────┘    └──────────┘    └──────────┘    └──────────┘ │
     │               │               │               │       │
     │ FAIL          │ FAIL          │ FAIL          │ FAIL  │
     ▼               ▼               ▼               ▼       │
┌─────────────────────────────────────────────────────────┐  │
│                    回路处理器                           │  │
│  1. 分析失败原因                                        │  │
│  2. 刷新相关指令                                        │──┘
│  3. 回退到适当 Phase                                    │
│  4. 重试（最多 3 次，之后人工介入）                      │
└─────────────────────────────────────────────────────────┘
```

---

## Gate 定义（质量门禁）

### G1: 需求完整性门禁

**触发**：Phase 1 → Phase 2 转换时
**检查项**：
- [ ] 有明确的验收标准（至少 2 条）
- [ ] 有完成定义（DoD）
- [ ] 用户已确认理解正确

**失败处理**：
```
→ 回退到 Phase 1
→ 使用 AskUserQuestion 补充缺失信息
→ 重试（最多 3 次）
```

### G2: 规划可执行性门禁

**触发**：Phase 2 → Phase 3 转换时
**检查项**：
- [ ] 任务列表已创建（3-7 个任务）
- [ ] 每个任务有完成标准
- [ ] 验证命令已确定
- [ ] 用户已确认规划

**失败处理**：
```
→ 回退到 Phase 2
→ 重新分析项目结构
→ 调整任务粒度
```

### G3: 测试通过门禁

**触发**：每个任务完成时
**检查项**：
- [ ] 代码修改已完成
- [ ] 测试命令执行成功
- [ ] 无新增错误

**失败处理**：
```
→ 进入调试循环（最多 3 次）
→ 调试失败 → 请求人工指导
→ 用户可选择：继续调试 / 跳过任务 / 回滚
```

### G4: 交付完整性门禁

**触发**：Phase 4 完成时
**检查项**：
- [ ] 所有任务已完成
- [ ] 完整测试套件通过
- [ ] 验收标准全部满足

**失败处理**：
```
→ 识别未完成项
→ 回退到 Phase 3 处理遗漏
→ 或标记为"已知限制"并请求用户确认
```

---

## 回路机制（核心创新）

### 多层回路策略

**核心原则**：Modify 优先于回退，但回退优先于人工介入

```
┌─────────────────────────────────────────────────────────────┐
│                     G3 失败处理流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 0: 即时修复（1-3 次）                                │
│  ────────────────────────────                               │
│  • 分析错误信息                                             │
│  • 定位问题原因                                             │
│  • 修复代码                                                 │
│  • 重新测试                                                 │
│                                                             │
│           │ 失败 3 次                                       │
│           ▼                                                 │
│  Level 1: Git 回退 + 任务重构（1-2 次）                     │
│  ────────────────────────────────────                       │
│  • git checkout 恢复到任务开始前的状态                       │
│  • 分析为什么这个任务连续失败                                │
│  • 重新拆分或调整这个任务的实现方案                          │
│  • 用新方案重新尝试                                         │
│                                                             │
│           │ 新方案也失败                                    │
│           ▼                                                 │
│  Level 2: 回退 Phase 2 + 整体重规划（1 次）                 │
│  ────────────────────────────────────────                   │
│  • git checkout 恢复到 Phase 2 结束时的状态                  │
│  • 重新审视整体任务规划                                     │
│  • 可能需要调整验收标准或任务粒度                            │
│  • 重新拆分所有任务                                         │
│                                                             │
│           │ 整体重规划后仍然失败                             │
│           ▼                                                 │
│  Level 3: 人工介入                                          │
│  ──────────────────                                         │
│  • 需求本身可能有问题                                       │
│  • 请求用户帮助                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 回路触发条件汇总

| 触发条件 | 回路层级 | 回路行动 |
|---------|---------|---------|
| G1 失败 | - | 刷新 Phase 1 指令 → 补充需求信息 |
| G2 失败 | - | 刷新 Phase 2 指令 → 调整任务规划 |
| G3 失败 ≤3 次 | Level 0 | 即时调试修复 |
| G3 失败 >3 次 | Level 1 | **Git 回退 + 任务重构** |
| Level 1 失败 | Level 2 | **Git 回退 + Phase 2 重规划** |
| Level 2 失败 | Level 3 | 人工介入 |
| G4 失败 | - | 识别遗漏 → 回退 Phase 3 补充 |

### Git 回退策略

**关键**：每个阶段开始前创建检查点

```bash
# Phase 2 结束时（任务规划确认后）
git stash  # 或 git add . && git commit -m "checkpoint: phase2-done"

# 每个任务开始前
# 记录当前 HEAD：task_start_commit=$(git rev-parse HEAD)

# Level 1 回退：回到任务开始前
git checkout ${task_start_commit}
git clean -fd  # 清理未跟踪文件

# Level 2 回退：回到 Phase 2 结束时
git checkout ${phase2_checkpoint}
git clean -fd
```

### 任务重构策略（Level 1）

当一个任务连续失败 3 次后：

1. **Git 回退**到任务开始前的状态
2. **分析失败模式**：
   - 是技术方案问题？→ 换一种实现方式
   - 是任务粒度问题？→ 拆分成更小的子任务
   - 是依赖问题？→ 先完成前置任务
3. **重构任务**：
   ```
   原任务：实现用户登录
   ↓ 重构为
   子任务 A：实现登录表单 UI
   子任务 B：实现登录 API 调用
   子任务 C：实现登录状态管理
   ```
4. **更新 TodoWrite** 并重新执行

### 整体重规划策略（Level 2）

当 Level 1 也失败后：

1. **Git 回退**到 Phase 2 结束时的检查点
2. **重新审视**：
   - 验收标准是否合理？
   - 任务拆分是否正确？
   - 是否遗漏了关键依赖？
3. **调整规划**：
   - 可能需要简化验收标准
   - 可能需要改变技术方案
   - 可能需要增加/减少任务
4. **请求用户确认**新的规划
5. **重新进入 Phase 3**

### 指令刷新机制

**触发条件**：
1. **轮数触发**：每 5 轮对话强制刷新核心原则
2. **Gate 失败触发**：任何 Gate 失败时刷新相关 Phase 指令
3. **用户反馈触发**：用户说"你忘了 XXX"时立即刷新全部
4. **恢复模式触发**：从中断恢复时刷新全部

**刷新动作**（显式读取，避免依赖记忆）：

1. **使用 Read 工具重新读取 SKILL.md 关键章节**

   根据触发场景选择读取范围：

   **场景 A：Phase 指令刷新**（Gate 失败时）
   ```javascript
   // 当前在 Phase 1，刷新 Phase 1 + G1 定义
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=389, limit=60)
   // 读取 Phase 1 章节（第 389-449 行）

   // 当前在 Phase 3，刷新 Phase 3 + G3 定义 + 回路机制
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=567, limit=200)
   // 读取 Phase 3 + Level 0/1/2/3 回路定义
   ```

   **场景 B：全局刷新**（轮数触发、用户反馈、恢复模式）
   ```javascript
   // 步骤 1：读取状态机定义和核心原则
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=1, limit=100)
   // 读取文件头 + 状态机定义 + 核心原则

   // 步骤 2：读取当前 Phase 定义
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=${phase_start_line}, limit=50)

   // 步骤 3：读取 Gate 定义汇总
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=65, limit=50)
   // 读取 G1/G2/G3 定义表格
   ```

2. **读取后执行内部确认**

   ```
   ✅ 指令已刷新（显式读取）

   **刷新内容**：
   - [x] 当前 Phase 定义：Phase ${current_phase}
   - [x] 对应 Gate 检查项：${gate_name}
   - [x] 回路处理规则：Level 0/1/2/3
   - [x] 核心原则：[列出关键原则]

   **关键要点回顾**：
   1. [从读取的内容中提取的要点 1]
   2. [从读取的内容中提取的要点 2]
   3. [从读取的内容中提取的要点 3]

   现在继续执行当前 Phase...
   ```

3. **避免的错误模式**

   ❌ **错误**：仅依赖"内部回忆"刷新
   ```
   # 不要这样做
   "我重新确认了 Phase 3 的定义：实现任务..."  ← 可能是摘要，不准确
   ```

   ✅ **正确**：显式使用 Read 工具
   ```
   # 应该这样做
   Read("Claude/skills/aw-kernel/autodev/SKILL.md", offset=567, limit=200)
   "根据读取的内容，Phase 3 定义为：[精确引用]"  ← 基于实际读取
   ```

---

### 指令刷新快速参考表

| 刷新场景 | 读取章节 | offset | limit | 说明 |
|---------|---------|--------|-------|------|
| **G1 失败** | Phase 1 + G1 定义 | 389 | 60 | Phase 1 完整流程 |
| **G2 失败** | Phase 2 + G2 定义 | 483 | 60 | Phase 2 + 检查点创建 |
| **G3 失败** | Phase 3 + G3 定义 + 回路 | 567 | 200 | Phase 3 + Level 0/1/2 |
| **轮数触发** | 状态机 + 核心原则 | 1 | 100 | 文件头部分 |
| **用户反馈** | 完整状态机 | 1 | 650 | 全局刷新（如需要） |
| **恢复模式** | Gate 定义汇总 | 89 | 50 | G1/G2/G3 表格 |

**注意**：offset 和 limit 值为参考值，需根据 SKILL.md 的实际结构调整。

---

### 长对话防护策略

**问题**：超长对话（>100 轮）可能触发自动摘要，丢失 SKILL.md 细节

**防护措施**：

1. **定期写入 state.md**（每 20 轮对话）
   ```markdown
   ## 当前工作状态（轮次 ${round_number}）

   **Phase**：Phase ${current_phase}
   **任务进度**：${completed_tasks} / ${total_tasks}
   **最近 Gate 结果**：${latest_gate_result}
   **retry 计数**：${retry_count}

   **关键指令摘要**：
   - Phase ${current_phase} 目标：[...]
   - Gate ${current_gate} 检查项：[...]
   - 当前回路级别：Level ${current_level}
   ```

2. **Phase 切换时强制刷新**
   - 进入新 Phase 前，显式读取该 Phase 定义
   - 输出 Phase 切换确认

3. **关键决策点刷新**
   - 执行回路（Level 1/2/3）前
   - 委派 Agent 前
   - 用户确认后

---

## Phase 1: 需求理解与精炼

### 目标
把模糊的需求转化为清晰的验收标准（DoD）。

### 执行步骤

1. **分析用户输入**
   - 识别需求类型（新功能 / Bug修复 / 重构 / 优化）
   - 提取关键信息点

2. **使用 AskUserQuestion 澄清**（最多 3 轮）
   - 核心功能范围是什么？
   - 怎样算"完成"？（验收标准）
   - 有什么约束？（不能做什么）

   **如果 3 轮后仍不清晰**：委派 requirement-refiner Agent
   ```javascript
   Task({
     subagent_type: "general-purpose",
     description: "委派需求精炼",
     prompt: `使用 requirement-refiner Agent 精炼以下模糊需求：

     用户需求：${用户原始输入}
     已澄清内容：${前 3 轮问答总结}

     要求输出：
     1. 核心价值命题（一句话）
     2. 验收标准列表（至少 2 条，可验证）
     3. 明确的范围边界（做什么/不做什么）
     4. 关键约束条件
     `
   })
   ```
   接收精炼结果后，继续步骤 3

3. **输出需求摘要**
   ```
   ## 需求摘要

   **类型**：[新功能/Bug修复/重构/优化]
   **目标**：[一句话描述]
   **验收标准**：
   - [ ] 标准1
   - [ ] 标准2
   **约束**：
   - 不能做 X
   - 必须兼容 Y
   ```

4. **执行 G1 门禁检查**
   - 验收标准 ≥ 2 条？
   - 用户已确认？
   - **通过** → Phase 2
   - **失败** → 回路：补充信息后重试

### 快速跳过条件
如果用户输入**同时满足**以下条件，可跳过 Phase 1：
- 已包含明确的验收标准（≥ 2 条）
- 已说明完成定义
- 范围清晰无歧义
- 用户明确说"直接执行"

### Git 能力检测（Phase 1 → Phase 2 转换时执行）

**目的**：检测 Git 可用性，决定回路机制策略

```bash
# 检查是否为 Git 仓库
if git rev-parse --git-dir > /dev/null 2>&1; then
  # 检查是否有 commit 历史
  if git rev-parse HEAD > /dev/null 2>&1; then
    echo "✅ Git 仓库可用，有 commit 历史"
    GIT_AVAILABLE=true
    GIT_HAS_HISTORY=true
  else
    echo "⚠️  Git 仓库可用，但无 commit 历史（新仓库）"
    GIT_AVAILABLE=true
    GIT_HAS_HISTORY=false
  fi
else
  echo "⚠️  非 Git 仓库，回路机制将使用文件备份"
  GIT_AVAILABLE=false
  GIT_HAS_HISTORY=false
fi
```

**根据检测结果调整策略**：
- `GIT_AVAILABLE=true` + `GIT_HAS_HISTORY=true`: 使用完整 Git 回退策略
- `GIT_AVAILABLE=true` + `GIT_HAS_HISTORY=false`: 使用 git stash 作为回退
- `GIT_AVAILABLE=false`: 使用文件备份到 `.autoworkflow/backups/`

---

## Phase 2: 任务拆分与规划

### 目标
将需求拆分为可执行的任务列表，并创建里程碑。

### 执行步骤

1. **分析项目结构**（必须执行）
   ```bash
   Glob("**/package.json")  # 或其他项目配置文件
   Glob("src/**/*")         # 源码结构
   Read(README.md)          # 项目说明（如果存在）
   ```

2. **识别影响范围**
   - 需要修改哪些文件？
   - 需要新增哪些文件？
   - 有哪些依赖关系？

3. **确定验证命令**
   ```bash
   # 检测项目测试命令
   Read(package.json)  # 查看 scripts.test
   # 或
   Glob("**/pytest.ini")
   Glob("**/Makefile")
   ```

4. **拆分任务**（3-7 个为宜）
   - 每个任务应该独立可测试
   - 任务之间有清晰的依赖关系
   - 每个任务有明确的完成标准

5. **使用 TodoWrite 创建任务列表**
   ```javascript
   TodoWrite([
     { content: "任务1: ...", status: "pending", activeForm: "正在处理任务1" },
     { content: "任务2: ...", status: "pending", activeForm: "正在处理任务2" },
     ...
   ])
   ```

6. **执行 G2 门禁检查**
   - 任务数量 3-7 个？
   - 每个任务有完成标准？
   - 验证命令已确定？
   - 用户已确认？
   - **通过** → 创建检查点 → Phase 3
   - **失败** → 回路：调整规划后重试

7. **创建 Phase 2 检查点**（G2 通过后立即执行）

   **根据 Git 能力检测结果选择策略**：

   **策略 A：完整 Git 回退**（`GIT_HAS_HISTORY=true`）
   ```bash
   # 记录当前状态作为回退点
   git add -A
   git stash push -m "autodev-checkpoint-phase2"
   # 或者如果用户允许创建 commit
   # git commit -m "checkpoint: autodev phase2 complete"

   # 记录检查点标识
   PHASE2_CHECKPOINT=$(git stash list | head -1 | cut -d: -f1)
   echo "✅ Phase 2 检查点已创建（Git stash）"
   echo "检查点标识：$PHASE2_CHECKPOINT"
   ```

   **策略 B：文件备份**（`GIT_AVAILABLE=false` 或 `GIT_HAS_HISTORY=false`）
   ```bash
   # 创建备份目录
   mkdir -p .autoworkflow/backups/phase2

   # 复制当前工作区（排除 .git, node_modules 等）
   rsync -av --exclude='.git' --exclude='node_modules' \
         --exclude='.autoworkflow' \
         . .autoworkflow/backups/phase2/

   echo "✅ Phase 2 检查点已创建（文件备份）"
   echo "备份位置：.autoworkflow/backups/phase2/"
   ```

---

## Phase 3: 迭代开发

### 目标
逐个完成任务，每个任务都经过测试验证。

### 执行步骤（对每个任务循环）

1. **记录任务起点**（每个任务开始前）

   **策略 A：Git commit 记录**（`GIT_HAS_HISTORY=true`）
   ```bash
   # 记录当前 commit 作为任务回退点
   task_start_commit=$(git rev-parse HEAD)
   echo "✅ 任务起点已记录: ${task_start_commit}"
   ```

   **策略 B：文件快照**（`GIT_AVAILABLE=false` 或 `GIT_HAS_HISTORY=false`）
   ```bash
   # 创建任务快照目录
   TASK_ID=$(date +%Y%m%d_%H%M%S)
   mkdir -p .autoworkflow/backups/tasks/$TASK_ID

   # 复制当前状态
   rsync -av --exclude='.git' --exclude='node_modules' \
         --exclude='.autoworkflow/backups' \
         . .autoworkflow/backups/tasks/$TASK_ID/

   echo "✅ 任务起点已创建（文件快照）"
   echo "快照ID：$TASK_ID"
   ```

2. **更新任务状态**
   ```javascript
   TodoWrite([
     { content: "任务1", status: "completed", ... },
     { content: "任务2", status: "in_progress", ... },  // 当前
     { content: "任务3", status: "pending", ... },
   ])
   ```

3. **执行代码修改**

   **简单任务**（单文件、逻辑清晰）：
   - 使用 Read 理解现有代码
   - 使用 Edit/Write 修改代码
   - 保持小步修改，便于回滚

   **复杂任务**（多文件、逻辑复杂、涉及架构）：委派 feature-shipper Agent
   ```javascript
   // 判断标准：涉及 ≥3 个文件 或 修改 ≥50 行 或 跨模块依赖
   Task({
     subagent_type: "general-purpose",
     description: "委派复杂任务执行",
     prompt: `使用 feature-shipper Agent 执行以下任务：

     任务名称：${当前任务描述}
     验收标准：${任务完成标准}
     验证命令：${测试命令}
     涉及文件：${相关文件列表}

     要求：
     1. 执行完整的 feature-shipper 工作流
     2. 返回任务状态（completed/blocked）
     3. 提供变更摘要（修改的文件和行数）
     4. 如遇阻塞，返回详细的阻塞原因
     `
   })
   ```
   委派返回后，验证结果并更新 TodoWrite 状态

4. **执行 G3 门禁检查**
   ```bash
   Bash("npm test")  # 或项目对应的测试命令
   ```

5. **处理 G3 结果（多层回路）**

   **✅ 通过**：
   ```
   → 标记任务 completed
   → 进入下一个任务
   → 如果是里程碑结束，请求用户确认
   ```

   **❌ Level 0: 即时修复（retry ≤ 3）**：
   ```
   → retry < 2: 自行分析错误信息并修复
     - 分析错误信息
     - 刷新 Phase 3 调试指令
     - 定位问题原因
     - 修复并重新测试
     - retry++

   → retry == 2: 委派 code-debug-expert Agent（调试困难）
     Task({
       subagent_type: "general-purpose",
       description: "委派调试诊断",
       prompt: `使用 code-debug-expert Agent 诊断以下测试失败：

       错误信息：${测试错误输出}
       相关文件：${涉及的文件路径}
       失败次数：已尝试 2 次修复

       要求：
       1. 定位根因（必须有 Read/Bash 证据）
       2. 提供 2-3 种修复方案及风险评估
       3. 推荐最佳方案
       `
     })
     根据诊断结果修复并重新测试
     retry++
   ```

   **❌ Level 1: 任务回退 + 重构（Level 0 失败后）**：
   ```
   → 输出 Level 1 回路报告

   → 回退操作（根据 Git 能力）：

     **策略 A：Git 回退**（`GIT_HAS_HISTORY=true`）
     git checkout ${task_start_commit}
     # 恢复到任务开始前的 commit

     **策略 B：文件恢复**（`GIT_AVAILABLE=false` 或 `GIT_HAS_HISTORY=false`）
     rm -rf ./*  # 清空当前工作区（保留 .git 和 .autoworkflow）
     rsync -av .autoworkflow/backups/tasks/${TASK_ID}/ ./
     # 从备份目录恢复任务开始前的文件状态

   → 分析失败模式（技术方案/粒度/依赖）
   → 重构任务（拆分或换方案）
   → 更新 TodoWrite
   → 用新方案重新尝试（最多 2 次）
   ```

   **❌ Level 2: 回退 Phase 2 + 整体重规划（Level 1 失败后）**：
   ```
   → 输出 Level 2 回路报告

   → 回退操作（根据 Git 能力）：

     **策略 A：Git 回退**（`GIT_HAS_HISTORY=true`）
     git stash pop ${PHASE2_CHECKPOINT}
     # 恢复到 Phase 2 检查点（stash）

     **策略 B：文件恢复**（`GIT_AVAILABLE=false` 或 `GIT_HAS_HISTORY=false`）
     rm -rf ./*  # 清空当前工作区（保留 .git 和 .autoworkflow）
     rsync -av .autoworkflow/backups/phase2/ ./
     # 从备份目录恢复 Phase 2 检查点的文件状态

   → 重新审视验收标准和任务规划
   → 请求用户确认新规划
   → 重新进入 Phase 3
   ```

   **❌ Level 3: 人工介入（Level 2 失败后）**：
   ```
   → 输出人工介入请求
   → 需求本身可能有问题
   → 等待用户指导
   ```

### Level 1 回路报告格式

```
## 🔄 Level 1 回路：任务重构

**触发原因**：任务 [X] 连续失败 3 次

**失败分析**：
- 错误类型：[技术方案问题/粒度问题/依赖问题]
- 根因推测：[分析]

**回退操作**：
- Git 能力：[有历史/无历史/非 Git 仓库]
- 策略选择：[Git checkout / 文件恢复]
- 执行命令：
  [Git 策略] git checkout ${task_start_commit}
  [文件策略] rsync -av .autoworkflow/backups/tasks/${TASK_ID}/ ./
- 状态：已恢复到任务开始前

**任务重构**：
原任务：[原任务描述]
↓ 重构为
- 子任务 A：[描述]
- 子任务 B：[描述]

**下一步**：用重构后的方案重新尝试
```

### Level 2 回路报告格式

```
## 🔄 Level 2 回路：整体重规划

**触发原因**：Level 1 重构后仍然失败

**回退操作**：
- Git 能力：[有历史/无历史/非 Git 仓库]
- 策略选择：[Git stash pop / 文件恢复]
- 执行命令：
  [Git 策略] git stash pop ${PHASE2_CHECKPOINT}
  [文件策略] rsync -av .autoworkflow/backups/phase2/ ./
- 状态：已恢复到 Phase 2 结束时

**重新评估**：
- 验收标准是否需要调整？[是/否]
- 任务拆分是否合理？[是/否]
- 技术方案是否可行？[是/否]

**新规划建议**：
[列出调整后的任务规划]

**请确认新规划后继续** [确认/调整/放弃]
```

### Level 3 人工介入请求格式

```
## 🚨 需要人工介入

**情况说明**：
- Level 0 即时修复：失败 3 次
- Level 1 任务重构：失败
- Level 2 整体重规划：失败

**可能的根因**：
- 需求本身存在矛盾或不可行
- 技术约束未被充分考虑
- 需要额外的上下文或知识

**需要主人帮助**：
🔸 选项A：提供更多上下文或领域知识
🔸 选项B：调整需求/验收标准
🔸 选项C：暂停此功能，先处理其他任务
🔸 选项D：完全放弃此需求
```

### 里程碑检查点

每完成一个里程碑（通常 2-3 个任务）：
```
## 里程碑 X 完成

**已完成**：
- [x] 任务1
- [x] 任务2

**下一个里程碑**：
- [ ] 任务3
- [ ] 任务4

继续吗？[是/否/调整计划]
```

---

## Phase 4: 验收与提交

### 目标
确认所有任务完成，生成变更总结，提交代码。

### 执行步骤

1. **执行 G4 门禁检查**
   ```bash
   Bash("npm test")       # 完整测试
   Bash("npm run lint")   # 代码检查（如有）
   ```

2. **验收标准核对**
   - 逐条检查 Phase 1 定义的验收标准
   - 标记每条的完成状态

3. **生成变更总结**
   ```bash
   Bash("git diff --stat")
   Bash("git status")
   ```

4. **输出交付报告**
   ```
   ## 交付报告

   **验收标准**：
   - [x] 标准1 - 已满足
   - [x] 标准2 - 已满足

   **完成的任务**：
   - [x] 任务1
   - [x] 任务2
   - [x] 任务3

   **变更文件**：
   - src/xxx.ts (+50, -10)
   - src/yyy.ts (+20, -5)

   **测试结果**：✅ 全部通过 (15 passed)

   **已知限制**：（如有）
   - [限制说明]
   ```

5. **请求提交确认**
   - "主人，所有任务已完成并通过测试，确认提交吗？"

6. **执行 Git 操作**（仅在用户确认后）
   ```bash
   Bash("git add .")
   Bash("git commit -m 'feat(scope): 实现XXX功能'")
   # 如果用户要求 push
   Bash("git push")
   ```

---

## 中断与恢复

### 恢复协议

用户说 **"继续 autodev"** 或 **"恢复"** 时：

1. **刷新核心指令**（全部）
2. **读取 TodoWrite 状态**
3. **推断当前 Phase**：
   - 无任务 → Phase 1
   - 有任务但全 pending → Phase 2（用户未确认）
   - 有 in_progress 任务 → Phase 3
   - 全部 completed → Phase 4
4. **确认代码状态**：
   ```bash
   Bash("git status")
   Bash("git log -1 --oneline")
   ```
5. **输出恢复报告**并请求确认

### 恢复报告格式

```
## AutoDev 恢复

**上次状态**：Phase 3 - 迭代开发
**当前任务**：任务3（in_progress）
**已完成**：任务1, 任务2
**待完成**：任务3, 任务4, 任务5

**Git 状态**：
- 分支：feature/xxx
- 未提交更改：3 个文件

从任务3继续吗？[是/回滚/重新规划]
```

---

## 工具纪律（强制）

### No Evidence, No Output

| 陈述类型 | 必须的工具调用 |
|---------|--------------|
| "项目使用 X 框架" | Read(package.json) 或 Glob |
| "代码中有/没有 Y" | Grep 或 Read |
| "测试通过/失败" | Bash(test命令) 实际输出 |
| "任务 X 已完成" | TodoWrite 更新 |
| "当前在 Phase X" | TodoWrite 状态推断 |

### 禁止行为

- ❌ 猜测项目结构（必须 Glob/Read）
- ❌ 假设测试结果（必须 Bash 执行）
- ❌ 跳过 Gate 检查
- ❌ 跳过用户确认
- ❌ 未经允许执行 git push
- ❌ 遗忘后不刷新指令

---

## 指令刷新检查点

在以下时机，**必须内部确认**核心指令是否清晰：

| 时机 | 需要确认的指令 |
|------|---------------|
| 进入任意 Phase | 该 Phase 的执行步骤 |
| Gate 失败 | 回路处理规则 |
| 每 5 轮对话 | 核心原则 + 当前 Phase |
| 用户说"你忘了" | 全部刷新 |
| 从中断恢复 | 全部刷新 |

刷新后输出：
```
✅ 指令刷新：[刷新的内容]
当前状态：Phase X - [阶段名称]
下一步：[具体行动]
```

---

## Agent 委派机制（Task 工具）

### 设计理念

AutoDev 作为**工作流编排者**，在特定场景下可以通过 Task 工具委派专用 Agent 处理复杂子任务。

```
┌─────────────────────────────────────────────────┐
│                  /autodev Skill                  │
│              （工作流编排 + 状态管理）              │
├─────────────────────────────────────────────────┤
│                                                  │
│   Phase 1 ──委派──▶ requirement-refiner          │
│   （需求特别模糊时）    （需求精炼专家）             │
│                                                  │
│   Phase 3 ──委派──▶ feature-shipper              │
│   （独立子任务执行）    （代码交付专家）             │
│                                                  │
│   G3 失败 ──委派──▶ code-debug-expert            │
│   （复杂调试场景）      （调试诊断专家）             │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 委派触发条件

| 场景 | 触发条件 | 委派目标 |
|------|---------|---------|
| 需求模糊 | Phase 1 问答超过 3 轮仍不清晰 | requirement-refiner |
| 单任务执行 | Phase 3 中任务复杂度高、涉及多文件 | feature-shipper |
| 调试困难 | G3 Level 0 失败 2 次后 | code-debug-expert |

### 委派执行格式

```javascript
// 委派 requirement-refiner 精炼需求
Task({
  subagent_type: "general-purpose",
  description: "精炼模糊需求",
  prompt: `
    使用 requirement-refiner Agent 的方法论，帮我精炼以下需求：
    ${用户原始需求}

    要求输出：
    1. 核心价值命题
    2. 验收标准列表（至少 2 条）
    3. 明确的范围边界
  `
})

// 委派 feature-shipper 执行单个任务
Task({
  subagent_type: "general-purpose",
  description: "执行单任务",
  prompt: `
    使用 feature-shipper Agent 执行以下任务：

    任务：${当前任务描述}
    验收标准：${任务完成标准}
    验证命令：${测试命令}

    完成后返回：任务状态 + 变更摘要
  `
})

// 委派 code-debug-expert 调试
Task({
  subagent_type: "general-purpose",
  description: "诊断测试失败",
  prompt: `
    使用 code-debug-expert Agent 诊断以下测试失败：

    错误信息：${测试错误输出}
    相关文件：${涉及的文件路径}

    要求：
    1. 定位根因（必须有 Read/Bash 证据）
    2. 提供修复方案
    3. 评估修复风险
  `
})
```

### 委派决策流程

```
需求进入 Phase 1
      │
      ▼
  需求清晰度检测
      │
      ├── 清晰 ──────────────▶ 自行处理
      │
      └── 模糊（问答 >3 轮）──▶ Task 委派 requirement-refiner
                                    │
                                    ▼
                              接收精炼结果
                                    │
                                    ▼
                              继续 Phase 2
```

### 委派注意事项

1. **状态同步**：委派返回后，必须更新 TodoWrite 状态
2. **结果验证**：委派结果需要通过 Gate 检查
3. **不过度委派**：简单任务直接处理，不浪费 Token
4. **上下文传递**：委派时提供足够的上下文信息

---

## 使用示例

### 触发方式

```
用户：/autodev 我想给项目添加一个用户登录功能
用户：帮我实现一个登录功能，要有邮箱验证
用户：继续 autodev（从中断恢复）
```

### Gate 回路示例

```
[Phase 3] 迭代开发
浮浮酱：执行任务2...
浮浮酱：运行测试...
❌ G3 失败：2 个测试未通过

→ 回路触发：
  1. 刷新 Phase 3 调试指令
  2. 分析错误：TypeError in auth.ts:42
  3. 修复：添加空值检查
  4. 重试 G3...

✅ G3 通过，继续下一个任务
```

---

> ฅ'ω'ฅ 浮浮酱的自动开发模式现在有了"自我修复"能力喵～
> Gate 失败不可怕，回路机制会自动处理！
> 长对话也不怕遗忘，指令刷新机制保驾护航！
