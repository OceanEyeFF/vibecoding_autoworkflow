---
title: "aw-installer Release Operation Model — Review Findings"
status: superseded
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Release Operation Model — Review Findings

> 对 `docs-release-operation-model` 分支的 Code Review 结果，共确认 5 个问题。本文仅描述问题事实，不包含修复方案。

> 状态：这些发现已由后续 release review fix worktrack 处理；本文仅作为审查输入记录保留。

## 问题 1：Workflow YAML 示例与实际实现不一致

**位置**: `aw-installer-release-operation-model.md:87-115`

文档内联的 YAML 示例与 `.github/workflows/publish.yml` 实际内容存在差异。文档说 "The implemented workflow follows this shape"，但实际 workflow 比文档多出以下步骤：

**文档有但实际缺少/不同的内容：**

| 差异项 | 文档 | 实际 |
|---|---|---|
| `registry-url` | `"https://registry.npmjs.org"` (无末尾 `/`) | `"https://registry.npmjs.org/"` (有末尾 `/`) |

**文档缺失、实际存在的步骤：**

1. `env` 块：未记录 `PYTHONDONTWRITEBYTECODE`、`GITHUB_RELEASE_TAG`、`GITHUB_RELEASE_PRERELEASE`、`GITHUB_RELEASE_BODY` 环境变量注入
2. `Set up Python` (`actions/setup-python@v5` + `python-version: "3.13"`)
3. `Install test dependencies` (`python -m pip install --upgrade pip pytest jsonschema`)
4. `Resolve release metadata` (`node toolchain/scripts/deploy/bin/resolve-release-metadata.js`)
5. `Folder logic check` (`PYTHONDONTWRITEBYTECODE=1 python toolchain/scripts/test/folder_logic_check.py`)
6. `Governance tests` (`PYTHONDONTWRITEBYTECODE=1 python -m pytest toolchain/scripts/test`)
7. `Deploy package smoke` (`npm --prefix toolchain/scripts/deploy run smoke --silent`)
8. `Real publish guard` (`npm_config_tag="$NPM_CONFIG_TAG" node .../check-root-publish.js`，含 `AW_INSTALLER_PUBLISH_APPROVED=1` 和 `CI=true` 环境变量)
9. 最终的 `npm publish` 步骤：文档缺少 `AW_INSTALLER_PUBLISH_APPROVED: "1"` 和 `CI: "true"` 环境变量

文档内联了 9 个步骤，实际 workflow 有 15 个命名步骤（不含 `env` 块）。

---

## 问题 2：actions/checkout 未禁用凭据持久化

**位置**: `.github/workflows/publish.yml:22`

```yaml
- uses: actions/checkout@v4
```

此配置未设置 `persist-credentials: false`。当前 workflow 的 `permissions` 已声明 `contents: read`，因此即使凭据被持久化到本地 git config，也无法用于写操作。

但 publish workflow 不需要后续 git 操作（不 push、不创建 tag、不提交），持久化凭据是多余行为。GitHub Actions 安全最佳实践中，publish/deploy workflow 建议显式禁用凭据持久化作为纵深防御。

项目全局搜索未发现 `.github/` 目录下有任何 `persist-credentials` 的使用先例。

---

## 问题 3：canary channel 推导规则的文档不明确

**位置**: `aw-installer-release-operation-model.md:127`

文档 "Implemented Guard Shape" 节写：

```
- prerelease GitHub Releases map to npm `next` or `canary`; stable GitHub Releases map to npm `latest`.
```

"next or canary" 未说明何时选 `next`、何时选 `canary`。

**事实上的推导规则**（在 `toolchain/scripts/deploy/bin/check-root-publish.js` 的 `deriveReleaseChannelFromTag` 中实现）：

- 含 `canary` prerelease 标识符 → `canary`
- 以 `alpha`/`beta`/`rc` 开头的 prerelease 标识符 → `next`
- 无 prerelease → `latest`
- 其他 → 拒绝发布

`release-channel-contract.md` 的 channel 表格（第 30 行）对 `canary` 的描述为 "prerelease semver containing `canary`"，比操作模型文档更精确，但操作模型文档未引用该规则。

---

## 问题 4：审批边界链条缺乏导航汇总

**事实描述**：当前 `aw-installer` npm publish 审批涉及以下层次，分散在多个文件中：

1. `release-channel-contract.md` — 定义 publish readiness gate 的准入条件（12 条同时满足）
2. `aw-installer-release-operation-model.md` — 选择操作模型、添加 release-body marker 要求
3. `aw-installer-rc-approval-package.md` — 记录特定版本的审批决定
4. `package.json` — `awInstallerRelease` 元数据锁（`realPublishApproval`/`approvedVersion`/`approvedGitTag`/`approvedChannel`）
5. `.github/workflows/publish.yml` — CI 执行所有检查步骤
6. `resolve-release-metadata.js` — 验证 tag 匹配、prerelease/channel 一致性、release-body marker
7. `check-root-publish.js` — `prepublishOnly` guard，完整准入条件检查
8. npm registry 侧 Trusted Publisher 设置（repo 外部，需 package owner 手动配置）

这些层次各自有明确的职责边界，但没有任何一个文档为操作者提供从 "我要发布一个新版本" 到 "npm publish 成功" 的完整步骤导航。新操作者需要阅读至少 4 个独立文档才能理解完整流程。

---

## 问题 5：npm 最低版本 11.5.1 的选择原因未记录

**位置**: `aw-installer-release-operation-model.md:28` 和 `aw-installer-release-operation-model.md:83`

Control Signal 声明：

```
- minimum_npm_cli_for_trusted_publishing: `11.5.1`
```

正文描述为 "installs npm 11.5.1 on Node 24 for Trusted Publishing compatibility"。npm provenance/Trusted Publishing 功能从 npm 9.x 起已支持。`11.5.1` 这个具体版本号的选择原因（特定 bug 修复、OIDC 兼容性改进、或其他功能依赖）未在文档或代码注释中说明。

实际 workflow (`.github/workflows/publish.yml:37`) 同样硬编码了 `npm install -g npm@11.5.1`，也无注释说明版本理由。
