# Claude Code Skill 设计基线：指令模块化管理

> 编号：IDEA-005
> 优先级：P0
> 关联问题：P05（核心 Agent 无本地化文档缓存）
> 更新时间：2026-01-04（适配 Claude Code Skill 机制）

---

## 一、问题回顾

当前问题：
- 复杂 Skill（如 autodev）指令长度达 700+ 行
- 每次对话都要加载完整 Skill 文件
- 长对话后，原始指令会被稀释
- LLM 会"忘记"核心约束

---

## 二、设计目标

1. 核心指令模块化到独立文件
2. SKILL.md 只保留核心概念和导航
3. 在需要时通过 Read 工具"刷新"指令记忆
4. 避免上下文污染
5. **适配 Claude Code Skill 机制**（不依赖不支持的元数据字段）

---

## 三、设计方案

### 3.1 指令模块化架构（适配 Claude Code Skill）

**重要前提**：Claude Code 的 Skill 系统**不支持** `instruction_files` 元数据字段，无法声明式自动加载外部文件。

**替代方案**：在 Skill 目录中组织模块化文件，通过 SKILL.md 中的"启动协议"和"刷新机制"明确指导 Claude 在特定时机使用 Read 工具加载。

#### 目录结构示例（以 autodev 为例）

```
Claude/skills/aw-kernel/autodev/
├── SKILL.md                         # 核心 Skill（简化版，含启动协议和导航）
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

#### 跨 Skill 共享指令（可选）

```
Claude/skills/_shared/
├── tool-discipline.md               # 共享工具纪律（IDEA-006）
├── output-format.md                 # 共享输出格式
└── safety-rules.md                  # 共享安全规则
```

各 Skill 可以在启动协议中读取这些共享文件。

### 3.2 精简后的 SKILL.md（手动 Read 机制）

**注意**：由于 Claude Code 不支持 `instruction_files` 字段，需要在 Skill 正文中明确写出启动协议和刷新机制。

```yaml
---
name: autodev
description: >
  自动化开发工作流 - 四阶段流程 + 多层回路机制
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# AutoDev 自动化开发工作流

## 快速导航

详细指令已组织为模块化文档，按需读取：

**执行阶段**：
- Phase 1: `Claude/skills/aw-kernel/autodev/phases/phase-1-refinement.md`
- Phase 2: `Claude/skills/aw-kernel/autodev/phases/phase-2-planning.md`
- Phase 3: `Claude/skills/aw-kernel/autodev/phases/phase-3-iteration.md`
- Phase 4: `Claude/skills/aw-kernel/autodev/phases/phase-4-delivery.md`

**质量门禁**：
- G1-G4: `Claude/skills/aw-kernel/autodev/gates/gate-{1-4}-*.md`

**多层回路**：
- Level 0-3: `Claude/skills/aw-kernel/autodev/loops/loop-level-{0-3}-*.md`

## 启动协议（必须执行）

1. **首次启动**时读取核心指令：
   ```
   Read("Claude/skills/aw-kernel/autodev/phases/phase-1-refinement.md")
   ```

2. **检查状态文件**（如存在 `.autodev/state.json`）：
   ```
   Read(".autodev/state.json")
   ```
   根据 state.json 中的 `current_phase` 读取对应的 Phase 指令文件。

3. **输出状态报告**：当前处于哪个 Phase、哪个任务、重试次数等。

## 指令刷新机制（主动触发）

**必须主动刷新指令的情况**：

| 触发条件 | 刷新操作 |
|---------|---------|
| **每 5 轮对话** | Read 当前 Phase 的指令文件 |
| **Gate 失败** | Read 对应的 Gate 检查清单 + Loop 策略文件 |
| **用户说"你忘了 XXX"** | Read 所有相关指令文件（Phase + Gate + Loop） |
| **中断后恢复** | Read state.json + 当前 Phase + 当前 Loop Level 的指令文件 |

刷新时输出：
```
[指令刷新] 已重新加载：phases/phase-2-planning.md
```

## 核心原则（概览）

1. **人类在环**：每个 Phase 结束请求确认
2. **状态可见**：使用 TodoWrite 追踪进度
3. **可恢复**：通过 state.json 恢复中断
4. **小步迭代**：每次只做小步修改
5. **测试验证**：每个任务完成后必须测试

详细的 Phase 执行步骤、Gate 检查清单、Loop 策略请查阅对应的模块化文件。
```

### 3.3 模块化指令文件示例

#### `phases/phase-1-refinement.md`

```markdown
# Phase 1: 需求理解与精炼

## 目标
把模糊的需求转化为清晰的验收标准（DoD）。

## 执行步骤

1. **分析用户输入**
   - 识别需求类型（新功能 / Bug 修复 / 重构 / 优化）
   - 提取关键信息

2. **使用 AskUserQuestion 澄清**（最多 3 轮）
   - 问题必须聚焦在阻塞实现的歧义点
   - 避免过早讨论实现细节

3. **输出需求摘要**
   - 核心价值命题（一句话）
   - 功能范围（做什么 / 不做什么）
   - 验收标准（可测试的清单）

4. **执行 G1 门禁检查**
   - 详见 `gates/gate-1-completeness.md`
   - 通过 → Phase 2
   - 失败 → 回到步骤 2 补充信息

## 不可违背的约束

1. **先明确验收标准再动手**
   - 缺失时先补齐（最多问 3 个问题）
   - 没有明确 DoD 不开始编码

2. **不自作主张**
   - 遇到不确定的业务规则，停下来问

3. **工具纪律**（IDEA-006）
   - 先查证后输出
   - 先调用再回答
   - 结论必须有证据
```

#### `gates/gate-1-completeness.md`

```markdown
# G1 门禁：需求完整性检查

## 检查清单

- [ ] 验收标准已明确（≥3 条，可测试）
- [ ] 功能范围已界定（有"不做什么"）
- [ ] 核心价值已清晰（能一句话解释）
- [ ] 用户已确认需求理解

## 通过标准

**全部**检查项都为 ✅ 时才能进入 Phase 2。

## 失败处理

如果任一项为 ❌：
1. Read("Claude/skills/aw-kernel/autodev/phases/phase-1-refinement.md") 刷新指令
2. 使用 AskUserQuestion 补充缺失信息
3. 重新输出需求摘要
4. 再次执行 G1 检查
```

#### `loops/loop-level-0-instant-fix.md`

```markdown
# Level 0 回路：即时修复

## 触发条件

G3 门禁（测试）失败，且 retry_count ≤ 3

## 执行策略

1. **分析错误信息**
   - 读取完整的错误堆栈
   - 定位失败的具体测试用例

2. **定位问题原因**
   - Read 相关代码文件
   - 理解预期行为 vs 实际行为

3. **修复代码**
   - 使用 Edit 工具修改代码
   - 保持小步修改（≤10 行）

4. **重新测试**
   - Bash("npm test")
   - retry_count++

5. **判断结果**
   - ✅ 通过 → 标记任务 completed，进入下一任务
   - ❌ 失败且 retry < 3 → 回到步骤 1
   - ❌ 失败且 retry == 3 → 触发 **Level 1 回路**
```

### 3.4 指令刷新机制（手动触发）

在 SKILL.md 中明确写出刷新触发条件和对应操作：

```markdown
## 指令刷新触发条件（必须遵守）

当以下情况发生时，你**必须主动**使用 Read 工具刷新指令：

1. **每 5 轮对话**
   - 强制读取当前 Phase 的指令文件
   - 例如：Read("Claude/skills/aw-kernel/autodev/phases/phase-2-planning.md")

2. **用户说"你忘了 XXX"**
   - 立即读取所有相关指令文件（Phase + Gate + Loop）
   - 在响应中道歉并说明已刷新

3. **Gate 失败**
   - 读取对应的 Gate 检查清单
   - 读取对应的 Loop 策略文件
   - 例如：Read("gates/gate-2-executability.md") + Read("loops/loop-level-1-task-refactor.md")

4. **中断后恢复**
   - 读取 state.json
   - 根据 state.json 的 current_phase 和 failure_level 读取对应文件

刷新时输出：
```
[指令刷新] 已重新加载：
- phases/phase-2-planning.md
- gates/gate-2-executability.md
```
```

**关键点**：Claude Code 不会自动执行这些 Read 操作，需要在 Skill 正文中明确写出"当 X 发生时，必须 Read Y 文件"。

### 3.5 创建模块化指令文件

**手动创建**或通过脚本生成模块化指令文件目录结构。

#### 示例脚本（可选）

```bash
#!/bin/bash
# 为 autodev Skill 创建模块化指令目录

SKILL_DIR="Claude/skills/aw-kernel/autodev"

mkdir -p "$SKILL_DIR/phases"
mkdir -p "$SKILL_DIR/gates"
mkdir -p "$SKILL_DIR/loops"

# 创建 Phase 文件模板
for i in 1 2 3 4; do
  touch "$SKILL_DIR/phases/phase-$i-placeholder.md"
done

# 创建 Gate 文件模板
for i in 1 2 3 4; do
  touch "$SKILL_DIR/gates/gate-$i-placeholder.md"
done

# 创建 Loop 文件模板
for i in 0 1 2 3; do
  touch "$SKILL_DIR/loops/loop-level-$i-placeholder.md"
done

echo "✅ 模块化指令目录结构已创建"
```

**或者**使用 Claude Code 的 install-local 脚本集成这个功能。

---

## 四、预期收益

| 指标 | 改进前 | 改进后 |
|------|-------|-------|
| SKILL.md 主文件长度 | 700+ 行（autodev） | ~150 行（核心概念 + 导航） |
| 详细指令文件数 | 0（全部内联） | 12-15 个模块化文件（phases + gates + loops） |
| 指令稀释风险 | 高 | 低（手动刷新机制） |
| 可维护性 | 低（单文件过大） | 高（模块化管理） |
| 跨 Skill 共享 | 复制粘贴 | 可引用 `_shared/` 目录 |
| 指令定位速度 | 慢（需在长文件中搜索） | 快（直接打开对应模块文件） |

---

## 五、验收标准

- [ ] SKILL.md 主文件精简（核心概念 + 启动协议 + 刷新机制 + 导航）
- [ ] 详细指令模块化到独立 Markdown 文件（phases/ gates/ loops/）
- [ ] 有明确的启动协议（指导首次加载哪些文件）
- [ ] 有手动指令刷新机制（明确写出触发条件和 Read 操作）
- [ ] 可选：有跨 Skill 共享指令目录（`_shared/`）
- [ ] 模块化文件组织符合直觉（易于查找和维护）

---

## 六、实施建议

### 优先级 1（立即执行）
- 对现有复杂 Skill（如 autodev）进行模块化拆分
- 创建 phases/ gates/ loops/ 目录结构
- 在 SKILL.md 中添加启动协议和刷新机制

### 优先级 2（后续优化）
- 创建 `Claude/skills/_shared/` 目录存放跨 Skill 共享指令
- 编写脚本自动生成模块化目录结构
- 为其他 Skill 应用相同的模块化策略

### 优先级 3（长期维护）
- 定期检查指令刷新机制是否被遵守
- 根据实际使用情况调整模块粒度
- 收集 LLM"遗忘"指令的案例，优化刷新触发条件

---

## 七、相关文件

- 待修改：`Claude/skills/aw-kernel/autodev/SKILL.md`（精简并添加启动协议）
- 待创建：`Claude/skills/aw-kernel/autodev/phases/*.md`（Phase 详细指令）
- 待创建：`Claude/skills/aw-kernel/autodev/gates/*.md`（Gate 检查清单）
- 待创建：`Claude/skills/aw-kernel/autodev/loops/*.md`（Loop 策略）
- 可选创建：`Claude/skills/_shared/*.md`（跨 Skill 共享指令）

---

> **核心思想（更新）**：指令模块化 + 手动触发加载 + 主动刷新 = 抗遗忘
>
> **关键区别**：Claude Code Skill 不支持 `instruction_files` 元数据自动加载，需通过在 SKILL.md 中明确写出"当 X 发生时，Read Y 文件"来实现指令刷新。
