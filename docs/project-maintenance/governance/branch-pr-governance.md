---
title: "Branch / PR 治理规则"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
---
# Branch / PR 治理规则

Decision time: 2026-04-25

> 目的：明确本仓库的分支与 PR 约束，让 review 与治理检查具备可重复入口。

本页属于 [Governance](./README.md) 路径簇。

## 一、适用范围

适用于 `product/`、`docs/`、`toolchain/` 及根目录治理变更，以及引入或修改执行型治理对象（如 `.codex/`、review/verify 规则）。

## 二、分支约定

- `baseline branch`：由 `origin/HEAD` 动态解析的远端默认分支（当前为 `origin/HEAD -> master`），是 Worktrack 默认比较基准与 PR target 来源
- `protected baseline`：被远端保护规则覆盖的 baseline branch，只允许 PR 合并
- `worktrack branch`：围绕单个 Worktrack 的限定范围工作分支，不替代或改写 baseline
- `current branch`：当前本地分支，需显式确认角色，不自动等同 baseline 或 worktrack
- Worktrack Contract 的 `baseline_branch` 是 PR target/merge target/checkpoint 判定的权威字段，不在 skill/hook/runbook 中写死
- 推荐分支命名：`work/<topic>`、`fix/<topic>`、`docs/<topic>`

## 三、PR 规则

变更必须通过 PR 提交，target 来自 Worktrack Contract 的 `baseline_branch`（合同缺失时用 `origin/HEAD` 解析后补齐或阻断收尾）；PR 必须包含变更摘要、验证结果与风险说明，默认遵循 `.github/pull_request_template.md`。

## 四、Review 规则

`CODEOWNERS` 生效时至少需要对应 owner review；参考 `docs/project-maintenance/governance/review-verify-handbook.md`。

## 五、CI 最小检查链

PR 阶段必须通过：`folder_logic_check.py` + `path_governance_check.py` + `governance_semantic_check.py` + pytest（folder_logic + closeout_gate + agents_adapter_contract）。

## 六、远端保护规则

必须启用 GitHub Branch Protection Ruleset：仅允许 PR 合并到 protected baseline，必须通过 CI 最小检查链与 `CODEOWNERS` review，不允许 force push 与删除。规则集匹配 `origin/HEAD` 当前 baseline（当前为 `master`）；`origin/HEAD` 迁移时同步更新 ruleset、Worktrack `baseline_branch` 与本文 `last_verified`。

## 七、本地 pre-push hook

```bash
git config core.hooksPath toolchain/scripts/git-hooks
chmod +x toolchain/scripts/git-hooks/pre-push
```

hook 通过 `origin/HEAD` 动态解析 baseline（当前解析为 `origin/master`）；无法解析时保守阻断 `main`/`master`。本地 hook 是额外保险，不替代远端规则集。

## 八、例外与特批

- 若需跳过上述检查，须在 PR 中说明原因并获得显式批准。
- 禁止为"过关"降低检查标准或替换证据。

## 九、相关文档

- `AGENTS.md`
- `docs/project-maintenance/governance/review-verify-handbook.md`
- `docs/project-maintenance/governance/path-governance-checks.md`
