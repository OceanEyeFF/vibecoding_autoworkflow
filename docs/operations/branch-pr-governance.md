---
title: "Branch / PR 治理规则"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Branch / PR 治理规则

Decision time: 2026-04-03

> 目的：明确本仓库的分支与 PR 约束，让 review 与治理检查具备可重复入口。

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
- review 参考 `docs/operations/review-verify-handbook.md`

## 五、CI 最小检查链

PR 阶段必须通过以下最小链：

1. `python toolchain/scripts/test/folder_logic_check.py`
2. `python toolchain/scripts/test/path_governance_check.py`
3. `python toolchain/scripts/test/governance_semantic_check.py`
4. `python -m pytest toolchain/scripts/test/test_folder_logic_check.py toolchain/scripts/test/test_closeout_gate_tools.py`

## 六、例外与特批

- 若需要跳过上述检查，必须在 PR 中说明原因并获得显式批准。
- 不允许为了“过关”降低检查标准或替换证据。

## 七、相关文档

- `AGENTS.md`
- `docs/operations/review-verify-handbook.md`
- `docs/operations/path-governance-checks.md`
