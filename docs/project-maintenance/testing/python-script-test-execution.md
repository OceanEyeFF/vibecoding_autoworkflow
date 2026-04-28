---
title: "Python Script Test Execution"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# Python Script Test Execution

> 目的：固定本仓库运行 Python 验证、治理检查和 closeout gate 的 operator-facing 命令口径。本文不定义 deploy 行为，也不授权 npm publish。

本页属于 [Testing Runbooks](./README.md)。deploy 主流程见 [Deploy Runbook](../deploy/deploy-runbook.md)，review / verify 口径见 [Review / Verify Handbook](../governance/review-verify-handbook.md)。

## Command Rule

在本仓库运行 Python 验证、部署或辅助命令时，默认使用：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 ...
```

这样可以避免在 `product/`、`docs/`、`toolchain/` 或 `tools/` 下生成 `.pytest_cache`、`__pycache__`、`.pyc` 或 `.pyo` 运行缓存。

## Governance Checks

涉及根目录、路径、分层、文档导航或治理规则时，先跑：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
```

这些检查分别覆盖：

- root / docs / product / toolchain / tools 分层和缓存污染规则
- 入口文档、frontmatter、相对链接和必要导航
- 关键语义合同、review/verify handoff、deploy/manual-runbook 语义同步

## Deploy Regression Tests

涉及 `toolchain/scripts/deploy/`、`aw-installer` wrapper、adapter deploy 行为或 package envelope 时，跑：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

如果改动同时影响 `toolchain/scripts/test/` 的治理脚本或 closeout gate 测试，补跑：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test -q
```

## Closeout Gate

涉及 closeout、gate、package surface、deploy docs、adapter behavior 或跨层治理时，最终跑：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json
```

closeout gate 会聚合 scope/spec/static/cache/test/smoke gates，并检查 Python / pytest 运行缓存是否污染受治理目录。

## Diff Hygiene

提交或交接前跑：

```bash
git diff --check
```

如果 `git diff --check` 失败，先修复空白问题，再重跑与改动面匹配的 Python 验证。

## Common Bundles

文档导航或治理文档改动：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
git diff --check
```

deploy / adapter / package wrapper 改动：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json
```
