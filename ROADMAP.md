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

### 1.2 待开发

| 组件 | 优先级 | 说明 |
|------|--------|------|
| 执行日志系统 | 🔴 高 | Agent 调用记录、性能指标 |
| Hooks 钩子机制 | 🔴 高 | 执行前后的验证与增强 |
| 版本管理 | 🟡 中 | Agent 版本控制与迭代 |
| 自动更新 | 🟢 低 | 检测并拉取最新版本 |

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

## 六、实施时间线

### Phase 1: 基础设施 (2026 Q1)

| 周次 | 任务 | 优先级 | 状态 |
|------|------|--------|------|
| W1-W2 | 日志系统基础架构 | 🔴 高 | 📋 计划中 |
| W3-W4 | Hooks 钩子系统基础 | 🔴 高 | 📋 计划中 |
| W5-W6 | Agent 版本管理 + CHANGELOG | 🟡 中 | 📋 计划中 |
| W7-W8 | 健康检查 + 诊断工具 | 🟡 中 | 📋 计划中 |

### Phase 2: 增强功能 (2026 Q2)

| 周次 | 任务 | 优先级 | 状态 |
|------|------|--------|------|
| W1-W2 | 性能指标收集 | 🟡 中 | 📋 计划中 |
| W3-W4 | 核心 Agent v1.1 迭代 | 🔴 高 | 📋 计划中 |
| W5-W6 | Agent 编排系统原型 | 🟢 低 | 📋 计划中 |
| W7-W8 | 自动更新机制 | 🟢 低 | 📋 计划中 |

### Phase 3: 高级特性 (2026 Q3)

| 周次 | 任务 | 优先级 | 状态 |
|------|------|--------|------|
| W1-W4 | A/B 测试框架 | 🟢 低 | 📋 计划中 |
| W5-W8 | Agent 依赖管理 | 🟢 低 | 📋 计划中 |
| W9-W12 | 核心 Agent v2.0 迭代 | 🟡 中 | 📋 计划中 |

---

## 附录 A: 相关设计文档

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
