# Claude 工作区架构分析

## 整体设计理念

这是一个**源资产分离** + **安装产物隔离** 的架构体系，遵循"单一真源"原则喵～

```
源资产（入库维护）          安装产物（生成，不入库）
     ↓                           ↓
toolchain/                    /.claude/
agents/                    agents/
skills/                    skills/
commands/                  commands/
```

---

## 1️⃣ 核心目录结构

### 📁 toolchain/ 源资产层

```
toolchain/
├── README.md                  # 快速开始指南
├── GUIDE.md                  # 不存在，但根 GUIDE.md 引用本层
│
├── agents/                    # 🤖 Agent 定义（核心）
│   ├── GUIDE.md             # Agent 模块指南
│   ├── TOOLCHAIN.md          # 自动化工具链文档
│   ├── feature-shipper.md    # 中枢 Agent（最重要）
│   ├── code-analyzer.md      # 代码结构分析
│   ├── requirement-refiner.md # 需求精炼
│   ├── code-debug-expert.md  # 系统化调试
│   ├── system-log-analyzer.md # 日志分析
│   │
│   ├── scripts/
│   │   ├── claude_autoworkflow.py  # 核心自动化引擎（~700行）
│   │   ├── claude_aw.ps1          # Windows 包装脚本
│   │   └── claude_aw.sh           # Linux/WSL 包装脚本
│   │
│   └── assets/templates/       # 模板资产（安装时复制）
│       ├── agent-config.json
│       ├── spec-template.md
│       ├── state-template.md
│       └── tools/
│           ├── cc-aw.ps1
│           └── cc-aw.sh
│
├── skills/                     # 🔧 可复用 Skills
│   ├── autoworkflow/          # 自动化工作流 skill
│   │   └── SKILL.md
│   └── git-workflow/          # Git 工作流 skill
│       └── SKILL.md
│
├── commands/                   # 🎯 可调用命令
│   └── autoworkflow/
│       └── feature-shipper.md
│
├── scripts/                    # 📦 安装脚本（跨平台）
│   ├── install-local.sh       # Linux/WSL 本地安装
│   ├── install-local.ps1      # Windows 本地安装
│   ├── uninstall-local.sh
│   └── uninstall-local.ps1
│
└── docs/
    └── repo-GUIDE.md         # 历史文档（已归档）
```

---

## 2️⃣ 工作流架构（Feature-Shipper 驱动）

### 🔄 闭环流程

```
┌─────────────────────────────────────────────┐
│  Feature-Shipper（中枢 Agent）              │
└────────────┬────────────────────────────────┘
             │
             ├─→ 1️⃣ 需求收敛
             │    Requirement-Refiner
             │    ↓ 产出 DoD/spec.md
             │
             ├─→ 2️⃣ 代码理解
             │    Code-Analyzer
             │    ↓ 理解现有架构
             │
             ├─→ 3️⃣ 实现
             │    Feature-Shipper
             │    ↓ 编码 + 测试
             │
             ├─→ 4️⃣ 门禁验证（Gate）
             │    Autoworkflow.py gate
             │    ↓ Build → Test → Lint → Format
             │
             └─→ 5️⃣ 交付
                  更新 state.md + PR 就绪
```

**关键约定**：无测试全绿不算完成 ⚠️

---

## 3️⃣ 自动化工具链（TOOLCHAIN）

### 核心组件

| 组件 | 位置 | 功能 |
|------|------|------|
| **claude_autoworkflow.py** | `agents/scripts/` | 核心引擎（700 行）|
| **Gate 执行器** | 内置 | Build→Test→Lint→Format 流程 |
| **State 管理器** | 内置 | 维护 `.autoworkflow/state.md` |
| **Model 推荐器** | 内置 | 根据任务意图推荐模型 |
| **所有权管理** | 内置 | `.owner` 文件协调并发 |

### 共享状态层（`.autoworkflow/`）

```
.autoworkflow/              # 项目级共享目录
├── state.md               # 🔑 执行状态（多 agent 协作界面）
├── spec.md                # 📋 需求规格
├── gate.env               # ⚙️ Gate 命令配置
├── doctor.md              # 🔍 诊断报告
├── model-policy.json      # 🤖 模型推荐策略
├── agent-config.json      # 🎯 Agent 配置
├── .owner                 # 🔒 软锁（并发协调）
├── .gitignore             # ⛔ 不入库
├── history/               # 📜 操作历史（带来源标识）
├── tools/
│   └── claude_autoworkflow.py  # 工具脚本副本
└── logs/                  # 📝 日志隔离
    ├── codex/             # Codex 独占
    │   └── feedback.jsonl
    └── claude-code/       # Claude Code 独占
        └── feedback.jsonl
```

**关键设计**：Claude Code 和 Codex 共享 `state.md` 等核心文件，但日志完全隔离 🎯

---

## 4️⃣ 安装流程

### 方式一：项目内安装（repo-local）

```bash
# macOS/Linux/WSL
bash toolchain/scripts/install-local.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File toolchain/scripts/install-local.ps1
```

**效果**：生成 `/.claude/agents`, `/.claude/skills`, `/.claude/commands`（不入库）

### 方式二：全局安装（推荐）

```bash
# 通过 CodeX/feature-shipper 的安装脚本
bash CodeX/codex-skills/feature-shipper/scripts/install-claude-global.sh
```

**效果**：安装到 `~/.claude/`（全局可用，不污染目标仓库）

---

## 5️⃣ Agent 生态

### 主线 Agents

| Agent | 用途 | 输入 | 输出 |
|-------|------|------|------|
| **feature-shipper** | 中枢驱动 | 需求文本 | 完整实现 + PR |
| **requirement-refiner** | 需求精炼 | 模糊描述 | 明确 DoD + 任务列表 |
| **code-analyzer** | 架构梳理 | 代码库 | 依赖图 + 分层视图 |
| **code-debug-expert** | 系统调试 | 错误 + 日志 | 假设→验证→根因 |
| **system-log-analyzer** | 事故分析 | 日志文件 | 时间线 + 根因假设 |

### Skills 继承

> 注意：子 agent 不自动继承 skills，需在 YAML 中显式声明 ⚠️

例如：`feature-shipper` 声明了 `skills: autoworkflow, git-workflow`

---

## 6️⃣ 关键文件详解

### 📄 state.md（协作界面）

```markdown
# Project State

<!-- source: claude-code -->
<!-- timestamp: 2025-12-26T10:35:00Z -->

## Gate (2025-12-26T10:35:00Z)
- Status: PASS
- Build: ✅
- Test: ✅
- Lint: ✅

## Last Implementation
- Task: 添加用户认证功能
- Agent: feature-shipper
- Status: COMPLETED
```

**特点**：
- 所有写入都带来源标识（claude-code / codex）
- 时间戳完整可追溯
- 自动追加，不覆盖历史

### ⚙️ gate.env（验证命令）

```bash
BUILD_CMD=npm run build
TEST_CMD=npm test
LINT_CMD=npm run lint
FORMAT_CHECK_CMD=npm run format:check
```

**用途**：定义"测试全绿"的具体命令集

### 🤖 model-policy.json（模型推荐）

```json
{
  "profiles": {
    "light": {"claude": "haiku", "codex": "gpt-4o-mini"},
    "medium": {"claude": "sonnet", "codex": "gpt-4o"},
    "heavy": {"claude": "opus", "codex": "o1"}
  },
  "intents": {
    "doctor": "light",
    "implement": "medium",
    "debug": "heavy"
  },
  "rules": [
    {"if": "gate_failed", "then": "heavy", "reason": "Tests failing"}
  ]
}
```

---

## 7️⃣ 核心原则

### 🎯 设计原则

| 原则 | 含义 | 示例 |
|------|------|------|
| **单一真源** | `toolchain/` 是唯一源代码 | 更新 toolchain/ 后跑安装脚本同步 |
| **共享+隔离** | 共享状态层，日志隔离 | `state.md` 共享，`logs/` 分离 |
| **门禁优先** | 无绿灯不交付 | Gate 失败自动建议用强模型 |
| **先验证后输出** | 结论必须有证据 | 所有输出都可追溯文件/行号 |

### 📝 工具纪律（强制）

1. **先查证后输出**：结论必须有可追溯证据
2. **先调用再回答**：不凭空补全
3. **标准步骤**：意图拆解 → 工具调用 → 限制边界 → 提纯信息
4. **长上下文**：多轮工作写入 `.autoworkflow/state.md`

---

## 8️⃣ 快速使用流程

### 初次使用（推荐全局安装）

```bash
# 1. 在本仓库运行全局安装
bash toolchain/scripts/install-global.sh  # 需补充脚本

# 2. 跳转到目标项目
cd /path/to/target-project

# 3. 初始化
python ~/.claude/agents/scripts/claude_autoworkflow.py init

# 4. 配置 Gate
python ~/.claude/agents/scripts/claude_autoworkflow.py set-gate --create \
  --test "pytest" \
  --lint "pylint src/"

# 5. 启动 Claude Code
claude

# 6. 选择 feature-shipper Agent，开始需求对话
```

### Claude Code 内部快捷命令

```bash
# 如果 UI 看不到 agents，用命令显式调用
/autoworkflow:feature-shipper 需求描述
```

---

## 9️⃣ 与 Codex 混合模式

### 三大场景

#### 场景 1：先 Codex 后 Claude Code
1. Codex 初始化 → 创建 `.autoworkflow/`
2. Claude Code 自动检测
3. 进入混合模式（仅创建日志隔离层）
4. 共享 `state.md`

#### 场景 2：先 Claude Code 后 Codex
1. Claude Code 初始化
2. Codex 自动复用

#### 场景 3：并发冲突
1. 检测到 `.owner` 存在（另一个工具在运行）
2. Claude Code 提示用户：
   - 等待另一个工具完成
   - 强制接管
   - 使用独立目录

---

## 🔟 常用路径速记

| 路径 | 用途 |
|------|------|
| `.claude/agents/feature-shipper.md` | 中枢 Agent 定义 |
| `.autoworkflow/tools/aw.ps1\|aw.sh` | 统一工具入口 |
| `.autoworkflow/state.md` | 进度 + 最近 Gate 输出 |
| `.autoworkflow/gate.env` | Build/Test/Lint 命令 |
| `.autoworkflow/logs/claude-code/` | Claude Code 日志 |

---

## 小贴士 💡

1. **复杂 PowerShell 引号**：直接编辑 `gate.env` 而非命令行
2. **多模块仓库**：优先同步 CI 配置或根 `GUIDE.md` 中的命令
3. **长日志**：定期清理 `.autoworkflow/logs/*/feedback.jsonl`
4. **不入库**：加 `.autoworkflow/*` 到 `.git/info/exclude`
