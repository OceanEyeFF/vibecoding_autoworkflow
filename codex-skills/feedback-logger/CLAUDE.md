[根目录](../../../CLAUDE.md) > [codex-skills](../) > **feedback-logger**

---

# Feedback Logger Skill 文档

## 变更记录 (Changelog)

### 2025-12-26 01:02:28
- 初次生成模块文档
- 建立日志记录工具链清单

---

## 模块职责

**Feedback Logger** 是一个轻量级后台日志记录工具，用于在改进测试、调试、迭代过程中捕获关键中间信息，避免信息丢失与返工。

**核心能力**：
- 后台 watch `.autoworkflow/*` 文件变化（state.md / doctor.md / gate.env）
- 包裹命令执行并记录失败高亮与尾部日志
- 手工记录关键假设/结论/TODO
- 所有日志写入 `.autoworkflow/logs/feedback.jsonl`（不提交到 Git）

**设计原则**：
- 可选安装（不影响主工作流）
- 轻量无侵入（后台进程，低资源占用）
- 结构化日志（JSONL 格式，易于解析）

---

## 入口与启动

### 核心脚本

- **主脚本**：`scripts/feedback.py`
  - 提供完整的 CLI 接口
  - 支持 `init` / `start` / `stop` / `log` / `wrap` 等子命令

### 使用方式

#### 初始化（repo-local 部署）

```bash
# Bash（从 Codex Skills 目录）
python "$CODEX_HOME/skills/feedback-logger/scripts/feedback.py" init --root /path/to/target-repo

# PowerShell
python (Join-Path $env:CODEX_HOME 'skills/feedback-logger/scripts/feedback.py') init --root /path/to/target-repo
```

初始化后，目标项目会生成：
- `.autoworkflow/tools/feedback.py`（主脚本副本）
- `.autoworkflow/tools/fb.ps1`（Windows 包装脚本）
- `.autoworkflow/tools/fb.sh`（Linux/WSL 包装脚本）
- `.autoworkflow/logs/feedback.jsonl`（日志文件）

#### 启动后台 watch

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\fb.ps1 start

# WSL/Ubuntu
bash .autoworkflow/tools/fb.sh start
```

#### 停止后台 watch

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\fb.ps1 stop

# WSL/Ubuntu
bash .autoworkflow/tools/fb.sh stop
```

---

## 对外接口（CLI 命令）

### init - 初始化日志工具链

**功能**：在目标项目根目录创建 `.autoworkflow/logs/` 结构与包装脚本

**生成文件**：
- `.autoworkflow/tools/feedback.py`（主脚本副本）
- `.autoworkflow/tools/fb.ps1` / `fb.sh`（包装脚本）
- `.autoworkflow/logs/feedback.jsonl`（日志文件）

**示例**：

```bash
python "$CODEX_HOME/skills/feedback-logger/scripts/feedback.py" init --root /path/to/target-repo
```

---

### start - 启动后台 watch

**功能**：启动后台进程，监控以下文件变化：
- `.autoworkflow/state.md`
- `.autoworkflow/doctor.md`
- `.autoworkflow/gate.env`

**行为**：
- 文件变化时，自动记录到 `.autoworkflow/logs/feedback.jsonl`
- 记录内容包括：时间戳、事件类型（`file_change`）、文件路径、变更摘要

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\fb.ps1 start

# WSL/Ubuntu
bash .autoworkflow/tools/fb.sh start
```

**输出**：

```
Background watch started (PID: 12345)
Log: .autoworkflow/logs/feedback.jsonl
```

---

### stop - 停止后台 watch

**功能**：停止由 `start` 启动的后台进程

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\fb.ps1 stop

# WSL/Ubuntu
bash .autoworkflow/tools/fb.sh stop
```

**输出**：

```
Stopped watch process (PID: 12345)
```

---

### log - 手工记录日志

**功能**：手工记录关键假设、结论、TODO 等信息

**参数**：
- `--message <text>`：日志内容（必需）
- `--tag <tag>`：标签（可选，如 `hypothesis` / `conclusion` / `todo`）

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\fb.ps1 log --message "假设：flaky 测试由于竞态条件" --tag hypothesis

# WSL/Ubuntu
bash .autoworkflow/tools/fb.sh log --message "TODO: 补充边界条件测试" --tag todo
```

**日志格式**（写入 `feedback.jsonl`）：

```json
{
  "ts": "2025-12-26T01:02:28Z",
  "kind": "manual_log",
  "message": "假设：flaky 测试由于竞态条件",
  "tags": ["hypothesis"],
  "data": {}
}
```

---

### wrap - 包裹命令并记录失败信息

**功能**：执行指定命令，如果失败则自动记录关键失败行与尾部日志

**参数**：
- `--tag <tag>`：标签（可选，如 `gate` / `build` / `test`）
- `<command> [args...]`：要执行的命令

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\fb.ps1 wrap --tag gate aw gate

# WSL/Ubuntu
bash .autoworkflow/tools/fb.sh wrap --tag test npm test
```

**行为**：
- 执行命令并捕获输出
- 命令成功：仅记录简要信息
- 命令失败：记录失败高亮（包含 `error` / `fail` / `exception` 的行）+ 尾部日志（最后 20 行）

**日志格式**（失败时）：

```json
{
  "ts": "2025-12-26T01:02:28Z",
  "kind": "wrapped_command",
  "message": "Command failed: npm test",
  "tags": ["test", "failure"],
  "data": {
    "exit_code": 1,
    "highlights": [
      "Error: Expected 'foo' but got 'bar'",
      "FAIL src/utils/helper.test.ts"
    ],
    "tail": [
      "...",
      "Test Suites: 1 failed, 5 passed",
      "Tests: 1 failed, 42 passed"
    ]
  }
}
```

---

## 关键依赖与配置

### 依赖项

- **Python 版本**：3.7+ (推荐 3.9+)
- **外部依赖**：无（仅使用标准库）
- **平台要求**：
  - Windows: PowerShell 5.1+ 或 PowerShell Core 7+
  - Linux/WSL: Bash 4.0+

### 配置文件

无额外配置文件，行为由命令参数控制。

### 监控的文件清单（默认）

```python
DEFAULT_WATCH_FILES = (
    ".autoworkflow/state.md",
    ".autoworkflow/doctor.md",
    ".autoworkflow/gate.env",
)
```

---

## 数据模型

### 日志事件结构

```python
@dataclass(frozen=True)
class Event:
    ts: str                     # ISO-8601 时间戳
    kind: str                   # 事件类型（file_change / manual_log / wrapped_command）
    message: str                # 简要描述
    tags: list[str]             # 标签列表
    data: dict                  # 附加数据（结构因 kind 而异）
```

### 事件类型详解

#### 1. `file_change`（文件变化）

```json
{
  "ts": "2025-12-26T01:02:28Z",
  "kind": "file_change",
  "message": "File changed: .autoworkflow/state.md",
  "tags": ["file_watch"],
  "data": {
    "file_path": ".autoworkflow/state.md",
    "change_summary": "Updated gate result (PASS)"
  }
}
```

#### 2. `manual_log`（手工日志）

```json
{
  "ts": "2025-12-26T01:02:28Z",
  "kind": "manual_log",
  "message": "假设：flaky 测试由于竞态条件",
  "tags": ["hypothesis"],
  "data": {}
}
```

#### 3. `wrapped_command`（包裹命令）

```json
{
  "ts": "2025-12-26T01:02:28Z",
  "kind": "wrapped_command",
  "message": "Command failed: npm test",
  "tags": ["test", "failure"],
  "data": {
    "exit_code": 1,
    "highlights": ["Error: Expected 'foo' but got 'bar'"],
    "tail": ["Test Suites: 1 failed, 5 passed"]
  }
}
```

---

## 测试与质量

### 测试策略

1. **后台进程稳定性**
   - 验证 `start` / `stop` 可正常启动/停止进程
   - 验证进程不会泄漏（多次 start/stop 不会留下僵尸进程）

2. **文件监控准确性**
   - 修改监控文件（state.md / doctor.md），验证日志是否记录
   - 验证不监控的文件（如 `spec.md`）不会触发日志

3. **命令包裹正确性**
   - 执行成功命令，验证日志简洁
   - 执行失败命令，验证日志包含 highlights + tail

### 质量保证

- **日志格式一致性**：所有日志必须为合法 JSONL（每行一个 JSON 对象）
- **错误处理**：后台进程异常不应影响主工作流
- **资源占用**：后台进程应保持低 CPU/内存占用

---

## 常见问题 (FAQ)

### Q1: 后台 watch 进程会一直运行吗？
**A**: 是的，直到调用 `stop` 或系统重启。建议在调试完成后手动停止。

### Q2: 日志文件会无限增长吗？
**A**: 是的，当前版本不会自动清理。可手动删除或归档 `.autoworkflow/logs/feedback.jsonl`。

### Q3: 可以自定义监控的文件吗？
**A**: 当前版本不支持。如需定制，可直接修改 `feedback.py` 中的 `DEFAULT_WATCH_FILES`。

### Q4: 日志记录会影响性能吗？
**A**: 轻微影响（后台进程定期检查文件修改时间），但通常可忽略不计。

### Q5: 可以在 CI/CD 中使用吗？
**A**: 不推荐。Feedback Logger 设计用于本地开发/调试，CI/CD 应使用原生日志机制。

---

## 相关文件清单

```
codex-skills/feedback-logger/
├── SKILL.md                            # Codex 标准 Skill 描述
├── CLAUDE.md                           # 本文档
└── scripts/
    └── feedback.py                     # 核心脚本（~1000 行）
```

---

## 扩展资源

- **根文档**：[../../../CLAUDE.md](../../../CLAUDE.md)
- **Codex Skills 目录**：[../../](../../)
- **相关 Skill**：[../../feature-shipper/](../../feature-shipper/)
- **使用教程**：[../../../README.md](../../../README.md)
