# AW-Kernel 项目路线图

> 创建时间：2026-01-06
> 最后更新：2026-01-06
> 核心理念：构建可观测、可迭代、可扩展的 Agent 生态系统

---

## 目录

1. [当前状态](#一当前状态)
2. [核心 Agent 迭代计划](#二核心-agent-迭代计划)
3. [执行记录与日志系统](#三执行记录与日志系统)
4. [Hooks 钩子系统](#四hooks-钩子系统)
5. [高级功能规划](#五高级功能规划)
6. [实施时间线](#六实施时间线)
7. [AutoDev Skill 开发路线](#七autodev-skill-开发路线)

---

## 一、当前状态

### 1.1 已完成

| 组件 | 状态 | 说明 |
|------|------|------|
| 核心 Agents (6个) | ✅ 完成 | code-analyzer, code-debug-expert, code-project-cleaner, feature-shipper, requirement-refiner, system-log-analyzer |
| Skills (2个) | ✅ 完成 | autodev, autodev-worktree |
| 安装脚本 | ✅ 完成 | PowerShell (Windows) + Bash (Linux/macOS/WSL) |
| 命名空间隔离 | ✅ 完成 | `aw-kernel` 命名空间 |
| 文档体系 | ✅ 完成 | CLAUDE.md, TOOLCHAIN.md, STANDARDS.md |

### 1.2 待开发（按新优先级排序）

**优先级原则**：
1. 重要 > 不重要
2. 可以马上做 > 需要功能依赖
3. 不用造轮子 > 需要造轮子
4. 提升稳定性和体验 > 开发新功能

| 优先级 | 组件 | 类型 | 说明 |
|--------|------|------|------|
| 🥇 P0 | **现有 Agents 测试与修复** | 稳定性 | 测试 6 个 Agents，修复已知问题，收集用户反馈 |
| 🥈 P1 | **执行日志系统（简化版）** | 基础设施 | 基于 Hooks 的日志记录（不造轮子） |
| 🥉 P2 | **AutoDev Skill v0.1** | 新功能 | 四阶段流程 + Level 0，仅用 TodoWrite（不造轮子） |
| 🔹 P3 | Hooks 钩子系统 | 基础设施 | 需要编写 Python 脚本（造轮子） |
| 🔹 P3 | Agent 版本管理 + CHANGELOG | 工程化 | 文档化管理，无需脚本 |
| 🔸 P4 | AutoDev v0.2（Git 检查点） | 功能增强 | 需要 Git 管理脚本（造轮子） + 依赖 v0.1 验证 |
| 🔸 P4 | 健康检查脚本 | 工程化 | 需要编写诊断脚本（造轮子） |
| ⚪ P5 | AutoDev v0.3/v1.0 | 功能增强 | 依赖 v0.2 验证 + 大量脚本开发 |
| ⚪ P5 | Agent 编排系统 | 高级特性 | 不紧急，未来规划 |
| ⚪ P5 | 自动更新机制 | 高级特性 | 不紧急，未来规划 |

---

## 二、核心 Agent 迭代计划

### 2.1 版本管理策略

采用语义化版本控制 (SemVer)：`MAJOR.MINOR.PATCH`

```
v1.0.0 → v1.1.0 → v1.1.1 → v2.0.0
  │         │         │         │
  │         │         │         └── 重大变更（不兼容）
  │         │         └── 补丁修复（Bug fix）
  │         └── 新功能（向后兼容）
  └── 初始版本
```

**每个 Agent 文件头部添加版本信息**：

```markdown
---
name: code-analyzer
version: 1.0.0
last_updated: 2026-01-06
changelog: |
  - v1.0.0 (2026-01-06): 初始版本
---
```

### 2.2 迭代周期

| 迭代类型 | 周期 | 触发条件 |
|---------|------|---------|
| 补丁更新 | 按需 | Bug 修复、文档纠正 |
| 功能迭代 | 2周 | 新功能、性能优化 |
| 重大版本 | 1月+ | 架构变更、不兼容更新 |

### 2.3 各 Agent 迭代方向

#### code-analyzer v1.x → v2.0

| 版本 | 计划功能 |
|------|---------|
| v1.1 | 支持更多语言（Rust, Go, Swift） |
| v1.2 | 增加代码复杂度分析 |
| v1.3 | 集成安全漏洞检测 |
| v2.0 | 支持 AST 级别深度分析 |

#### code-debug-expert v1.x → v2.0

| 版本 | 计划功能 |
|------|---------|
| v1.1 | 增加堆栈追踪智能解析 |
| v1.2 | 支持远程调试日志分析 |
| v1.3 | 集成常见框架错误模式库 |
| v2.0 | 支持运行时状态推断 |

#### feature-shipper v1.x → v2.0

| 版本 | 计划功能 |
|------|---------|
| v1.1 | 增强 Git 操作的原子性 |
| v1.2 | 支持多分支并行开发 |
| v1.3 | 集成 CI/CD 状态检查 |
| v2.0 | 完整的发布流水线支持 |

### 2.4 变更日志管理

在 `Claude/agents/aw-kernel/` 下创建 `CHANGELOG.md`：

```markdown
# Changelog

## [Unreleased]
### Added
- ...

## [1.1.0] - 2026-01-20
### Added
- code-analyzer: 支持 Rust 语言分析
### Fixed
- feature-shipper: 修复 Git stash 操作在某些情况下失败的问题

## [1.0.0] - 2026-01-06
### Added
- 初始版本发布
- 6 个核心 Agents
- 2 个 Skills
```

---

## 三、执行记录与日志系统

### 3.1 设计目标

1. **可观测性**：了解 Agent 何时被调用、执行了什么、结果如何
2. **可追溯性**：问题发生时能回溯完整上下文
3. **可分析性**：收集性能指标、识别改进点
4. **隐私保护**：敏感信息脱敏处理

### 3.2 日志架构

```
~/.claude/
├── logs/
│   ├── aw-kernel/
│   │   ├── sessions/                    # 会话级日志
│   │   │   ├── 2026-01-06_143022_abc123.json
│   │   │   └── 2026-01-06_152015_def456.json
│   │   ├── agents/                      # Agent 级日志
│   │   │   ├── code-analyzer.log
│   │   │   ├── feature-shipper.log
│   │   │   └── ...
│   │   ├── metrics/                     # 性能指标
│   │   │   ├── daily/
│   │   │   │   └── 2026-01-06.json
│   │   │   └── summary.json
│   │   └── errors/                      # 错误日志
│   │       └── 2026-01-06.log
│   └── retention.json                   # 日志保留策略
```

### 3.3 日志格式

#### 3.3.1 会话日志 (Session Log)

```json
{
  "session_id": "2026-01-06_143022_abc123",
  "started_at": "2026-01-06T14:30:22Z",
  "ended_at": "2026-01-06T14:45:10Z",
  "duration_seconds": 888,
  "project": "/path/to/project",
  "agents_invoked": [
    {
      "agent": "code-analyzer",
      "version": "1.0.0",
      "invoked_at": "2026-01-06T14:30:25Z",
      "completed_at": "2026-01-06T14:31:02Z",
      "duration_ms": 37000,
      "status": "success",
      "input_summary": "分析 src/ 目录的代码质量",
      "output_summary": "发现 3 个改进点",
      "tool_calls": [
        {"tool": "Glob", "count": 2},
        {"tool": "Read", "count": 8},
        {"tool": "Grep", "count": 3}
      ]
    }
  ],
  "total_agents_invoked": 3,
  "total_tool_calls": 47,
  "errors": []
}
```

#### 3.3.2 Agent 日志 (Agent Log)

```
2026-01-06T14:30:25Z [INFO] [code-analyzer] Session abc123 - Started
2026-01-06T14:30:26Z [DEBUG] [code-analyzer] Scanning pattern: src/**/*.ts
2026-01-06T14:30:30Z [INFO] [code-analyzer] Found 42 files to analyze
2026-01-06T14:31:00Z [INFO] [code-analyzer] Analysis complete - 3 issues found
2026-01-06T14:31:02Z [INFO] [code-analyzer] Session abc123 - Completed (37s)
```

#### 3.3.3 性能指标 (Metrics)

```json
{
  "date": "2026-01-06",
  "agents": {
    "code-analyzer": {
      "invocations": 15,
      "avg_duration_ms": 28500,
      "success_rate": 0.93,
      "p50_duration_ms": 25000,
      "p95_duration_ms": 45000,
      "errors": 1
    },
    "feature-shipper": {
      "invocations": 8,
      "avg_duration_ms": 120000,
      "success_rate": 1.0,
      "p50_duration_ms": 110000,
      "p95_duration_ms": 180000,
      "errors": 0
    }
  },
  "totals": {
    "sessions": 12,
    "agent_invocations": 45,
    "tool_calls": 523,
    "avg_session_duration_s": 720
  }
}
```

### 3.4 日志实现方案

#### 方案 A：Hooks 方式（推荐）

通过 Claude Code Hooks 自动记录：

```json
// ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "command": "python ~/.claude/hooks/aw-kernel/log-tool-call.py",
        "description": "记录工具调用"
      }
    ],
    "Stop": [
      {
        "command": "python ~/.claude/hooks/aw-kernel/finalize-session.py",
        "description": "完成会话日志"
      }
    ]
  }
}
```

#### 方案 B：Agent 内置日志

在每个 Agent 的指令中加入日志要求：

```markdown
## 执行日志

每次执行时，你必须：
1. 开始时记录 `[开始] Agent: {name}, 任务: {summary}`
2. 结束时记录 `[完成] 耗时: {duration}, 结果: {status}`
3. 将日志追加到 `.autodev/agent-log.txt`
```

### 3.5 日志保留策略

```json
{
  "retention": {
    "sessions": {
      "max_age_days": 30,
      "max_count": 1000
    },
    "metrics": {
      "daily": {
        "max_age_days": 90
      },
      "monthly_summary": {
        "max_age_days": 365
      }
    },
    "errors": {
      "max_age_days": 90
    }
  },
  "cleanup_schedule": "daily"
}
```

---

## 四、Hooks 钩子系统

### 4.1 钩子类型设计

基于 Claude Code 的 Hooks 机制，设计以下钩子点：

| 钩子类型 | 触发时机 | 用途 |
|---------|---------|------|
| `PreAgentInvoke` | Agent 被调用前 | 上下文注入、权限检查 |
| `PostAgentInvoke` | Agent 完成后 | 结果验证、日志记录 |
| `PreToolUse` | 工具调用前 | 参数验证、安全检查 |
| `PostToolUse` | 工具调用后 | 结果记录、缓存 |
| `OnError` | 发生错误时 | 错误报告、自动恢复 |
| `OnSessionStart` | 会话开始 | 初始化状态、加载配置 |
| `OnSessionEnd` | 会话结束 | 清理资源、保存状态 |

### 4.2 钩子目录结构

```
~/.claude/hooks/aw-kernel/
├── config.json                      # 钩子配置
├── pre-agent/
│   ├── inject-context.py            # 注入项目上下文
│   ├── check-permissions.py         # 权限检查
│   └── load-project-rules.py        # 加载项目规则
├── post-agent/
│   ├── validate-output.py           # 输出验证
│   ├── log-execution.py             # 执行日志
│   └── update-metrics.py            # 更新指标
├── pre-tool/
│   ├── validate-paths.py            # 路径安全检查
│   └── rate-limit.py                # 频率限制
├── post-tool/
│   ├── cache-results.py             # 结果缓存
│   └── track-changes.py             # 变更追踪
└── on-error/
    ├── report-error.py              # 错误报告
    └── suggest-recovery.py          # 恢复建议
```

### 4.3 钩子配置示例

```json
{
  "version": "1.0.0",
  "enabled": true,
  "hooks": {
    "pre_agent": {
      "enabled": true,
      "scripts": [
        {
          "name": "inject-context",
          "script": "pre-agent/inject-context.py",
          "timeout_ms": 5000,
          "required": true,
          "agents": ["*"]
        },
        {
          "name": "check-permissions",
          "script": "pre-agent/check-permissions.py",
          "timeout_ms": 2000,
          "required": true,
          "agents": ["feature-shipper", "code-project-cleaner"]
        }
      ]
    },
    "post_agent": {
      "enabled": true,
      "scripts": [
        {
          "name": "validate-output",
          "script": "post-agent/validate-output.py",
          "timeout_ms": 10000,
          "required": false,
          "mode": "warn"
        },
        {
          "name": "log-execution",
          "script": "post-agent/log-execution.py",
          "timeout_ms": 3000,
          "required": true
        }
      ]
    },
    "on_error": {
      "enabled": true,
      "scripts": [
        {
          "name": "report-error",
          "script": "on-error/report-error.py",
          "timeout_ms": 5000
        }
      ]
    }
  },
  "global_settings": {
    "log_all_hooks": true,
    "fail_open": false,
    "max_hook_duration_ms": 30000
  }
}
```

### 4.4 核心钩子实现

#### 4.4.1 上下文注入钩子

```python
#!/usr/bin/env python3
"""
pre-agent/inject-context.py
在 Agent 执行前注入项目上下文
"""

import json
import sys
import os
from pathlib import Path

def get_project_context(project_path: str) -> dict:
    """收集项目上下文信息"""
    context = {
        "project_name": Path(project_path).name,
        "has_git": os.path.exists(os.path.join(project_path, ".git")),
        "has_package_json": os.path.exists(os.path.join(project_path, "package.json")),
        "has_pyproject": os.path.exists(os.path.join(project_path, "pyproject.toml")),
        "project_rules": None
    }

    # 加载项目规则（如果存在）
    rules_file = os.path.join(project_path, ".claude", "rules.json")
    if os.path.exists(rules_file):
        with open(rules_file) as f:
            context["project_rules"] = json.load(f)

    return context

def main():
    hook_input = json.loads(sys.stdin.read())

    agent_name = hook_input.get("agent", "unknown")
    project_path = hook_input.get("project_path", os.getcwd())

    context = get_project_context(project_path)

    # 返回注入的上下文
    print(json.dumps({
        "status": "continue",
        "injected_context": context,
        "message": f"Context injected for {agent_name}"
    }))

if __name__ == "__main__":
    main()
```

#### 4.4.2 输出验证钩子

```python
#!/usr/bin/env python3
"""
post-agent/validate-output.py
验证 Agent 输出是否符合规范
"""

import json
import sys
import re

def validate_output(agent_name: str, output: str) -> dict:
    """验证输出"""
    issues = []
    warnings = []

    # 规则 1：检查是否包含绝对路径泄露
    if re.search(r'/home/\w+|C:\\Users\\\w+', output):
        warnings.append("输出中可能包含用户目录路径")

    # 规则 2：检查是否有未完成的占位符
    if re.search(r'\{TODO\}|\[TBD\]|FIXME', output, re.IGNORECASE):
        warnings.append("输出中包含未完成的占位符")

    # 规则 3：feature-shipper 特定检查
    if agent_name == "feature-shipper":
        if "git push" in output.lower() and "force" in output.lower():
            issues.append("feature-shipper 尝试 force push，已阻止")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }

def main():
    hook_input = json.loads(sys.stdin.read())

    agent_name = hook_input.get("agent", "unknown")
    agent_output = hook_input.get("output", "")

    result = validate_output(agent_name, agent_output)

    if result["valid"]:
        status = "continue"
        if result["warnings"]:
            message = f"验证通过，但有警告: {', '.join(result['warnings'])}"
        else:
            message = "验证通过"
    else:
        status = "block"
        message = f"验证失败: {', '.join(result['issues'])}"

    print(json.dumps({
        "status": status,
        "validation": result,
        "message": message
    }))

if __name__ == "__main__":
    main()
```

### 4.5 钩子使用场景

| 场景 | 钩子组合 | 说明 |
|------|---------|------|
| 安全审计 | PreTool + PostAgent | 记录所有操作，验证输出安全性 |
| 性能优化 | PreAgent + PostAgent | 测量执行时间，识别瓶颈 |
| 上下文增强 | PreAgent | 注入项目配置、历史记录 |
| 错误恢复 | OnError | 自动建议恢复方案 |
| 缓存加速 | PostTool | 缓存 Glob/Grep 结果 |

---

## 五、高级功能规划

### 5.1 Agent 编排系统

支持多 Agent 协作的工作流定义：

```yaml
# workflows/code-review.yaml
name: code-review-workflow
version: 1.0.0
description: 自动化代码审查流程

stages:
  - name: analyze
    agent: code-analyzer
    inputs:
      path: "${input.target_path}"
    outputs:
      - issues

  - name: suggest-fixes
    agent: code-debug-expert
    depends_on: [analyze]
    condition: "${stages.analyze.outputs.issues.length > 0}"
    inputs:
      issues: "${stages.analyze.outputs.issues}"
    outputs:
      - fixes

  - name: apply-fixes
    agent: feature-shipper
    depends_on: [suggest-fixes]
    requires_approval: true
    inputs:
      changes: "${stages.suggest-fixes.outputs.fixes}"

on_failure:
  notify: true
  rollback: true
```

### 5.2 Agent 依赖管理

```json
{
  "dependencies": {
    "code-analyzer": {
      "requires": [],
      "optional": ["code-debug-expert"],
      "conflicts": []
    },
    "feature-shipper": {
      "requires": ["code-analyzer"],
      "optional": ["code-debug-expert"],
      "conflicts": []
    }
  }
}
```

### 5.3 自动更新机制

```bash
# ~/.claude/scripts/aw-kernel/check-updates.sh
#!/bin/bash

REPO_URL="https://gitee.com/oceaneye/trae-agents-prompt.git"
LOCAL_VERSION=$(cat ~/.claude/agents/aw-kernel/.installed | grep version | cut -d: -f2 | tr -d ' ')
REMOTE_VERSION=$(curl -s "https://gitee.com/api/v5/repos/oceaneye/trae-agents-prompt/releases/latest" | jq -r '.tag_name')

if [ "$LOCAL_VERSION" != "$REMOTE_VERSION" ]; then
    echo "New version available: $REMOTE_VERSION (current: $LOCAL_VERSION)"
    echo "Run 'aw-kernel update' to upgrade"
fi
```

### 5.4 健康检查

```python
#!/usr/bin/env python3
"""
healthcheck.py - Agent 系统健康检查
"""

import os
import json
from pathlib import Path

def check_health():
    results = {
        "status": "healthy",
        "checks": {}
    }

    claude_home = Path.home() / ".claude"

    # 检查 1: Agent 文件完整性
    agents_dir = claude_home / "agents" / "aw-kernel"
    expected_agents = [
        "code-analyzer.md",
        "code-debug-expert.md",
        "code-project-cleaner.md",
        "feature-shipper.md",
        "requirement-refiner.md",
        "system-log-analyzer.md"
    ]

    missing = [a for a in expected_agents if not (agents_dir / a).exists()]
    results["checks"]["agents_integrity"] = {
        "status": "pass" if not missing else "fail",
        "missing": missing
    }

    # 检查 2: 日志目录可写
    logs_dir = claude_home / "logs" / "aw-kernel"
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        test_file = logs_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        results["checks"]["logs_writable"] = {"status": "pass"}
    except Exception as e:
        results["checks"]["logs_writable"] = {"status": "fail", "error": str(e)}

    # 检查 3: Hooks 配置有效
    hooks_config = claude_home / "hooks" / "aw-kernel" / "config.json"
    if hooks_config.exists():
        try:
            with open(hooks_config) as f:
                json.load(f)
            results["checks"]["hooks_config"] = {"status": "pass"}
        except json.JSONDecodeError as e:
            results["checks"]["hooks_config"] = {"status": "fail", "error": str(e)}
    else:
        results["checks"]["hooks_config"] = {"status": "skip", "reason": "not configured"}

    # 汇总状态
    if any(c["status"] == "fail" for c in results["checks"].values()):
        results["status"] = "unhealthy"

    return results

if __name__ == "__main__":
    print(json.dumps(check_health(), indent=2))
```

### 5.5 A/B 测试框架

支持对 Agent 不同版本进行对比测试：

```json
{
  "experiments": {
    "code-analyzer-v2-test": {
      "enabled": true,
      "control": "code-analyzer@1.0.0",
      "treatment": "code-analyzer@2.0.0-beta",
      "traffic_split": 0.2,
      "metrics": ["duration", "accuracy", "user_satisfaction"],
      "start_date": "2026-02-01",
      "end_date": "2026-02-14"
    }
  }
}
```

---

## 六、实施时间线（重新规划）

### 新规划原则
1. **稳定优先**：先修复现有问题，再开发新功能
2. **渐进式**：每个阶段都交付可用的价值
3. **不造轮子**：优先使用 Claude Code 原生能力
4. **验证优先**：新功能依赖前序验证通过

---

### Phase 1: 稳定与基础（2026 Q1，W1-W4）

**目标**：确保现有系统稳定，建立观测能力

| 周次 | 任务 | 优先级 | 交付物 | 类型 |
|------|------|--------|--------|------|
| **W1** | 🥇 现有 Agents 全面测试 | P0 | 测试报告 + 问题清单 | 稳定性 |
| **W1-W2** | 🥇 修复已知问题（高优先级） | P0 | Bug 修复 + 版本号更新 | 稳定性 |
| **W2** | 🥈 日志系统设计（简化版） | P1 | 日志架构文档 | 基础设施 |
| **W3** | 🥈 基于 Hooks 的日志记录 | P1 | 会话日志 + Agent 日志 | 基础设施 |
| **W3-W4** | 🔹 Agent 版本管理规范 | P3 | CHANGELOG.md + 版本号标注 | 工程化 |
| **W4** | 🥈 日志系统验收测试 | P1 | 验收报告 | 基础设施 |

**里程碑**：
- ✅ 所有 Agents 通过测试，已知 Bug 修复
- ✅ 日志系统可用，能追踪 Agent 调用历史
- ✅ 版本管理规范建立

---

### Phase 2: AutoDev 最简可行版本（2026 Q1-Q2，W5-W8）

**目标**：验证 AutoDev 核心工作流可行性

| 周次 | 任务 | 优先级 | 交付物 | 类型 |
|------|------|--------|--------|------|
| **W5** | 🥉 AutoDev v0.1 设计细化 | P2 | 详细设计文档 | 新功能 |
| **W5-W6** | 🥉 AutoDev v0.1 开发 | P2 | SKILL.md（四阶段 + Level 0） | 新功能 |
| **W6** | 🥉 AutoDev v0.1 内部测试 | P2 | 测试报告 + 问题清单 | 新功能 |
| **W7** | 🥉 AutoDev v0.1 问题修复 | P2 | Bug 修复 | 新功能 |
| **W7-W8** | 🥉 AutoDev v0.1 用户试用 | P2 | 用户反馈收集 | 新功能 |
| **W8** | 决策点：是否继续 v0.2 开发 | - | 决策报告 | 管理 |

**里程碑**：
- ✅ AutoDev v0.1 可用，能完整走通四阶段流程
- ✅ 收集到至少 3 个真实使用场景的反馈
- ✅ 决定是否投入 v0.2（Git 脚本）开发

**决策依据**：
- v0.1 是否解决了核心痛点？
- 用户是否真的需要 Git 回退功能？
- 投入脚本开发的 ROI 是否合理？

---

### Phase 3: 有条件的增强（2026 Q2，W9-W12）

**前置条件**：Phase 2 决策通过

| 周次 | 任务 | 优先级 | 交付物 | 类型 |
|------|------|--------|--------|------|
| **W9** | 🔹 Hooks 钩子系统开发 | P3 | Python 脚本（上下文注入、输出验证） | 基础设施 |
| **W10** | 🔸 AutoDev v0.2 开发（如决策通过） | P4 | Git 检查点 + Level 1 | 功能增强 |
| **W10-W11** | 🔸 健康检查脚本 | P4 | healthcheck.py | 工程化 |
| **W11-W12** | 核心 Agent v1.1 迭代 | - | 新功能 + 性能优化 | Agent 迭代 |

**里程碑**：
- ✅ Hooks 系统可用（如需要）
- ✅ AutoDev v0.2 可用（如需要）
- ✅ 健康检查能诊断系统状态

---

### Phase 4: 高级特性（2026 Q3+，按需规划）

**前置条件**：Phase 3 验证通过，且有明确需求

| 功能 | 优先级 | 触发条件 |
|------|--------|---------|
| AutoDev v0.3（指令模块化） | P5 | v0.2 用户反馈 Prompt 遗忘问题严重 |
| AutoDev v1.0（辅助脚本） | P5 | v0.2/v0.3 Git 操作不可靠 |
| AutoDev Worktree 支持 | P5 | 有明确的并行开发场景需求 |
| Agent 编排系统 | P5 | 有复杂的多 Agent 协作需求 |
| A/B 测试框架 | P5 | 需要对比不同 Agent 版本效果 |
| 自动更新机制 | P5 | 用户基数足够大，手动更新成本高 |

**原则**：
- 不预先投入，等待真实需求驱动
- 每个功能都需要明确的 ROI 分析
- 优先考虑低成本替代方案

---

### 时间线对比（旧 vs 新）

| 阶段 | 旧计划 | 新计划 | 调整理由 |
|------|--------|--------|---------|
| Q1 W1 | AutoDev v0.1 | Agents 测试与修复 | 稳定性优先 |
| Q1 W2 | 日志 + AutoDev v0.2 | 日志系统（简化） | 不造轮子，聚焦基础 |
| Q1 W3 | Hooks + AutoDev v0.3 | 日志验收 + 版本管理 | 先把日志做好 |
| Q1 W4 | AutoDev v1.0 | 日志验收完成 | 不急于开发 AutoDev |
| Q1 W5-W8 | Agent 版本管理 | AutoDev v0.1 开发与验证 | 验证可行性优先 |
| Q2 W9-W12 | 性能指标 + Agent v1.1 | 有条件的增强（Hooks/v0.2） | 按需投入，不预先开发 |
| Q3+ | 高级特性 | 按需规划 | 需求驱动，不预先规划 |

---


## 七、AutoDev Skill 开发路线（精简版）

### 7.1 设计理念

AutoDev 是一个基于 Claude Code 原生能力的**自动化开发工作流 Skill**，核心设计原则：

1. **原生优先**：优先使用 Claude Code 原生工具（Task、TodoWrite、Bash）
2. **无需编排器**：不再需要 Central Orchestrator，用 Skill 直接驱动
3. **人类在环**：每个里程碑结束时确认，不自动跳转
4. **状态可见**：用 TodoWrite 追踪进度，用户随时可见
5. **可恢复**：中断后可以通过描述当前状态继续

### 7.2 四阶段工作流

```
Phase 1: 需求理解与精炼
   ↓ (用户确认)
Phase 2: 任务拆分与里程碑规划
   ↓ (用户确认)
Phase 3: 迭代开发（循环）
   ↓ (所有任务完成)
Phase 4: 验收与提交
```

**关键特性**：
- **4 个 Gate 门禁**（G1-G4）：每个阶段结束时的质量检查
- **多层回路机制**（Level 0-3）：自动问题修复与升级策略

### 7.3 v0.1 最简可行版本（近期重点）

**开发时间**：2026 Q1-Q2（W5-W8）

**核心目标**：验证四阶段工作流可行性，不追求完美

| 组件 | 功能 | 实现方式 |
|------|------|---------|
| 核心流程 | Phase 1-4 基础流程 | 单个 SKILL.md 文件（约 500 行） |
| 门禁系统 | G1-G4 基础检查 | 嵌入 Prompt 中的清单 |
| 回路机制 | **仅 Level 0**（即时修复，最多 3 次） | 嵌入 Prompt 中的重试逻辑 |
| 状态管理 | **仅 TodoWrite**（内存） | Claude Code 原生工具 |

**不包含的功能**（按需后续考虑）：
- ❌ Git 检查点机制（需要脚本）
- ❌ Level 1/2 回路（需要 Git 脚本）
- ❌ 状态持久化到文件（需要 `.autodev/state.json`）
- ❌ 指令模块化（需要外部文件 + Read 触发）
- ❌ 辅助脚本（需要大量开发）

**验收标准**：
- [ ] 能完整走通 Phase 1 → 2 → 3 → 4
- [ ] G1/G2/G3/G4 门禁能正确检查
- [ ] Level 0 循环能工作（失败 3 次后请求人工介入）
- [ ] 中断后能通过 TodoWrite 恢复基本进度
- [ ] 至少 3 个真实场景验证通过

**设计约束**：
1. **单文件实现**：所有指令在 `Claude/skills/aw-kernel/autodev.md` 中
2. **无外部依赖**：不依赖任何脚本或外部状态文件
3. **Prompt 长度控制**：≤ 600 行（避免上下文爆炸）
4. **失败优雅降级**：Level 0 失败后，提供详细的人工介入指导

---

### 7.4 v0.2+ 高级版本（按需规划）

**开发决策点**：W8（2026 Q2）

**决策依据**：
1. v0.1 是否解决了核心痛点？
2. 用户反馈中是否有强烈的 Git 回退需求？
3. 投入脚本开发的成本是否合理（预计 2-3 周）？

**可能的高级功能**（如果决策通过）：

#### v0.2 增强版（如需要）
| 组件 | 新增功能 | 成本 |
|------|---------|------|
| Git 检查点 | Phase 2 检查点、任务起点记录 | 需要 Bash 脚本封装 Git 操作 |
| Level 1 回路 | Git 回退 + 任务重构（2 次尝试） | 需要可靠的 Git 恢复脚本 |
| 本地化状态 | `.autodev/state.json` 持久化 | 需要状态读写脚本 |

**成本评估**：约 2 周开发 + 1 周测试

#### v0.3 完整版（如需要）
| 组件 | 新增功能 | 成本 |
|------|---------|------|
| 指令模块化 | 外部指令文件（phases/gates/loops/） | 需要重构 SKILL.md + 手动 Read 触发 |
| Level 2 回路 | 整体重规划（回退到 Phase 2） | 需要更复杂的 Git 操作 |
| 指令刷新 | 手动 Read 触发指令重载 | 需要刷新机制设计 |

**成本评估**：约 2 周开发 + 1 周测试

#### v1.0 生产版（如需要）
| 组件 | 新增功能 | 成本 |
|------|---------|------|
| 辅助脚本 | `autodev-helper.sh` 封装 Git 操作 | 需要完整的 Bash/Python 脚本开发 |
| Level 3 增强 | 详细诊断报告 + 行动建议 | 需要复杂的状态分析逻辑 |
| 完整文档 | 用户手册 + 开发者指南 | 需要文档编写工作 |

**成本评估**：约 2 周开发 + 1 周文档 + 1 周测试

---

### 7.5 与 Agent 生态集成

| Skill | 调用的 Agents | 说明 |
|-------|--------------|------|
| autodev (v0.1) | requirement-refiner | Phase 1: 需求精炼 |
| autodev (v0.1) | feature-shipper | Phase 3: 单功能交付 |
| autodev (v0.1) | code-debug-expert | Level 0: 调试支持 |

**未来可能的集成**（如高级版本开发）：
- autodev-worktree：在 Git Worktree 中并行开发
- 更多专业 Agents 的编排调用

---

### 7.6 设计权衡说明

#### 为什么 v0.1 只做 Level 0？

**理由**：
1. **不造轮子**：Level 0 只需要 Prompt 中的重试逻辑，无需脚本
2. **验证优先**：先验证四阶段流程本身是否可行
3. **成本可控**：Level 1/2 需要大量 Git 脚本开发（2-3 周）
4. **需求不明确**：不确定用户是否真的需要自动 Git 回退

**如果 Level 0 不够用怎么办？**
- 人工介入时提供清晰的 Git 操作指导
- 收集用户反馈，决定是否投入 Level 1 开发

#### 为什么不做状态持久化？

**理由**：
1. **不造轮子**：TodoWrite 是 Claude Code 原生能力
2. **复杂度低**：无需管理 `.autodev/state.json` 文件
3. **够用**：TodoWrite 在 UI 中可见，中断后可以恢复基本进度

**如果 TodoWrite 不够用怎么办？**
- v0.1 用户反馈中如果有"状态丢失"问题，再考虑 v0.2 的文件持久化

#### 为什么不拆分指令文件？

**理由**：
1. **简单**：单文件更容易维护和调试
2. **够用**：600 行 Prompt 在 Claude Code 的上下文窗口内
3. **避免复杂性**：手动 Read 触发增加了系统复杂度

**如果 Prompt 遗忘问题严重怎么办？**
- v0.1 用户反馈中如果有"LLM 忘记指令"问题，再考虑 v0.3 的模块化

---
## 附录 A: 相关设计文档

- [AutoDev 架构 v2.0](ClaudeCodeAgentDocuments/01_DesignBaseLines/autodev-architecture-v2.md)
- [AutoDev 多版本迭代计划](ClaudeCodeAgentDocuments/01_DesignBaseLines/autodev-iteration-plan.md)
- [IDEA-006 Layer 3: Hooks 验证机制](ClaudeCodeAgentDocuments/01_DesignBaseLines/IDEA-006-implementation/layer3-hooks-validation.md)
- [Agent 设计标准](Claude/agents/aw-kernel/STANDARDS.md)
- [工具链文档](Claude/agents/aw-kernel/TOOLCHAIN.md)

---

## 附录 B: 贡献指南

### 如何提出新功能

1. 在 Issues 中创建 Feature Request
2. 描述问题背景和期望解决方案
3. 讨论并确认实现方案
4. 提交 PR 并关联 Issue

### 如何报告 Bug

1. 提供复现步骤
2. 附上相关日志（如有）
3. 说明期望行为 vs 实际行为

---

> 本路线图会随项目进展持续更新。最新版本请查看仓库中的 ROADMAP.md 文件。
