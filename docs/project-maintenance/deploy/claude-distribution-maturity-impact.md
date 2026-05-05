---
title: "Claude Distribution Maturity Impact"
status: active
updated: 2026-05-03
owner: aw-kernel
last_verified: 2026-05-03
---
# Claude Distribution Maturity Impact

> 目的：把 “Claude 分发已经通过 Python adapter 和当前 checkout/local package 的 Node-owned `aw-installer` 落地 full Harness skill payload” 这一当前事实，与后续 TUI / registry / release / Python 退役成熟度工作分开，避免继续使用把 Claude 写成未落地或未来化的过期表述。

本页属于 [Deploy Runbooks](./README.md) 系列文档。实现细节先读 [`product/harness/adapters/claude/README.md`](../../../product/harness/adapters/claude/README.md)；历史设计切片见 [Claude Full Skill Distribution Design](./claude-full-skill-distribution-design.md)。

## Control Signal

- current_fact: `adapter_deploy.py --backend claude` 和当前 checkout/local package 的 `aw-installer --backend claude` package/local lifecycle 已经承接受控的完整 Harness skill payload lane。
- payload_fact: `product/harness/adapters/claude/skills/` 当前覆盖 `product/harness/skills/` 下的 19 个 canonical Harness skills。
- stale_framing: 把 Claude full skill distribution 写成尚未落地、等待未来实现，已不符合当前版本进度。
- maturity_decision: Claude 可以按 “adapter-backed compatibility lane 已成熟” 处理。
- maturity_limit: 该成熟度不自动等价于 TUI backend 选择、公网 registry smoke、stable/latest release、Python deploy adapter 可以退役，或 Claude 替代 `agents` 主线已经成熟。
- release_allowed_by_this_doc: no

## 当前成熟度拆分

### 已经成熟的工作面

- Python deploy adapter 已支持 `--backend claude` 的 full Harness skill payload install / diagnose / verify / update。
- 当前 checkout/local package 的 Node-owned `aw-installer` 已支持 `--backend claude` package/local diagnose human/JSON、`--claude-root`、check_paths_exist、verify、update dry-run human/JSON、install、prune --all 和 update --yes。
- Claude payload descriptors 已位于 `product/harness/adapters/claude/skills/<skill>/payload.json`。
- Claude target root 默认为 `.claude/skills/`，当前 target dir 使用 `<skill-name>`，旧 `aw-<skill-name>` 仅作为 legacy managed cleanup 入口。
- Claude payload 使用 canonical-copy，从 `product/harness/skills/` 复制 canonical skill 内容，deploy target 不是 source truth。
- Claude payload 已支持 `claude_frontmatter.disable-model-invocation: true`，用于保护 side-effecting 或控制流 skill。
- deploy 与 usage-help 文档已承认当前 full payload 事实，不再把 Claude 描述成 startup-only 分发。

### 仍未由该成熟度覆盖的工作面

- TUI 将 Claude backend 作为一等选择路径，而不是围绕 `agents` 主路径保持兼容。
- registry `npx aw-installer` 对 Claude install / verify / update 的公开 smoke 证据。
- stable/latest release 语义、npm dist-tag、GitHub Release、tag 或 remote 状态。
- Claude 替代 `agents` 成为默认或主分发路径。
- Python deploy adapter 删除或迁移到纯 Node 实现。

## 影响面

### Goal Charter

如果只表达当前事实，可以把 Claude 理解为 “adapter-backed compatibility lane 成熟”。如果要把长期目标从 `agents` 主线调整为 Codex / Claude 双主线，或把 Claude 改成默认分发对象，必须走 `repo-change-goal-skill`，不能在 deploy 文档中静默改写目标。

### Deploy Docs

deploy 文档需要避免以下过期口径：

- 把 Claude 写成 startup-only 分发。
- 把 Claude full payload 写成未落地。
- 把 Claude 分发写成当前不推进。

保留的边界表达是：

- Claude full payload 已由 Python adapter lane 和当前 checkout/local package Node-owned CLI 落地。
- Claude 仍是 `agents` mainline 旁路的 compatibility lane。
- TUI / registry / release maturity 仍需单独证据和 worktrack。

### Product And Adapter Payloads

当前事实落在：

- `product/harness/adapters/claude/skills/`
- `product/harness/skills/`
- `toolchain/scripts/deploy/adapter_deploy.py`

后续如果改变 payload set、target dir policy、frontmatter policy、legacy cleanup 或 marker 语义，必须同步更新 [`product/harness/adapters/claude/README.md`](../../../product/harness/adapters/claude/README.md)、验证矩阵和相关 adapter 测试。

### Toolchain And UI

Python adapter 目前是 Claude maturity 的 reference owner；当前 checkout/local package 的 Node-owned `aw-installer` 是 package/local runtime owner。TUI 仍应按独立 feature/config worktrack 处理：

- CLI: 当前 package/local `claude` lifecycle 走 Node-owned path；显式 `agents` GitHub-source update JSON/human/apply 也走 Node-owned path；未迁移 deploy behavior 仍可保留 Python reference/fallback。
- TUI: 明确 Claude 是否出现在 guided flow 中，以及文案是否会暗示 release/stable 支持。
- fallback: 保留 Python reference/fallback 时，operator-facing 语义不能把 fallback 写成未实现。

### Verification

Claude maturity 的最低证据不应只看文档。涉及实现面的后续工作至少应覆盖：

- `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'`
- `node --check toolchain/scripts/deploy/bin/aw-installer.js`
- `node --test toolchain/scripts/deploy/test_aw_installer.js`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_agents_adapter_contract.py`
- 临时 target repo 中的 Claude install / verify / update smoke
- 如进入 registry 试用，再补 package `.tgz` 或 `npx aw-installer@<version>` smoke

### Release And Package Surface

本页不授权任何 release。若把 Claude maturity 写入 public package、README、release notes、npm dist-tag 或 GitHub Release，必须先确认当前 registry/version/tag 事实，并经过对应 release approval gate。

## 推荐推进路线

### Phase A: 文档真相追平

承认 Claude full payload 已在 Python adapter lane 和当前 checkout/local package Node-owned CLI 落地，并把旧的未实现/未来化口径改成 “adapter-backed compatibility lane 已成熟，package/local runtime path 已 Node-owned”。本页覆盖当前阶段。

### Phase B: 证据补强

在不发布、不改 dist-tag、不推 remote 的前提下，为 Claude lane 增补临时 target repo、package `.tgz` 或 registry candidate smoke 证据。

### Phase C: TUI / Registry 成熟化

如果要让 Claude 进入 TUI 一等路径、registry public claim 或 stable/latest path，开独立 feature/config worktrack，并明确 fallback、测试和 operator-facing 文案。

### Phase D: 目标或发布升级

如果要把 Claude 从 compatibility lane 升为 co-primary lane、默认路径或 public stable claim，先走 Goal Charter / release approval，不在普通 deploy 文档里顺手扩大目标。

## Stop Gates

- 修改长期目标、主路径优先级或默认分发对象：停止，走 `repo-change-goal-skill`。
- 修改代码行为、TUI 或 adapter semantics：停止，开 feature/config worktrack。
- 删除 Python deploy adapter 或迁移到纯 Node：停止，开 migration worktrack。
- 改 package metadata、version、packlist public claim、release notes、tag、GitHub Release、npm publish、dist-tag 或 remote：停止，走 release / package approval。
- 扩大到 Claude runtime 发现机制、user-home global install 或自动更新 trust chain：停止，重新定范围。
