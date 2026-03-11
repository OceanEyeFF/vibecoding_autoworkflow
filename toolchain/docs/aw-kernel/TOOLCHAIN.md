# Claude Code 自动化工具链文档

## 概述

本工具链为 Claude Code Agents 提供自动化能力，支持与 Codex 混合使用。核心设计原则：

1. **共享项目级状态**：`.autoworkflow/` 中的 `state.md`, `spec.md`, `gate.env` 等
2. **隔离 AI 软件级日志**：Claude Code 和 Codex 各自维护独立的日志/反馈文件
3. **软锁协调机制**：通过 `.owner` 文件避免并发冲突
4. **优雅降级**：检测到冲突时提示用户选择，而非直接报错

---

## 目录结构

### 工具链源码（本仓库）

```
toolchain/
├── scripts/
│   └── claude_autoworkflow.py     # 核心脚本（~700 行）
├── assets/
│   └── templates/
│       ├── tools/
│       │   ├── cc-aw.ps1          # Windows 包装脚本模板
│       │   └── cc-aw.sh           # Linux/WSL 包装脚本模板
│       ├── spec-template.md       # 需求规格模板
│       ├── state-template.md      # 执行状态模板
│       └── agent-config.json      # Agent 配置模板
└── agents/
    └── aw-kernel/
        ├── ship.md     # 中枢 Agent（可与工具链配合）
        └── TOOLCHAIN.md           # 本文档
```

### 目标项目（初始化后）

```
目标项目/
└── .autoworkflow/
    ├── state.md                   # 执行状态（共享）
    ├── spec.md                    # 需求规格（共享）
    ├── gate.env                   # Gate 配置（共享）
    ├── doctor.md                  # 诊断报告（共享）
    ├── model-policy.json          # 模型推荐策略（共享）
    ├── agent-config.json          # Agent 配置（共享）
    ├── .owner                     # 软锁文件
    ├── .gitignore                 # 本地文件忽略
    ├── history/                   # 操作历史（带来源标识）
    ├── tools/                     # 工具脚本（共享）
    │   └── claude_autoworkflow.py
    └── logs/                      # 日志隔离层
        ├── codex/                 # Codex 专属
        │   └── feedback.jsonl
        └── claude-code/           # Claude Code 专属
            └── feedback.jsonl
```

---

## 命令参考

### init - 初始化工具链

```bash
python claude_autoworkflow.py init [--force]
```

> 脚本位置：本仓库 `toolchain/scripts/claude_autoworkflow.py`。  
> 执行 init 后，会在目标项目生成 `.autoworkflow/tools/claude_autoworkflow.py`（后续可直接使用该副本）。

**功能**：
- 检测现有工具链（Codex/Claude Code/无）
- 创建 `.autoworkflow/` 目录结构
- 生成模板文件和工具脚本
- 获取所有权

**参数**：
- `--force, -f`：强制覆盖已有文件

**输出示例**：
```
🔍 检测到 Codex 工具链，进入混合模式...

✅ 初始化完成！
   共享层: /path/to/project/.autoworkflow
   日志层: /path/to/project/.autoworkflow/logs/claude-code
```

---

### doctor - 项目诊断

```bash
python claude_autoworkflow.py doctor [--write] [--update-state]
```

**功能**：
- 扫描项目，检测项目类型和工具
- 检查 autoworkflow 状态和 gate 配置
- 生成诊断报告

**参数**：
- `--write, -w`：写入 `doctor.md`
- `--update-state, -u`：更新 `state.md`

**检查项**：
| 类别 | 检查内容 |
|------|---------|
| 项目类型 | package.json, pyproject.toml, go.mod 等 |
| 工具链状态 | .autoworkflow/ 是否存在 |
| Gate 配置 | TEST_CMD 是否配置 |

**输出示例**：
```markdown
# Autoworkflow Doctor Report

## Host Info
- OS: nt
- Platform: windows
- Python: 3.11.0

## Project Markers
- package.json
- .github/workflows/

## Autoworkflow Status
- Initialized: yes
- Gate configured: yes
```

---

### set-gate - 配置 Gate

```bash
python claude_autoworkflow.py set-gate [--create] [--build CMD] [--test CMD] [--lint CMD]
```

**功能**：
- 创建或更新 `gate.env` 配置
- 定义"测试全绿"的具体命令

**参数**：
- `--create, -c`：如果不存在则创建 `gate.env`
- `--build, -b`：构建命令
- `--test, -t`：测试命令（必需）
- `--lint, -l`：Lint 命令
- `--format-check, -f`：格式检查命令

**示例**：
```bash
# Node.js 项目
python claude_autoworkflow.py set-gate --create --build "npm run build" --test "npm test"

# Python 项目
python claude_autoworkflow.py set-gate --create --test "pytest"
```

**gate.env 格式**：
```bash
BUILD_CMD=npm run build
TEST_CMD=npm test
LINT_CMD=npm run lint
```

---

### gate - 执行 Gate 验证

```bash
python claude_autoworkflow.py gate
```

**功能**：
- 读取 `gate.env` 配置
- 按顺序执行：Build → Test → Lint → FormatCheck
- 任一步骤失败则停止
- 自动追加结果到 `state.md`

**输出示例**：
```
🚀 开始 Gate 验证...

==> Build: npm run build
✅ Build 通过

==> Test: npm test
✅ Test 通过

🎉 Gate 通过！所有检查全绿！
```

**失败时**：
- 自动提取关键错误行（highlights）
- 记录最后 40 行输出（tail）
- 更新 `state.md` 带来源标识

---

### recommend-model - 智能模型推荐

```bash
python claude_autoworkflow.py recommend-model --intent <intent>
```

**功能**：
- 根据任务意图推荐合适的模型
- 检测项目状态（gate 是否失败等）
- 应用推荐规则

**参数**：
- `--intent, -i`：任务意图，可选值：
  - `doctor`：诊断（推荐轻量模型）
  - `init`：初始化（推荐轻量模型）
  - `implement`：实现（推荐中等模型）
  - `debug`：调试（推荐强模型）
  - `refactor`：重构（推荐强模型）

**推荐策略**：
| Profile | Claude | Codex | 适用场景 |
|---------|--------|-------|---------|
| light | haiku | gpt-4o-mini | doctor, init |
| medium | sonnet | gpt-4o | implement |
| heavy | opus | o1 | debug, refactor, gate 失败 |

**输出示例**：
```
🤖 模型推荐 (intent: debug)
   Profile: heavy
   Claude: opus
   Codex: o1
   Reason: Tests failing; use stronger model
   Signals: gate_failed
```

---

## 协调机制

### 所有权（.owner）

`.owner` 文件用于协调 Claude Code 和 Codex 的并发访问：

```json
{
  "tool": "claude-code",
  "session_id": "abc123",
  "acquired_at": "2025-12-26T10:30:00Z",
  "last_activity": "2025-12-26T10:35:00Z",
  "ttl_minutes": 30
}
```

**规则**：
1. 首次访问时获取所有权
2. 每次操作更新 `last_activity`
3. 30 分钟无活动自动释放
4. 检测到冲突时提示用户选择

### 来源标识

所有写入 `state.md` 的内容都带有来源标识：

```markdown
<!-- source: claude-code -->
<!-- timestamp: 2025-12-26T10:35:00Z -->

## Gate (2025-12-26T10:35:00Z)
- Status: PASS
```

---

## 日志隔离

### Claude Code 日志

路径：`.autoworkflow/logs/claude-code/`

文件：
- `feedback.jsonl`：事件日志（JSONL 格式）

日志格式：
```json
{
  "ts": "2025-12-26T10:35:00Z",
  "tool": "claude-code",
  "session": "abc123",
  "kind": "gate",
  "message": "Gate PASS",
  "data": {"exit_code": 0}
}
```

### Codex 日志

路径：`.autoworkflow/logs/codex/`

文件：
- `feedback.jsonl`：事件日志
- `feedback-watch.pid`：watch 进程 PID

---

## 与 Codex 混合使用

### 场景 1：先 Codex 后 Claude Code

1. Codex 初始化项目（`autoworkflow.py init`）
2. Claude Code 检测到 Codex 工具链
3. 自动进入混合模式（只创建日志隔离层）
4. 两者共享 `state.md` 等文件

### 场景 2：先 Claude Code 后 Codex

1. Claude Code 初始化项目
2. Codex 检测到现有工具链
3. Codex 自动复用共享层

### 场景 3：并发访问

1. Codex 正在运行（`.owner` 存在）
2. Claude Code 尝试访问
3. Claude Code 提示用户：
   - 等待 Codex 完成
   - 强制接管
   - 使用独立目录

---

## 配置文件

### agent-config.json

```json
{
  "version": "1.0.0",
  "tool_name": "claude-code",
  "auto_init": true,
  "auto_doctor": true,
  "auto_gate": true,
  "ownership": {
    "ttl_minutes": 30,
    "on_conflict": "prompt"
  },
  "model_policy": {
    "default": "sonnet",
    "intents": {
      "doctor": "sonnet",
      "implement": "sonnet",
      "debug": "opus",
      "refactor": "opus"
    }
  }
}
```

### model-policy.json

```json
{
  "version": "1.0.0",
  "profiles": {
    "light": {"claude": "haiku", "codex": "gpt-4o-mini"},
    "medium": {"claude": "sonnet", "codex": "gpt-4o"},
    "heavy": {"claude": "opus", "codex": "o1"}
  },
  "rules": [
    {"if": "gate_failed", "then": "heavy", "reason": "Tests failing; use stronger model"}
  ],
  "intents": {
    "doctor": "light",
    "implement": "medium",
    "debug": "heavy"
  }
}
```

---

## 常见问题

### Q1: 如何强制重新初始化？

```bash
python claude_autoworkflow.py init --force
```

### Q2: 如何查看当前所有权状态？

```bash
cat .autoworkflow/.owner
```

### Q3: 如何手动释放所有权？

删除 `.owner` 文件：
```bash
rm .autoworkflow/.owner
```

### Q4: 日志文件太大怎么办？

定期清理：
```bash
# 清空 Claude Code 日志
: > .autoworkflow/logs/claude-code/feedback.jsonl

# 清空 Codex 日志
: > .autoworkflow/logs/codex/feedback.jsonl
```

### Q5: 如何在 CI 中使用？

```yaml
# GitHub Actions 示例
- name: Run gate
  run: python .autoworkflow/tools/claude_autoworkflow.py gate
```

---

## 相关文档

- [ship.md](./ship.md) - 中枢 Agent 定义
- [GUIDE.md](./GUIDE.md) - 模块文档
- [根文档](../../../GUIDE.md) - 项目级文档
