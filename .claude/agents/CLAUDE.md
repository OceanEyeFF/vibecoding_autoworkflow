[根目录](../../CLAUDE.md) > **.claude/agents**

---

# Claude Code Agents 模块文档

## 变更记录 (Changelog)

### 2025-12-26 (自动化工具链)
- 新增 `claude_autoworkflow.py` 核心脚本（~700 行）
- 新增 `TOOLCHAIN.md` 工具链文档
- 更新 `feature-shipper.md` 添加自动化集成说明
- 新增 `scripts/` 和 `assets/templates/` 目录结构
- 支持与 Codex 混合使用（共享层 + 日志隔离层）

### 2025-12-26 01:02:28
- 初次生成模块文档
- 建立 Agent 清单与职责索引

---

## 模块职责

本模块包含适用于 **Claude Code** 的专业化 Agent 定义文件（Markdown 格式）。每个 Agent 定义了特定的工作模式、约束条件与输出规范。

**核心理念**：
- Agent 即文档：通过 Markdown + YAML front matter 定义行为
- 可复制部署：可将 Agent 文件复制到目标项目的 `.claude/agents/` 目录使用
- 模块化设计：中枢 Agent（feature-shipper）+ 专项 Agents（分析/调试/需求等）

---

## 入口与启动

### 使用方式

1. **在目标项目中使用**
   - 将所需 Agent `.md` 文件复制到目标项目的 `.claude/agents/` 目录
   - 在 Claude Code 中选择对应 Agent 名称启动

2. **Agent 发现机制**
   - Claude Code 会自动扫描项目根目录的 `.claude/agents/*.md` 文件
   - 每个 `.md` 文件的 `name` 字段即为 Agent 名称

### 示例：复制核心 Agent 到目标项目

```bash
# Windows
copy .claude\agents\feature-shipper.md <target-project>\.claude\agents\

# WSL/Ubuntu
cp .claude/agents/feature-shipper.md <target-project>/.claude/agents/
```

---

## 对外接口（Agent 清单）

### 中枢 Agent

#### feature-shipper
- **文件**：`feature-shipper.md`
- **职责**：闭环交付中枢，从需求到测试验证的完整循环
- **适用场景**：
  - 新增功能开发
  - Bug 修复并补测试
  - 按 spec/tasks 文档逐项实现
  - 在不熟悉的代码库内做可验证的改动
- **核心约束**：
  - 先明确验收标准与测试方式再动手
  - 每次只做小步改动，并用测试验证
  - 以"测试全绿"为唯一门槛
- **输出产物**：
  - `.autoworkflow/spec.md`（需求规格）
  - `.autoworkflow/state.md`（执行状态）
  - 代码变更（小步迭代）
  - gate 验证结果

---

### 专项 Agents

#### code-analyzer
- **文件**：`code-analyzer.md`
- **职责**：语言无关的代码结构与架构分析
- **适用场景**：
  - 分析陌生代码库拓扑
  - 生成架构文档（结构/健康度/接口）
  - 识别架构违规与技术债
- **核心特性**：
  - 不假设编程语言
  - 基于目录结构与调用关系推断
  - 生成三份文档：CodeStructure.md / CodesAnalysis.md / CodeApis.md
- **输出产物**：
  - `CodeStructure.md`（代码骨架与逻辑架构映射）
  - `CodesAnalysis.md`（架构健康度诊断）
  - `CodeApis.md`（接口契约指南）

#### requirement-refiner
- **文件**：`requirement-refiner.md`
- **职责**：将模糊需求转化为清晰可执行的最小可行迭代方案
- **适用场景**：
  - 用户提出模糊需求（如"做个社交APP"）
  - 需要收敛范围到 MVP
  - 需要拆解任务并排除非核心需求
- **核心流程**（五阶段强制）：
  1. 需求澄清（拆解为原子任务）
  2. 范围收缩（标记 must-have vs nice-to-have）
  3. 最小步进（定义 ≤3 步迭代，每步 ≤3 人日）
  4. 文档生成（需求精炼文档）
  5. 文档交付（含交互记录）
- **输出产物**：
  - 需求精炼文档
  - 交互记录文档

#### code-debug-expert
- **文件**：`code-debug-expert.md`
- **职责**：系统性调试与根因定位
- **适用场景**：
  - 复杂 Bug 定位
  - 日志分析与错误栈解读
  - 跨模块问题排查
- **核心方法**：
  - 假设-验证循环
  - 分层诊断（表层现象 → 中间原因 → 根本原因）
  - 最小可复现案例构造
- **输出产物**：
  - 根因分析报告
  - 修复建议与验证步骤

#### system-log-analyzer
- **文件**：`system-log-analyzer.md`
- **职责**：系统日志分析与事故复盘
- **适用场景**：
  - 生产故障分析
  - 性能问题排查
  - 时序事件关联分析
- **核心能力**：
  - 时间线重建
  - 异常模式识别
  - 根因推断与验证
- **输出产物**：
  - 日志分析报告
  - 时序图与根因链

#### code-project-cleaner
- **文件**：`code-project-cleaner.md`
- **职责**：代码项目清理与重构建议
- **适用场景**：
  - 代码库清理
  - 移除废弃代码
  - 依赖精简
- **核心策略**：
  - 静态分析（未使用代码检测）
  - 依赖图分析（循环依赖/冗余依赖）
  - 安全性清理建议
- **输出产物**：
  - 清理建议清单
  - 风险评估报告

#### stage-development-executor
- **文件**：`stage-development-executor.md`
- **职责**：阶段文档驱动的交付执行（偏重 Playwright）
- **适用场景**：
  - 按阶段文档（开发计划）逐步实现
  - Web 应用开发（需要 Playwright 测试）
  - 渐进式交付与验证
- **核心流程**：
  - 读取阶段文档（包含任务清单与验收标准）
  - 逐任务实现 + Playwright 测试验证
  - 阶段完成后生成总结报告
- **输出产物**：
  - 阶段实现代码
  - Playwright 测试用例
  - 阶段总结报告

---

## 关键依赖与配置

### 依赖关系

- **无外部依赖**：所有 Agent 定义均为纯 Markdown 文档
- **运行时依赖**：Claude Code（或兼容的 Markdown Agent 解析器）
- **可选工具链**：
  - `codex-skills/feature-shipper`（提供 `.autoworkflow/` 工具链）
  - `codex-skills/feedback-logger`（提供后台日志记录）

### 配置文件

- **Agent 定义**：每个 `.md` 文件的 YAML front matter
  ```yaml
  ---
  name: agent-name
  description: 单行描述
  model: sonnet | inherit
  ---
  ```

- **目标项目配置**（由 Agent 运行时生成）：
  - `.autoworkflow/spec.md`（需求规格）
  - `.autoworkflow/state.md`（执行状态）
  - `.autoworkflow/gate.env`（gate 命令配置）

---

## 数据模型

### Agent 定义结构

```markdown
---
name: <agent-name>          # Agent 标识符（用于 Claude Code 选择）
description: <单行描述>     # 显示在 Agent 选择列表中的说明
model: <sonnet|inherit>     # 推荐模型或继承宿主设置
---

<Agent 行为定义>
- 核心原则
- 工作流程
- 输入契约
- 输出规范
- 约束条件
```

### 产物文件结构

#### `.autoworkflow/spec.md`（由 feature-shipper 生成）
```markdown
# 需求规格

## 范围
- [功能点 1]
- [功能点 2]

## 非目标
- [排除项 1]

## 验收标准
- [ ] 标准 1
- [ ] 标准 2

## Gate 命令
- Build: <命令>
- Test: <命令>
```

#### `.autoworkflow/state.md`（由 feature-shipper 维护）
```markdown
# 执行状态

## 当前进度
- [x] 任务 1
- [ ] 任务 2（进行中）

## 最近 Gate 结果
- 时间: 2025-12-26T01:02:28Z
- 状态: PASS/FAIL
- 输出摘要: ...

## 下一步
- [待办项]
```

---

## 测试与质量

### Agent 行为验证

- **验证方式**：在真实项目中使用 Agent，检查：
  - 是否遵循约束（如：feature-shipper 先打磨 spec 再实现）
  - 产物是否符合规范（spec.md / state.md / 代码变更）
  - 是否达到预期效果（测试全绿）

- **典型验证场景**：
  - 用 feature-shipper 完成一个小功能（从需求到测试通过）
  - 用 requirement-refiner 收敛一个模糊需求
  - 用 code-analyzer 分析一个陌生代码库

### 质量保证

- **文档质量**：
  - 所有 Agent 定义必须包含完整的 YAML front matter
  - 约束条件清晰且可验证
  - 输出规范明确且可操作

- **跨 Agent 一致性**：
  - 术语统一（如：验收标准 / DoD / gate）
  - 产物路径统一（如：`.autoworkflow/`）
  - 命令格式统一（跨平台脚本命名规则）

---

## 常见问题 (FAQ)

### Q1: 如何选择合适的 Agent？
**A**: 根据任务类型选择：
- 需要闭环交付 → `feature-shipper`
- 需求模糊 → `requirement-refiner`
- 分析代码结构 → `code-analyzer`
- 调试复杂 Bug → `code-debug-expert`

### Q2: 可以同时使用多个 Agent 吗？
**A**: 可以，但建议分阶段使用：
1. 先用 `requirement-refiner` 收敛需求
2. 再用 `feature-shipper` 实现
3. 遇到问题用 `code-debug-expert` 定位

### Q3: Agent 生成的文件需要提交到 Git 吗？
**A**: 建议：
- `.autoworkflow/spec.md` → 可选（团队共享时提交）
- `.autoworkflow/state.md` → 不提交（个人工作状态）
- `.autoworkflow/gate.env` → 可选（团队统一 gate 时提交）

### Q4: 如何更新 Agent 定义？
**A**:
1. 在本仓库更新 `.claude/agents/*.md`
2. 复制更新后的文件到目标项目
3. Claude Code 会自动重新加载

---

## 相关文件清单

```
.claude/agents/
├── feature-shipper.md          # 中枢：闭环交付
├── code-analyzer.md            # 专项：代码分析
├── requirement-refiner.md      # 专项：需求收敛
├── code-debug-expert.md        # 专项：调试定位
├── system-log-analyzer.md      # 专项：日志分析
├── code-project-cleaner.md     # 专项：项目清理
├── stage-development-executor.md # 专项：阶段交付（Playwright）
└── CLAUDE.md                   # 本文档
```

---

## 扩展资源

- **根文档**：[../../CLAUDE.md](../../CLAUDE.md)
- **Codex Skills**：[../../codex-skills/](../../codex-skills/)
- **使用教程**：[../../README.md](../../README.md)
- **AI 使用指南**：[../../AI高效使用指南.md](../../AI高效使用指南.md)
