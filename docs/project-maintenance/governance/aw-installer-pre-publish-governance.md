---
title: "aw-installer Pre-Publish Governance"
status: active
updated: 2026-05-09
owner: aw-kernel
last_verified: 2026-05-09
---
# aw-installer Pre-Publish Governance

> 目的：定义 publish 前必须满足的最小 release-readiness 边界。

本页属于 [Governance](./README.md)。

管理 candidate tuple readiness、packlist/docs freshness、preflight 证据、approval lock；不管理发布序列、channel 策略、smoke 执行。

## Stop Rule

Tuple 不一致、preflight/smoke 证据缺失、docs 指向错误选择器或旧行为、本地 package smoke 未通过时停止；npm 版本不可变。

## 1. Candidate Tuple

Before approval, confirm:

| Field | Required check |
| --- | --- |
| package name | root `package.json` name is `aw-installer` |
| package version | valid semver, not `0.0.0-local`, not already published |
| git tag | exactly `v<package.version>` |
| npm dist-tag | matches the intended release channel |
| GitHub Release prerelease flag | matches the semver prerelease state |
| release body marker | includes `aw-installer-publish-approved: v<package.version>` |
| approval lock | `approvedVersion`, `approvedGitTag`, and `approvedChannel` match |

stable lanes 使用默认 `aw-installer` selector；RC lanes 必须用 `aw-installer@next`，不用裸 `aw-installer`。

## 2. Packlist And Docs Freshness

```bash
npm pack --dry-run --json
```

确认 packlist 包含入口点、payload descriptor、canonical skill payload 与 docs，排除状态/缓存/临时证据；root `README.md` 和 governance/testing/usage docs 指向正确选择器；deploy docs 不变成 release policy、testing docs 不变成 approval pages。若 package version、approval lock、selector 或 CLI surface 变化，publish 前先调用 `doc-catch-up-worker-skill` 做 source version docs freshness 检查；此时只能同步 source version facts，不得写入尚未发布的 registry fact。

## 3. Required Local Preflight Evidence

保留以下通过证据：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
npm --prefix toolchain/scripts/deploy test --silent
npm pack --dry-run --json
npm run publish:dry-run --silent
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json
```

证明 candidate surface 与 publish guard，不执行 publish。

## 4. Local Package Smoke

完成 [npx Command Test Execution](../testing/npx-command-test-execution.md) 定义的 local package smoke；证据要求属于本页，命令矩阵与 pass criteria 属 testing runbook。

## 5. Approval Lock

前述检查通过后才可设置 approval lock：

```json
{
  "realPublishApproval": "approved",
  "approvedVersion": "<package.version>",
  "approvedGitTag": "v<package.version>",
  "approvedChannel": "<latest|next|canary>"
}
```

本页只授权 tuple lock，不执行 release sequence。就绪后继续 [aw-installer Release Standard Flow](./aw-installer-release-standard-flow.md)。
