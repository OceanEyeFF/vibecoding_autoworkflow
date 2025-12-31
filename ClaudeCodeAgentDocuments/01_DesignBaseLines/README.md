# Claude Code Agent 设计基线索引

> 创建时间：2024-12-31
> 状态：初始化完成，待逐个实施

---

## 一、文档总览

| 编号 | 文档 | 优先级 | 关联问题 | 状态 |
|------|------|-------|---------|------|
| IDEA-001 | [SubAgent 调用机制](./IDEA-001-subagent-call-mechanism.md) | P0 | P01 | 🔴 待实施 |
| IDEA-002 | [Agent 职责边界定义](./IDEA-002-agent-boundary-definition.md) | P1 | P02 | 🔴 待实施 |
| IDEA-003 | [鉴权 Agent 设计](./IDEA-003-permission-guard-agent.md) | P1 | P03 | 🔴 待实施 |
| IDEA-004 | [结构化交互协议](./IDEA-004-structured-interaction-protocol.md) | P1 | P04 | 🔴 待实施 |
| IDEA-005 | [本地化文档缓存](./IDEA-005-localized-instruction-cache.md) | P0 | P05 | 🔴 待实施 |
| IDEA-006 | [强制数据访问机制](./IDEA-006-mandatory-data-access.md) | P0 | P06 | 🔴 待实施 |

---

## 二、优先级分布

### P0 级（必须优先解决）

| 编号 | 核心改进点 | 预期收益 |
|------|-----------|---------|
| IDEA-001 | SubAgent 可被显式调用 | Agent 间真正协作 |
| IDEA-005 | 核心指令外置 + 刷新机制 | 避免上下文污染 |
| IDEA-006 | 强制先访问数据 | 阻止幻觉输出 |

### P1 级（重要改进）

| 编号 | 核心改进点 | 预期收益 |
|------|-----------|---------|
| IDEA-002 | 明确职责边界 | 清晰的使用指南 |
| IDEA-003 | 鉴权 Agent | 支持无人值守 |
| IDEA-004 | 统一输出 Schema | Agent 间可靠通信 |

---

## 三、实施路线图

```
Phase 1: 基础协议（Week 1-2）
├── IDEA-006: 强制数据访问机制
├── IDEA-004: 结构化交互协议
└── 产出：更新后的 Prompt 模板

Phase 2: 指令管理（Week 2-3）
├── IDEA-005: 本地化文档缓存
├── 更新 init 脚本
└── 产出：agent-instructions 目录结构

Phase 3: 多 Agent 协作（Week 3-4）
├── IDEA-001: SubAgent 调用机制
├── IDEA-002: Agent 职责边界
└── 产出：可协作的 Agent 系统

Phase 4: 安全与自动化（Week 4-5）
├── IDEA-003: 鉴权 Agent
├── CI 集成
└── 产出：可无人值守的系统
```

---

## 四、关键设计理念

### 4.1 从假协作到真协作

```
当前状态                          目标状态
─────────────                    ─────────────
单 Agent + 分散 Prompt   →       多 Agent + 显式调用
口头约定协作             →       结构化协议通信
边界模糊                 →       职责单一
```

### 4.2 从建议到强制

```
当前状态                          目标状态
─────────────                    ─────────────
"建议先查证后输出"       →       "无证据 = BLOCKED"
"可以写入 state.md"      →       "必须写入 + 刷新读取"
"遵循输出格式"           →       "不符合 Schema = 无效"
```

### 4.3 从集中到分散

```
当前状态                          目标状态
─────────────                    ─────────────
236 行 Prompt            →       50 行 Prompt + 外置指令
每次加载完整指令         →       按需加载 + 刷新机制
上下文易污染             →       可恢复的指令记忆
```

---

## 五、验收标准总览

### 最终目标

- [ ] Agent 可以真正调用 SubAgent（不是口头约定）
- [ ] 每个 Agent 有清晰的职责边界
- [ ] 输出遵循统一的 JSON Schema
- [ ] 没有证据时输出 BLOCKED
- [ ] 长对话不会丢失核心约束
- [ ] 可以在 CI 中无人值守运行

### 质量指标

| 指标 | 当前 | 目标 |
|------|-----|------|
| Agent 协作成功率 | 0%（假协作） | >90% |
| 幻觉输出率 | 高 | <5% |
| 指令遗忘率 | 高（长对话） | <10% |
| 无人值守可用性 | 不可用 | 可用（有安全保障） |

---

## 六、相关文件

### 问题诊断
- [问题诊断报告](../00_tmpfiles/claude-agents-issues-diagnosis.md)

### 源代码（待改进）
- `Claude/agents/feature-shipper.md`
- `Claude/agents/requirement-refiner.md`
- `Claude/agents/code-analyzer.md`
- `Claude/agents/code-debug-expert.md`
- `Claude/agents/system-log-analyzer.md`
- `Claude/skills/autoworkflow/SKILL.md`
- `Claude/skills/git-workflow/SKILL.md`

---

> 下一步：从 IDEA-006（强制数据访问）开始实施，因为它是所有改进的基础。
