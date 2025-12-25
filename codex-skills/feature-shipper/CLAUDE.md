[根目录](../../../CLAUDE.md) > [codex-skills](../) > **feature-shipper**

---

# Feature Shipper Skill 文档

## 变更记录 (Changelog)

### 2025-12-26 01:02:28
- 初次生成模块文档
- 建立工具链清单与使用指南

---

## 模块职责

**Feature Shipper** 是 Codex 环境下的核心交付工具链，提供从项目初始化、健康检查、gate 配置到验证执行的完整闭环能力。

**核心能力**：
- 初始化目标项目的 `.autoworkflow/` 工具链
- 运行 `doctor` 诊断项目可运行性
- 配置与执行 `gate`（测试全绿定义）
- 智能推荐模型选择策略

**设计原则**：
- 跨平台一致性（Windows / WSL / Ubuntu）
- 无外部依赖（纯 Python 标准库）
- 可 repo-local 部署（复制到目标项目）

---

## 入口与启动

### 核心脚本

- **主脚本**：`scripts/autoworkflow.py`
  - 提供完整的 CLI 接口
  - 支持 `init` / `doctor` / `set-gate` / `gate` / `recommend-model` 等子命令

### 使用方式

#### 方式 1：从 Codex Skills 运行（全局安装后）

```bash
# Bash
python "$CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py" --root <repo-root> init

# PowerShell
python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') --root <repo-root> init
```

#### 方式 2：repo-local 运行（推荐）

初始化后，目标项目会生成：
- `.autoworkflow/tools/autoworkflow.py`（主脚本副本）
- `.autoworkflow/tools/aw.ps1`（Windows 包装脚本）
- `.autoworkflow/tools/aw.sh`（Linux/WSL 包装脚本）

之后可直接在目标项目根目录运行：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\aw.ps1 doctor --write --update-state

# WSL/Ubuntu
bash .autoworkflow/tools/aw.sh doctor --write --update-state
```

---

## 对外接口（CLI 命令）

### init - 初始化工具链

**功能**：在目标项目根目录创建 `.autoworkflow/` 结构

**生成文件**：
- `.autoworkflow/tools/autoworkflow.py`（主脚本副本）
- `.autoworkflow/tools/aw.ps1` / `aw.sh`（包装脚本）
- `.autoworkflow/tools/gate.ps1` / `gate.sh`（gate 执行脚本）
- `.autoworkflow/spec.md`（需求规格模板）
- `.autoworkflow/state.md`（执行状态模板）
- `.autoworkflow/model-policy.json`（模型推荐策略）

**示例**：

```bash
# 方式 1：在目标项目根目录执行
python <path-to-this-skill>/scripts/autoworkflow.py init

# 方式 2：显式指定 --root
python <path-to-this-skill>/scripts/autoworkflow.py --root /path/to/target-repo init

# 强制覆盖已有文件
python <path-to-this-skill>/scripts/autoworkflow.py --root /path/to/target-repo init --force
```

---

### doctor - 项目健康检查

**功能**：扫描项目结构，推断可能的构建/测试命令，生成诊断报告

**检查项**：
- 项目类型识别（Node.js / Python / Go / Rust / Java / .NET 等）
- 依赖文件检测（package.json / requirements.txt / go.mod 等）
- 构建/测试/格式化命令推断
- 常见问题检测（缺少依赖/配置错误等）

**输出**：
- 控制台输出诊断报告
- 可选：写入 `.autoworkflow/doctor.md`（`--write`）
- 可选：更新 `.autoworkflow/state.md`（`--update-state`）

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\aw.ps1 doctor --write --update-state

# WSL/Ubuntu
bash .autoworkflow/tools/aw.sh doctor --write --update-state
```

---

### set-gate - 配置 Gate 命令

**功能**：创建或更新 `.autoworkflow/gate.env`，定义"测试全绿"的具体命令

**参数**：
- `--build <cmd>`：构建命令（可选）
- `--test <cmd>`：测试命令（必需）
- `--lint <cmd>`：Lint 命令（可选）
- `--format-check <cmd>`：格式检查命令（可选）
- `--create`：如果文件不存在则创建

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\aw.ps1 set-gate --create --build "npm run build" --test "npm test"

# WSL/Ubuntu
bash .autoworkflow/tools/aw.sh set-gate --create --build "npm run build" --test "npm test"
```

**注意**：如果命令包含复杂引号/分号，建议直接编辑 `.autoworkflow/gate.env`：

```bash
# .autoworkflow/gate.env
BUILD_CMD=npm run build
TEST_CMD=npm test
LINT_CMD=npm run lint
FORMAT_CHECK_CMD=npm run format:check
```

---

### gate - 执行 Gate 验证

**功能**：按 `.autoworkflow/gate.env` 中定义的命令顺序执行（build → test → lint → format-check），任一步骤失败则停止

**输出**：
- 控制台输出各步骤执行结果
- 自动追加最新结果到 `.autoworkflow/state.md`
- 失败时包含关键失败行与尾部日志（highlights + tail）

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\aw.ps1 gate

# WSL/Ubuntu
bash .autoworkflow/tools/aw.sh gate
```

**内部逻辑**：
1. 读取 `.autoworkflow/gate.env`
2. 依次执行：
   - Build（如果配置）
   - Test（必需，缺失则报错）
   - Lint（如果配置）
   - FormatCheck（如果配置）
3. 所有步骤通过 → 输出 "Gate done (green)"
4. 任一步骤失败 → 停止并报错

---

### recommend-model - 智能模型推荐

**功能**：根据任务类型推荐合适的模型（中等模型 vs 强模型）

**参数**：
- `--intent <doctor|debug|implement|refactor>`：任务意图

**推荐策略**（基于 `.autoworkflow/model-policy.json`）：
- `doctor`：中等模型（快速诊断）
- `implement`：中等模型（常规实现）
- `debug`：gate 失败次数超过阈值时升级到强模型
- `refactor`：强模型（复杂重构）

**示例**：

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .autoworkflow\tools\aw.ps1 recommend-model --intent doctor

# WSL/Ubuntu
bash .autoworkflow/tools/aw.sh recommend-model --intent debug
```

**输出示例**：

```
Recommended model for intent 'doctor': sonnet (claude-sonnet-4)
Reason: Lightweight task, medium model sufficient
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

#### `.autoworkflow/gate.env`（由 set-gate 创建）

```bash
BUILD_CMD=npm run build
TEST_CMD=npm test
LINT_CMD=npm run lint
FORMAT_CHECK_CMD=npm run format:check
```

#### `.autoworkflow/model-policy.json`（由 init 创建）

```json
{
  "default": "sonnet",
  "intents": {
    "doctor": "sonnet",
    "implement": "sonnet",
    "debug": "opus",
    "refactor": "opus"
  },
  "escalation": {
    "gate_failure_threshold": 2,
    "escalate_to": "opus"
  }
}
```

---

## 数据模型

### doctor 诊断结果结构

```python
@dataclass(frozen=True)
class DoctorResult:
    project_type: str           # "node" / "python" / "go" / "rust" / "java" / "dotnet"
    build_cmd: str | None       # 推断的构建命令
    test_cmd: str | None        # 推断的测试命令
    lint_cmd: str | None        # 推断的 Lint 命令
    format_check_cmd: str | None # 推断的格式检查命令
    issues: list[str]           # 检测到的问题
    recommendations: list[str]  # 改进建议
```

### gate 执行结果结构

```python
@dataclass(frozen=True)
class GateResult:
    status: str                 # "PASS" / "FAIL"
    timestamp: str              # ISO-8601 格式
    steps: list[StepResult]     # 各步骤结果
    summary: str                # 简要摘要
```

```python
@dataclass(frozen=True)
class StepResult:
    name: str                   # "Build" / "Test" / "Lint" / "FormatCheck"
    cmd: str                    # 执行的命令
    exit_code: int              # 退出码
    output_tail: str            # 输出尾部（失败时）
    highlights: list[str]       # 关键错误行（失败时）
```

---

## 测试与质量

### 测试策略

1. **跨平台验证**
   - 在 Windows / WSL / Ubuntu 分别运行 `init` / `doctor` / `gate`
   - 验证生成的脚本（`.ps1` / `.sh`）可正常执行

2. **真实项目验证**
   - 在多种项目类型中运行（Node.js / Python / Go / Rust）
   - 验证 `doctor` 推断的命令准确性
   - 验证 `gate` 执行的正确性

3. **边界情况测试**
   - 空项目（无依赖文件）
   - 跨语言项目（monorepo）
   - 复杂 gate 命令（包含引号/分号）

### 质量保证

- **代码规范**：遵循 PEP 8，使用类型注解
- **错误处理**：所有 subprocess 调用必须捕获异常
- **日志可读性**：输出必须结构化且易于理解

---

## 常见问题 (FAQ)

### Q1: init 时提示文件已存在怎么办？
**A**: 使用 `--force` 参数强制覆盖：
```bash
python autoworkflow.py init --force
```

### Q2: doctor 推断的命令不准确怎么办？
**A**: 手动编辑 `.autoworkflow/gate.env`，或使用 `set-gate` 覆盖：
```bash
bash .autoworkflow/tools/aw.sh set-gate --create --test "make test"
```

### Q3: gate 失败时如何查看完整日志？
**A**: 失败时会自动追加到 `.autoworkflow/state.md`，包含 highlights + tail。也可手动查看控制台输出。

### Q4: 可以在 CI/CD 中使用 gate 吗？
**A**: 可以，直接调用 gate 脚本即可：
```yaml
# GitHub Actions 示例
- name: Run gate
  run: bash .autoworkflow/tools/gate.sh
```

### Q5: 如何禁用某个 gate 步骤（如 lint）？
**A**: 在 `.autoworkflow/gate.env` 中删除或注释掉对应行：
```bash
# LINT_CMD=npm run lint  # 注释掉以禁用
```

---

## 相关文件清单

```
codex-skills/feature-shipper/
├── SKILL.md                            # Codex 标准 Skill 描述
├── CLAUDE.md                           # 本文档
├── scripts/
│   ├── autoworkflow.py                 # 核心脚本（3000+ 行）
│   └── project_survey.py               # 项目扫描辅助脚本
├── assets/
│   └── autoworkflow/
│       ├── spec-template.md            # 需求规格模板
│       ├── state-template.md           # 执行状态模板
│       └── tools/
│           ├── gate.ps1                # Windows gate 脚本模板
│           ├── gate.sh                 # Linux gate 脚本模板
│           ├── aw.ps1                  # Windows 包装脚本模板
│           └── aw.sh                   # Linux 包装脚本模板
```

---

## 扩展资源

- **根文档**：[../../../CLAUDE.md](../../../CLAUDE.md)
- **Codex Skills 目录**：[../../](../../)
- **相关 Skill**：[../../feedback-logger/](../../feedback-logger/)
- **使用教程**：[../../../README.md](../../../README.md)
