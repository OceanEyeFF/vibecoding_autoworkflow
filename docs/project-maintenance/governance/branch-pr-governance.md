---
title: "Branch / PR 治理规则"
status: active
updated: 2026-04-19
owner: aw-kernel
last_verified: 2026-04-19
---
# Branch / PR 治理规则

Decision time: 2026-04-03

> 目的：明确本仓库的分支与 PR 约束，让 review 与治理检查具备可重复入口。

本页属于 [Governance](./README.md) 路径簇。

## 一、适用范围

- 适用于 `product/`、`docs/`、`toolchain/` 及根目录治理变更
- 适用于引入或修改执行型治理对象（如 `.codex/`、review/verify 规则）

## 二、分支约定

- `main` 仅允许通过 PR 合并
- 推荐分支命名：
  - `work/<topic>`
  - `fix/<topic>`
  - `docs/<topic>`

## 三、PR 规则

- 变更必须通过 PR 提交
- PR 需包含：
  - 变更摘要
  - 验证结果
  - 风险与同步项说明
- 默认遵循 `.github/pull_request_template.md`

## 四、Review 规则

- `CODEOWNERS` 生效时，至少需要对应 owner review
- review 参考 `docs/project-maintenance/governance/review-verify-handbook.md`

## 五、CI 最小检查链

PR 阶段必须通过以下最小链：

1. `python toolchain/scripts/test/folder_logic_check.py`
2. `python toolchain/scripts/test/path_governance_check.py`
3. `python toolchain/scripts/test/governance_semantic_check.py`
4. `python -m pytest toolchain/scripts/test/test_folder_logic_check.py toolchain/scripts/test/test_closeout_gate_tools.py toolchain/scripts/test/test_agents_adapter_contract.py`

## 六、远端保护规则（Branch Protection Ruleset）

必须在 GitHub 使用 Branch Protection Ruleset 强制执行：

- 仅允许通过 PR 合并到 `main`
- 必须通过 CI 最小检查链
- 必须满足 `CODEOWNERS` review
- 禁止 force push、禁止删除受保护分支

规则集匹配目标：`main` 分支。

## 七、本地 pre-push hook

本地必须启用 hook，阻断直接 push 到 `main`：

```bash
git config core.hooksPath toolchain/scripts/git-hooks
chmod +x toolchain/scripts/git-hooks/pre-push
```

说明：本地 hook 只是额外保险，不能替代远端规则集。

## 八、例外与特批

- 若需要跳过上述检查，必须在 PR 中说明原因并获得显式批准。
- 不允许为了“过关”降低检查标准或替换证据。

## 九、相关文档

- `AGENTS.md`
- `docs/project-maintenance/governance/review-verify-handbook.md`
- `docs/project-maintenance/governance/path-governance-checks.md`
