# AW-Kernel 日志系统文档

> 版本：2.0.0
> 最后更新：2026-01-08
> 状态：✅ 已实施（Phase 2 - Hooks 方案）

---

## 目录

1. [概述](#概述)
2. [架构设计](#架构设计)
3. [日志格式](#日志格式)
4. [日志查询](#日志查询)
5. [常见问题](#常见问题)

---

## 概述

AW-Kernel 日志系统是一个轻量级的 Agent 执行记录系统，旨在提供：

- ✅ **可观测性**：了解 Agent 何时被调用、执行了什么、结果如何
- ✅ **可追溯性**：问题发生时能回溯完整上下文
- ✅ **可分析性**：收集性能指标、识别改进点

### 设计原则

| 原则 | 说明 |
|------|------|
| **不造轮子** | 复用 `.autoworkflow/` 现有日志层 |
| **零 Token** | 使用 Hooks 自动记录，不占用 Agent 上下文 |
| **100% 可靠** | 系统级触发，不依赖 LLM 自觉 |
| **有序存储** | JSONL 格式天然按时间顺序追加 |

---

## 架构设计

### 实现方式：Claude Code Hooks

日志系统通过 Claude Code 的 Hooks 机制实现，**无需在 Agent Prompt 中嵌入任何日志指令**。

```
项目根目录/
├── .claude/
│   ├── settings.json              # Hook 配置
│   └── hooks/
│       └── agent-logger.py        # 日志记录 Hook 脚本
└── .autoworkflow/
    └── logs/
        └── claude-code/
            └── feedback.jsonl     # 所有 Agent 日志
```

### Hook 事件

| 事件 | 触发时机 | 记录内容 |
|------|---------|---------|
| `PreToolUse` (Task) | Agent 启动前 | agent_start |
| `SubagentStop` | Agent 结束后 | agent_end |

### 优势对比

| 对比项 | 旧方案（Prompt 内嵌） | 新方案（Hooks） |
|--------|---------------------|----------------|
| Token 消耗 | ~80 行/Agent | **0** |
| 上下文污染 | 有 | **无** |
| 可靠性 | 依赖 LLM 自觉 | **系统级保证** |
| 维护成本 | 每个 Agent 都要改 | **一处配置** |

### 配置说明

**1. Hook 配置文件：`.claude/settings.json`**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/agent-logger.py\""
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/agent-logger.py\""
          }
        ]
      }
    ]
  }
}
```

**2. Hook 脚本：`.claude/hooks/agent-logger.py`**

脚本自动从 stdin 接收事件数据，解析 Agent 信息并写入日志文件。

---

## 日志格式

### JSONL 格式说明

每条日志占一行，每行是一个独立的 JSON 对象：

```jsonl
{"ts":"2026-01-07T10:30:22Z","tool":"claude-code","session":"session_20260107_103022_12345","kind":"agent_start","agent":"code-analyzer","task":"分析 src/ 目录的代码质量"}
{"ts":"2026-01-07T10:31:02Z","tool":"claude-code","session":"session_20260107_103022_12345","kind":"agent_end","agent":"code-analyzer","status":"success","duration_ms":40000,"summary":"发现 3 个改进点"}
```

### 字段规范

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `ts` | string | ✅ | ISO 8601 UTC 时间戳（如 `2026-01-07T10:30:22Z`） |
| `tool` | string | ✅ | 固定为 `"claude-code"` |
| `session` | string | ✅ | Session ID（格式：`session_YYYYMMDD_HHMMSS_PID`） |
| `kind` | string | ✅ | 事件类型：`agent_start` / `agent_end` / `error` |
| `agent` | string | ✅ | Agent 名称（如 `code-analyzer`） |
| `task` | string | ⚪ | 任务描述（`kind=agent_start` 时） |
| `status` | string | ⚪ | 执行状态（`kind=agent_end` 时）：`success` / `error` |
| `duration_ms` | number | ⚪ | 执行耗时毫秒（`kind=agent_end` 时） |
| `summary` | string | ⚪ | 执行摘要（`kind=agent_end` 时） |
| `error` | string | ⚪ | 错误描述（`kind=error` 时） |

### 事件类型

| kind | 触发时机 | 必需字段 |
|------|---------|---------|
| `agent_start` | Agent 开始执行 | `ts`, `tool`, `session`, `kind`, `agent`, `task` |
| `agent_end` | Agent 完成执行 | `ts`, `tool`, `session`, `kind`, `agent`, `status`, `duration_ms`, `summary` |
| `error` | Agent 执行出错 | `ts`, `tool`, `session`, `kind`, `agent`, `error` |

---

## 日志查询

日志查询分为三个层级，按需选择：

| 层级 | 工具 | 依赖 | 适用场景 |
|------|------|------|---------|
| **基础查询** | grep / tail | ✅ 零依赖 | 日常查看、简单过滤 |
| **高级查询** | Python 脚本 | ✅ 复用 Python | 聚合统计、复杂过滤 |
| **进阶查询** | jq | ⚠️ 需安装 | 专业用户、复杂转换 |

---

### 基础查询（零依赖，开箱即用）⭐

使用 `grep`、`tail` 等系统自带工具，**无需安装任何依赖**。

#### 1. 查看最近 10 条日志

```bash
tail -n 10 .autoworkflow/logs/claude-code/feedback.jsonl
```

#### 2. 查询某个 Agent 的所有日志

```bash
grep '"agent":"code-analyzer"' .autoworkflow/logs/claude-code/feedback.jsonl
```

#### 3. 查询所有错误日志

```bash
grep '"kind":"error"' .autoworkflow/logs/claude-code/feedback.jsonl
```

#### 4. 查询某个 Session 的日志

```bash
grep '"session":"session_20260107_103022_12345"' .autoworkflow/logs/claude-code/feedback.jsonl
```

#### 5. 统计各 Agent 的调用次数

```bash
grep -o '"agent":"[^"]*"' .autoworkflow/logs/claude-code/feedback.jsonl | sort | uniq -c
```

**输出示例**：
```
     15 "agent":"code-analyzer"
      8 "agent":"code-debug-expert"
     12 "agent":"feature-shipper"
```

#### 6. 统计成功/失败次数

```bash
grep -o '"status":"[^"]*"' .autoworkflow/logs/claude-code/feedback.jsonl | sort | uniq -c
```

#### 7. 查看今天的日志

```bash
grep "$(date +%Y-%m-%d)" .autoworkflow/logs/claude-code/feedback.jsonl
```

#### 8. 查看日志文件大小和行数

```bash
wc -l .autoworkflow/logs/claude-code/feedback.jsonl  # 行数
ls -lh .autoworkflow/logs/claude-code/feedback.jsonl  # 文件大小
```

---

### 高级查询（Python 脚本）

使用 `.autoworkflow/tools/query-logs.py` 脚本进行更复杂的查询。

**优势**：复用 Python（claude_autoworkflow.py 已依赖），无需额外安装。

#### 基本用法

```bash
# 查看帮助
python .autoworkflow/tools/query-logs.py --help

# 查询某个 Agent 的日志
python .autoworkflow/tools/query-logs.py --agent code-analyzer

# 查询错误日志
python .autoworkflow/tools/query-logs.py --kind error

# 查询最近 N 条
python .autoworkflow/tools/query-logs.py --limit 20

# 查看统计信息
python .autoworkflow/tools/query-logs.py --stats
```

#### 组合查询

```bash
# 查询 code-analyzer 的错误日志
python .autoworkflow/tools/query-logs.py --agent code-analyzer --kind error

# 查询今天的日志
python .autoworkflow/tools/query-logs.py --date today

# 导出为 CSV
python .autoworkflow/tools/query-logs.py --format csv > logs.csv
```

---

### 进阶查询（jq，可选安装）

如果你需要更强大的 JSON 查询能力，可以安装 `jq`：

```bash
# 安装 jq
brew install jq        # macOS
sudo apt install jq    # Ubuntu/Debian
```

#### jq 查询示例

```bash
# 格式化输出
tail -n 10 .autoworkflow/logs/claude-code/feedback.jsonl | jq '.'

# 查询某个 Agent
cat .autoworkflow/logs/claude-code/feedback.jsonl | jq 'select(.agent=="code-analyzer")'

# 统计平均执行时间
cat .autoworkflow/logs/claude-code/feedback.jsonl | \
  jq -s 'group_by(.agent) | map({agent: .[0].agent, avg_ms: ([.[] | .duration_ms // 0] | add / length)})'

# 按日期范围查询
cat .autoworkflow/logs/claude-code/feedback.jsonl | \
  jq 'select(.ts >= "2026-01-07T00:00:00Z" and .ts <= "2026-01-07T23:59:59Z")'

# 导出为 CSV
cat .autoworkflow/logs/claude-code/feedback.jsonl | \
  jq -r '[.ts, .agent, .kind, .status // ""] | @csv' > logs.csv
```

---

### 让 LLM 帮你分析日志

最简单的方式：直接让 Claude Code 帮你分析！

**示例 Prompt**：
```
请帮我分析 .autoworkflow/logs/claude-code/feedback.jsonl 中的日志：
1. 统计各 Agent 的调用次数
2. 找出执行时间最长的 5 次调用
3. 检查是否有错误记录
```

---

### 查询方式对比

| 查询需求 | 基础 (grep) | 高级 (Python) | 进阶 (jq) |
|---------|-------------|---------------|-----------|
| 查看最近日志 | ✅ `tail` | ✅ `--limit` | ✅ `tail \| jq` |
| 按 Agent 过滤 | ✅ `grep` | ✅ `--agent` | ✅ `select()` |
| 按类型过滤 | ✅ `grep` | ✅ `--kind` | ✅ `select()` |
| 统计调用次数 | ✅ `uniq -c` | ✅ `--stats` | ✅ `group_by` |
| 平均执行时间 | ❌ | ✅ `--stats` | ✅ `add/length` |
| 日期范围过滤 | ⚠️ 有限 | ✅ `--date` | ✅ `select()` |
| 导出 CSV | ❌ | ✅ `--format csv` | ✅ `@csv` |
| 格式化输出 | ❌ | ✅ 默认美化 | ✅ `jq '.'` |

**推荐**：日常使用基础查询，复杂分析用 Python 脚本或让 LLM 帮忙！

---

## 常见问题

### Q1: 如何清空日志文件？

**手动清空**：
```bash
: > .autoworkflow/logs/claude-code/feedback.jsonl
```

**备份后清空**：
```bash
mv .autoworkflow/logs/claude-code/feedback.jsonl \
   .autoworkflow/logs/claude-code/feedback.$(date +%Y%m%d).jsonl.bak
touch .autoworkflow/logs/claude-code/feedback.jsonl
```

### Q2: 日志文件会变得很大吗？

**不会**。根据测试：
- 每条日志约 200 字节
- 1000 次 Agent 调用 ≈ 200 KB
- 即使几千次调用，文件也只有几百 KB

### Q3: 如何查看特定时间段的日志？

使用 `jq` 的时间过滤（见"按日期范围查询"示例）。

### Q4: 如何让 LLM 帮我分析日志？

**示例 Prompt**：
```
请帮我分析 .autoworkflow/logs/claude-code/feedback.jsonl 中的日志，
找出 code-analyzer 这个 Agent 的所有调用记录，并总结：
1. 总调用次数
2. 平均执行时间
3. 是否有失败记录
```

### Q5: Session ID 不一致怎么办？

**原因**：LLM 在长对话中可能忘记 `SESSION_ID` 变量。

**解决方案**：
1. **Phase 1**：容忍偶尔的不一致，通过时间范围查询
2. **Phase 2**：使用归档脚本合并同一时间段的日志

### Q6: 如何在非 Git 项目中使用？

**完全支持**！日志系统不依赖 Git，只需要 `.autoworkflow/` 目录即可。

初始化：
```bash
python Claude/scripts/claude_autoworkflow.py init
```

### Q7: Windows 上时间戳生成有问题怎么办？

**推荐方案**：在 Git Bash 中运行 Agent（支持 `date` 命令）

**备选方案**：使用 PowerShell 时间戳脚本
```powershell
& .autoworkflow\tools\get-timestamp.ps1
```

---

## 最佳实践

### 1. 定期查看日志

建议每周检查一次 Agent 调用情况：
```bash
# 查看本周的 Agent 调用统计
cat .autoworkflow/logs/claude-code/feedback.jsonl | \
  jq -r '.agent' | sort | uniq -c | sort -nr
```

### 2. 监控错误日志

```bash
# 定期检查是否有错误
cat .autoworkflow/logs/claude-code/feedback.jsonl | jq 'select(.kind=="error")' | tail -10
```

### 3. 性能分析

```bash
# 找出执行最慢的 10 次调用
cat .autoworkflow/logs/claude-code/feedback.jsonl | \
  jq 'select(.duration_ms) | {agent, duration_ms, task}' | \
  jq -s 'sort_by(.duration_ms) | reverse | .[:10]'
```

### 4. 定期备份

```bash
# 每月备份一次
tar -czf logs-backup-$(date +%Y%m).tar.gz .autoworkflow/logs/claude-code/
```

---

## 未来规划

### Phase 2（可选）

- [ ] Session 归档脚本（按需）
- [ ] 日志查询辅助脚本（如果用户反馈需要）
- [ ] 可视化仪表盘（如果项目规模变大）

### Phase 3（未来）

- [ ] 与 Hooks 系统集成（自动化日志记录）
- [ ] 日志分析 Agent（自动发现性能瓶颈）
- [ ] 实时监控面板

---

## 相关文档

- [TOOLCHAIN.md](TOOLCHAIN.md) - 工具链说明
- [STANDARDS.md](STANDARDS.md) - Agent 设计标准
- [ROADMAP.md](../../../ROADMAP.md) - 项目路线图

---

> 本文档随日志系统演进持续更新。最新版本请查看仓库中的 LOGGING.md 文件。
