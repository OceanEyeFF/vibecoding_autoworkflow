---
title: "Deploy Script Governance Inventory"
status: draft
updated: 2026-05-02
owner: aw-kernel
last_verified: 2026-05-02
---
# Deploy Script Governance Inventory

> 目的：为后续是否删除 Python deploy 面提供可执行盘点和设计边界。本文只记录当前 deploy surface、引用方、分类与迁移建议；不授权删除代码、修改 package metadata、发布新版本、改 release tag、改远程或改 `.aw/` 控制面。

本页属于 [Deploy Runbooks](./README.md) 系列。入口合同见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)，payload 与 update trust boundary 见 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)。

## Control Signal

当前结论：迁移目标是替换 `aw-installer` 发布/runtime 执行路径上的 Python 依赖，不是清空仓库里的 Python。不要直接删除 Python deploy 面。先把必须在目标执行路径上无 Python 也安全可用的 `aw-installer` command surface 收敛到 Node-owned 实现，并用现有 Python reference 与 tests 做等价验证；只有当对应 Node path 覆盖 install、verify、diagnose、update、prune、path/marker handling、JSON、package-local、GitHub-source、agents、Claude 和 operator-error semantics 后，才允许逐项移除 Python runtime dependency。`adapter_deploy.py`、Python tests、governance scripts 和 scaffold tooling 可以在迁移期继续作为 reference / parity / governance tooling 保留；真正要从 package runtime 中退出的是 `aw-installer` fallback、`harness_deploy.py` compatibility wrapper、`aw-harness-deploy` Python alias 和 root/local package `files` 中的 runtime Python payload。

已验证进度：Slice A 已把 package/local-source `aw-installer check_paths_exist --backend agents` 收敛为 Node-owned 只读路径；Slice B 已把 package/local-source `aw-installer verify --backend agents` 收敛为 Node-owned 只读路径；Slice C 已把 package/local-source clean-target `aw-installer install --backend agents` 收敛为 Node-owned 写入路径；Slice D 已把 package/local-source `aw-installer prune --all --backend agents` 收敛为 Node-owned 删除路径；Slice E 已把 package/local-source `aw-installer update --backend agents --yes` 收敛为 Node-owned composition path；Slice G 已把 package/local-source human-readable `aw-installer update --backend agents` dry-run 与 TUI dry-run 展示收敛为 Node-owned plan rendering。已完成切片均保留 Python reference parity 或 failing-Python sentinel 证据；Slice C 只覆盖 target root 缺失或为空目录的 clean-target install，non-clean target install 子命令仍走 Python/reference；Slice D 只删除 current-backend recognized managed installs，并保留 foreign、unrecognized、invalid-marker 和用户内容；Slice E 只组合已验证的 `prune --all -> check_paths_exist -> install -> verify`，保留 blocking preflight、failure short-circuit、post-apply strict verify 和 recovery hint；Slice G 只覆盖 package/local `agents` dry-run rendering，不扩展 apply 语义。不引入远程 fetch，不碰 release metadata，不改变 package version，不扩展 GitHub-source update，也不删除 Python reference。

下一步建议：把后续工作排成 runtime no-Python 迁移切片，而不是一次性删除 Python。TUI dry-run Node rendering、agents 剩余 fallback 收敛可以作为普通本地 implementation worktrack 候选；Claude backend Node-owned lifecycle 仍需要新的 route decision / approval 后才能实施。GitHub-source update 属于 remote fetch/trust boundary，package packlist removal、Python runtime file removal、release metadata 或实际发布属于 release/package boundary，都需要新的显式审批和独立 gate。

停止线：

- 不删除 `adapter_deploy.py`、`harness_deploy.py`、`aw_scaffold.py` 或 Python tests。
- 不继续修改 package metadata、release approval lock、tag、remote、npm dist-tag 或 GitHub Release；JS wrapper 只允许在已批准 Slice A-E 的 Node-owned parity 边界内修改。
- 不把未实现的 Node path 写成已完成事实。
- 不把 `aw_scaffold.py` 的 `.aw_template` scaffold 语义并入 deploy package removal scope；它是 adjacent template tooling，不是 runtime installer target path。
- 不把仓库治理脚本、Python parity tests 或 scaffold helper 的存在视为 runtime Python 替换失败；runtime 替换只以 package/local 或 registry-style `aw-installer` 目标执行路径是否需要 Python 为准。

## Required Node-Owned Command Surface

以下能力必须在目标执行路径无 Python 时保持安全可用，才能讨论删除相应 Python deploy path。

| Surface | Required semantics before Python removal |
|---|---|
| `install` | 读取 package-local 或明确 source root 的 payload descriptor；写入前验证 source contract、target root、duplicate target dir、path conflicts 和 marker policy；写入文件权限稳定；失败前不得部分写业务 payload。 |
| `verify` | 只读严格复验 source、target root、payload files、target entry、`payload.json`、`aw.marker`、fingerprint drift、conflict 与 unrecognized 状态；发现 issue 必须非零退出。 |
| `diagnose` | 只读状态投影；`--json` 输出稳定 schema；发现 issue 仍可 0 退出；不能被 operator 误解为安装成功证明。 |
| `update` | 默认 dry-run；`--yes` 只包装 `prune --all -> check_paths_exist -> install -> verify`；不做自动回滚、增量修复、archive/history 或自升级。 |
| `prune` | `prune --all` 只删除当前 backend 可识别、带有效 marker、属于我方的 managed install；foreign/unrecognized 用户目录保留。 |
| Path handling | 保持 `path_safety_policy.json` 共享策略：保护系统根、home credential dirs、source/target root validation、backend root override、missing/broken symlink/wrong type classification。 |
| Marker handling | 保持 `aw-managed-skill-marker.v2` 语义，marker 只证明 live managed install，不成为 source truth、history 或 remote provenance。 |
| JSON | `diagnose --json` 和 `update --json` schema 保留 `backend`、`source_kind`、`source_ref`、`source_root`、`target_root`、binding count、managed/conflict/unrecognized counts、issue objects 和 blocking issue fields。 |
| Package-local source | 不设置 `AW_HARNESS_REPO_ROOT` 时从 package/check-out envelope 读取 source payload，并以当前工作目录作为 target repo root；source 与 target 不得意外重合。 |
| GitHub-source | `update --source github --github-repo OWNER/REPO --github-ref REF` 只把 GitHub archive 作为本次 source root；必须验证 archive source contract、可选 sha256、safe zip extraction、temp cleanup、target root 不回退到 source root。 |
| `agents` backend | 默认写入 `<target_repo>/.agents/skills/<target_dir>`；当前主用户路径必须优先 Node-owned。 |
| `claude` backend | 写入 `<target_repo>/.claude/skills/<target_dir>`；保留 full Harness skill payload 与 legacy `aw-<skill_id>` recognition；不得写成 `agents` 替代主路径。 |
| Operator errors | Help/version、TUI non-interactive guard、timeout、missing Python fallback、invalid source, invalid target, conflict, broken symlink, foreign marker 和 verify failure 的 exit code/stderr/stdout 语义必须可测试。 |

## Deploy Script Inventory

### Python Deploy Implementation

| Path | Current role | Removal classification | Rationale |
|---|---|---|---|
| `toolchain/scripts/deploy/adapter_deploy.py` | Core reference implementation for `install`, `check_paths_exist`, `verify`, `diagnose`, `prune`, `update`, path safety, GitHub archive source, source/target resolution, payload copy, marker/fingerprint and backend behavior. | split-later | Too much behavior remains Python-owned. Remove only after Node parity covers each command/backend/source mode and tests no longer require Python on target execution path. |
| `toolchain/scripts/deploy/harness_deploy.py` | Stable thin Python wrapper preserving `adapter_deploy.py` CLI semantics for package and npx fallback. | remove-after-node-parity | It can be removed only after `aw-installer` no longer needs Python fallback for any supported target path and `aw-harness-deploy` compatibility is retired or reimplemented. |
| `toolchain/scripts/deploy/aw_scaffold.py` | Legacy `.aw_template` scaffold generator/validator for `.aw/` runtime examples, not the package deploy target path. | retain | It is outside Python deploy removal. Treat separately if template tooling is ever migrated to Node. |

### Python Tests Under `toolchain/scripts/deploy/`

| Path | Current role | Removal classification | Rationale |
|---|---|---|---|
| `toolchain/scripts/deploy/test_adapter_deploy.py` | Broad regression suite for Python adapter, wrappers, package metadata, publish guards, Node-owned diagnose/update JSON, path safety, CLI/TUI wrapper behavior and packlist smoke. | split-later | Keep as reference/parity suite during migration. Later split into Node behavior tests, release metadata tests and any retained Python scaffold tests. |
| `toolchain/scripts/deploy/test_aw_scaffold.py` | Tests `.aw_template` scaffold validation/generation. | retain | Belongs to scaffold/template tooling, not runtime deploy deletion. |

### JS Wrappers And Package Metadata

| Path | Current role | Removal classification | Rationale |
|---|---|---|---|
| `toolchain/scripts/deploy/bin/aw-installer.js` | Primary Node bin. Owns help/version, `agents diagnose --json`, package-local `agents update` JSON and human-readable dry-run, package/local `agents check_paths_exist`, `verify`, clean-target `install`, `prune --all`, `update --yes` composition, TUI shell, environment filtering and Python fallback. | retain | This is the target owner for deploy runtime. Through Slice G, Node-owned behavior covers package/local agents `check_paths_exist`, `verify`, clean-target `install`, recognized same-backend managed-install `prune --all`, `update --backend agents` dry-run, TUI dry-run display, and `update --backend agents --yes` composition; unsupported variants still fall back to Python/reference until their named slices pass. |
| `toolchain/scripts/deploy/bin/aw-harness-deploy.js` | Compatibility alias that directly shells out to Python wrapper. | remove-after-node-parity | Remove or reimplement only after compatibility policy and release contract allow dropping Python fallback. |
| `toolchain/scripts/deploy/test_aw_installer.js` | Node unit tests for path safety, payload parsing, fingerprinting, JSON command parsing and update planning helpers. | retain | Expand as Node-owned behavior grows. |
| `toolchain/scripts/deploy/package.json` | Local package scaffold with bins and local smoke/test scripts. | retain | Do not modify in this worktrack; later keep aligned with root package only through release-approved metadata changes. |
| `package.json` | Root self-contained `aw-installer` package envelope, bin mapping, packlist, publish guard metadata and release approval lock. | retain | Release-owned. Not part of Python deletion except packlist must eventually stop shipping removed Python files after approval. |
| `toolchain/scripts/deploy/path_safety_policy.json` | Shared JS/Python source/target safety policy. | retain | Must remain the single policy source while both implementations exist; can stay as data after Python removal. |

### Release Helper References

| Path | Current role | Removal classification | Rationale |
|---|---|---|---|
| `toolchain/scripts/deploy/bin/check-root-publish.js` | Real publish guard for root package release approval, version/tag/channel and packlist constraints. | retain | Release boundary; not a deploy runtime deletion target. |
| `toolchain/scripts/deploy/bin/publish-dry-run.js` | Publish dry-run helper. | retain | Release boundary; no Python deploy dependency removal needed. |
| `toolchain/scripts/deploy/bin/resolve-release-metadata.js` | GitHub Release metadata resolver for publish workflow. | retain | Release boundary; only validates release metadata. |
| `toolchain/scripts/test/npm_pack_tarball.sh` | Root tarball pack helper for smoke tests. | retain | Needed to validate package-local runtime behavior. |
| `toolchain/scripts/test/npm_pack_tarball_result.js` | Pack result resolver used by smoke/closeout tests. | retain | Release/package validation helper. |

## `toolchain/scripts/test/` Deploy-Related Inventory

| Path | Semantics referenced | Classification for Python removal |
|---|---|---|
| `toolchain/scripts/test/aw_installer_cli/test_cli_commands.py` | CLI help/version/default, `agents` and `claude` lifecycle, GitHub-source fallback currently remains Python, TUI non-interactive guard. | split-later; convert lifecycle expectations to Node-owned parity while keeping GitHub/Claude fallback tests until migrated. |
| `toolchain/scripts/test/aw_installer_tui/test_tui_interactions.py` | Interactive TUI menu, diagnose Node JSON, strict verify, update dry-run, guided update cancel/apply. | retain; update assertions as Node-owned commands replace fallback. |
| `toolchain/scripts/test/aw_installer_registry_npx_smoke.js` | Published registry npx smoke across temporary targets; help/version/TUI guard/diagnose/update JSON/install/verify/update apply/final diagnose. | retain; must prove no-Python target path after migration. |
| `toolchain/scripts/test/aw_installer_registry_npx_smoke.sh` | Shell entry for registry npx smoke. | retain. |
| `toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh` | Local `.tgz` package smoke; clears source/target env and validates package-local source separation. | retain; promote as main validation for Node-owned package-local path. |
| `toolchain/scripts/test/test_agents_adapter_contract.py` | Agents/Claude payload descriptor contract, target dir uniqueness, diagnose JSON missing/wrong type target behavior. | split-later; keep payload contract checks, migrate diagnose execution assertions to Node when parity is complete. |
| `toolchain/scripts/test/test_set_harness_goal_deploy_aw.py` | `set-harness-goal-skill/scripts/deploy_aw.py` Claude cold-start helper and `.aw` generation behavior. | retain; separate cold-start helper, not adapter deletion. |
| `toolchain/scripts/test/test_closeout_gate_tools.py` | Closeout gate references deploy target roots, npm pack tarball, package version/packlist, tarball exec, local deploy target smoke and bytecode-free Python command execution. | split-later; keep closeout governance, update package/deploy checks as Node surface becomes canonical. |
| `toolchain/scripts/test/test_publish_workflow_contract.py` | Publish workflow, release metadata resolver and pre-publish validation gates. | retain; release boundary. |
| `toolchain/scripts/test/closeout_acceptance_gate.py` | Closeout orchestration includes deploy/package gates and local deploy target checks. | split-later; gate should eventually assert Node-owned no-Python runtime evidence. |
| `toolchain/scripts/test/folder_logic_check.py` | Governance check for folder/layer rules; deploy docs are part of allowed maintenance layer. | retain. |
| `toolchain/scripts/test/path_governance_check.py` | Governance check for path rules. | retain. |
| `toolchain/scripts/test/governance_semantic_check.py` | Governance semantic check. | retain. |
| `toolchain/scripts/test/governance_assess.py`, `test_governance_assess.py`, `test_governance_eval_tools.py`, `repo_governance_eval.py`, `test_repo_governance_eval.py`, `harness_scope_gate.py`, `test_harness_scope_gate.py`, `scope_gate_check.py`, `cache_scan_policy.py`, `gate_status_backfill.py` | General governance/gate/cache/status tools with deploy references only through gate or policy context. | retain; not candidates for Python deploy removal. |
| `toolchain/scripts/test/README.md`, `docs/project-maintenance/testing/python-script-test-execution.md` referenced tests | Operator-facing test execution guidance. | split-later docs only; update after implementation, not now. |

## Operator-Facing Documentation References

These docs currently mention Python deploy behavior, npx/package behavior, release behavior or deploy testing. This inventory lists path and semantic dependency; implementation slices update the relevant docs only after verified behavior exists.

| Path | Operator-facing semantic reference |
|---|---|
| `docs/project-maintenance/deploy/README.md` | Deploy runbook index and navigation. |
| `docs/project-maintenance/deploy/distribution-entrypoint-contract.md` | Defines `aw-installer` CLI/TUI command surface, current Node-owned pieces and Python fallback boundaries. |
| `docs/project-maintenance/deploy/payload-provenance-trust-boundary.md` | Defines package-local source, target root, GitHub-source archive, trust boundary and no-auto-update limits. |
| `docs/project-maintenance/deploy/deploy-runbook.md` | Destructive reinstall operator flow and verify/diagnose semantics. |
| `docs/project-maintenance/deploy/deploy-mapping-spec.md` | Source/backend/target/payload/marker mapping and `install`/`verify`/`diagnose`/`prune` constraints. |
| `docs/project-maintenance/deploy/agents-adapter-source.md` | Agents adapter source and payload descriptor expectations. |
| `docs/project-maintenance/deploy/claude-adapter-source.md` | Claude adapter source and compatibility/full-skill payload expectations. |
| `docs/project-maintenance/deploy/claude-full-skill-distribution-design.md` | Claude full skill distribution design and backend boundary. |
| `docs/project-maintenance/deploy/skill-deployment-maintenance.md` | Drift, conflict, diagnostic and maintenance recovery flows. |
| `docs/project-maintenance/deploy/skill-lifecycle.md` | Add/update/rename/remove skill lifecycle and adapter payload updates. |
| `docs/project-maintenance/deploy/aw-installer-public-quickstart-prompts.md` | External trial copy/paste commands and operator expectations. |
| `docs/project-maintenance/deploy/aw-installer-external-trial-feedback.md` | Feedback evidence and issue reporting path for `aw-installer`. |
| `docs/project-maintenance/deploy/aw-installer-npx-pre-publish-check.md` | Pre-publish packlist, docs, metadata, dry-run and smoke requirements. |
| `docs/project-maintenance/deploy/release-channel-contract.md` | Version/channel/dist-tag/release approval rules. |
| `docs/project-maintenance/deploy/aw-installer-release-operation-model.md` | Trusted Publishing/manual fallback workflow, publish guard and release metadata. |
| `docs/project-maintenance/deploy/github-release-publish-standard-flow.md` | GitHub Release creation, publish workflow, post-publish npx smoke and release evidence. |
| `docs/project-maintenance/deploy/template-tooling-mvp.md` | `aw_scaffold.py` commands; adjacent scaffold tooling, not runtime deploy deletion. |
| `docs/project-maintenance/deploy/template-consumption-spec.md` | Template consumption; adjacent to `.aw_template`, not package runtime install. |
| `docs/project-maintenance/deploy/existing-code-adoption.md` | Existing project adoption flow and `.aw` initialization context. |
| `docs/project-maintenance/testing/README.md` | Testing navigation for Python scripts, governance checks, npx/package smoke and CLI/TUI regression. |
| `docs/project-maintenance/testing/python-script-test-execution.md` | Bytecode-free Python command execution and governance/deploy test invocation. |
| `docs/project-maintenance/testing/npx-command-test-execution.md` | Registry/local `.tgz` npx smoke, command matrix, evidence logs, env clearing and remote clone boundaries. |
| `docs/project-maintenance/testing/codex-post-deploy-behavior-tests.md` | Post-deploy Codex behavior smoke distinct from deploy target alignment. |
| `docs/project-maintenance/testing/claude-post-deploy-behavior-tests.md` | Claude adapter and cold-start helper smoke references. |
| `docs/project-maintenance/usage-help/README.md` | Usage-help navigation for deploy main flow and backend-specific paths. |
| `docs/project-maintenance/usage-help/codex.md` | `agents` deploy verify, Python adapter examples, npx/tgz external trial and `--agents-root` override. |
| `docs/project-maintenance/usage-help/claude.md` | `claude` backend, Python adapter lane and `deploy_aw.py` cold-start helper boundary. |

## Classification Summary

| Class | Paths |
|---|---|
| remove | None now. No Python path is safe to delete before Node parity and release boundary approval. |
| remove-after-node-parity | `toolchain/scripts/deploy/harness_deploy.py`, `toolchain/scripts/deploy/bin/aw-harness-deploy.js` compatibility behavior, Python fallback branches in `toolchain/scripts/deploy/bin/aw-installer.js`, and root/local package `files` entries for removed Python deploy runtime files. |
| retain | `aw_scaffold.py`, `test_aw_scaffold.py`, release helpers, package metadata until release-approved, `path_safety_policy.json`, npx smoke runners, publish workflow tests and governance checks. |
| split-later | `adapter_deploy.py`, `test_adapter_deploy.py`, CLI/TUI integration tests, adapter contract tests and closeout gate checks. Split into Node-owned runtime tests, retained scaffold/release tests and temporary Python parity tests. |

## Recommended Implementation Sequence

Implement migration through smaller gates after this inventory is accepted:

1. Slice A: Node-owned `check_paths_exist` plus strict source/target/path classification parity for `agents` package-local source. Status: verified. This slice is read-only: no writes, no deletes, no update composition. It proved issue codes, exit behavior, stdout/stderr, duplicate target dir handling, conflict path reporting, target root validation and failing-Python sentinel behavior.
2. Slice B: Node-owned `verify --backend agents` package-local. Status: verified. This slice remains read-only and covers marker, fingerprint drift, target entry, payload file alignment, missing target, wrong type, broken symlink, unrecognized directory, foreign marker and unexpected managed directory cases.
3. Slice C: Node-owned `install --backend agents` into a clean temp target only. Status: verified. This slice introduces writes only after read-only parity is stable, and covers missing target root, existing empty target root, clean install, source contract validation, target readiness, non-clean fallback, out-of-scope fallback, path conflict prevention and partial-write prevention.
4. Slice D: Node-owned `prune --all` for recognized managed `agents` installs. Status: verified. This slice isolates delete behavior from install/update composition and proves missing target root no-op, wrong target root blocking, same-backend marker deletion, stale same-backend marker deletion, foreign/unrecognized/invalid-marker/user content retention and Python reference output parity.
5. Slice E: `update --backend agents --yes` composition. Status: verified. This slice validates package/local `prune --all -> check_paths_exist -> install -> verify` orchestration, no-Python target execution, Python reference output shape, blocking preflight, recoverable target states, strict post-apply verify and recovery hints.

The next runtime no-Python backlog should continue with named slices instead of broad deletion:

6. Slice F: Node-owned `claude` backend local/package lifecycle. Candidate scope: package/local `diagnose --json`, `update --json`, `check_paths_exist`, `verify`, clean-target `install`, `prune --all`, and `update --backend claude --yes`, preserving full Harness skill payload, `.claude/skills/<skill_id>` target naming, legacy `aw-<skill_id>` managed cleanup recognition, Claude-specific payload version/frontmatter constraints, strict verify, and failing-Python sentinel evidence. This is an approval-gated implementation worktrack because it is a Claude backend migration; it must not promote Claude to the `agents` main path, change release channel, or remove Python runtime files.
7. Slice G: Node-owned human-readable update dry-run rendering for package/local agents backend and TUI usage. Status: verified. This slice makes TUI dry-run display reuse Node update plan data instead of Python wrapper output, preserves dry-run-only behavior, and does not change mutating semantics or add release behavior.
8. Slice H: agents remaining fallback cleanup. Candidate scope: decide and implement Node-owned or explicitly unsupported behavior for non-clean target standalone `install` and any remaining package/local unsupported variants so target users do not silently need Python for the ordinary `agents` runtime path.
9. Slice I: GitHub-source update migration. Candidate scope: Node-owned `--source github` archive download, optional sha256 verification, safe zip extraction, source contract validation, temp cleanup, target/source separation and no auto-upgrade semantics. This crosses the remote fetch/trust boundary and needs explicit approval before implementation.
10. Slice J: runtime Python fallback and package payload retirement. Candidate scope: remove or reimplement `aw-harness-deploy`, remove `aw-installer` Python fallback branches, drop `harness_deploy.py` / `adapter_deploy.py` from package runtime `files`, and update closeout/release smoke to prove no-Python registry/package execution. This crosses package metadata, packlist and release boundary; it requires explicit approval and release-channel gates. `adapter_deploy.py` may remain in the repository as reference after it exits the package runtime payload.

Keep Python reference callable in CI and local tests for parity throughout this sequence. Do not remove fallback until all relevant Node-owned slices pass and a release-approved packlist/package boundary exists.

Reuse `path_safety_policy.json`, payload descriptor parsing, fingerprint order and marker schema already covered by `test_aw_installer.js`. As slices graduate, split broad `split-later` test surfaces into:

- temporary Python parity assertions used only until the matching Node slice is accepted
- permanent Node behavior tests for the canonical command surface
- retained release/scaffold governance tests that are not deploy runtime migration targets

Non-goals for upcoming runtime no-Python slices unless explicitly named:

- No full-repository Python deletion.
- No Claude backend migration before Slice F approval.
- No GitHub-source migration before Slice I approval.
- No Python runtime payload deletion or package metadata change before Slice J approval.
- No release package version, dist-tag, approval lock, tag, npm publish or GitHub Release change.
- No docs rewrite except implementation-specific docs after verified behavior exists.

## Validation Requirements

For this inventory-only worktrack, lightweight validation is enough:

```bash
git diff --check -- docs/project-maintenance/deploy/deploy-script-governance-inventory.md docs/project-maintenance/deploy/README.md
```

For a future Node-owned implementation slice, minimum validation should include:

- `npm --prefix toolchain/scripts/deploy test --silent`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest toolchain.scripts.deploy.test_adapter_deploy`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/aw_installer_cli toolchain/scripts/test/aw_installer_tui`
- `toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh --skip-remote`
- a package-local no-Python sentinel smoke that shadows `py`, `python`, and `python3` with failing binaries and proves the currently claimed Node-owned `agents` package-local commands do not invoke Python. Through Slice G this covers `diagnose`, `update --json`, human-readable `update`, TUI dry-run display, `check_paths_exist`, `verify`, clean-target `install`, `prune --all`, and `update --yes`; GitHub-source update, Claude backend and unsupported variants remain Python/reference paths until separately implemented and approved.
- `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`

The exact command set can be narrowed by the implementation diff, but any claim that Python is no longer on the target execution path must include package-local `.tgz` or registry-style smoke evidence.
For Node-owned deploy command claims, package-local or registry-style smoke must include a failing-Python sentinel; a smoke that can pass through silent Python fallback is not sufficient evidence.

## Release And Remote Boundaries

- This inventory does not authorize npm publish, GitHub Release creation, tag movement, dist-tag movement, remote branch writes or approval-lock changes.
- Removing Python files from root package packlist is a release-visible change and must go through release-channel approval, pack dry-run, publish dry-run and npx smoke evidence.
- GitHub-source support is remote fetch behavior, not package-local behavior. It must remain explicit through `--source github --github-repo OWNER/REPO --github-ref REF`, must not silently resolve channels, and must not auto-upgrade the installer package.
- External trial docs and release docs must be updated only after verified implementation facts exist. Until then, they should keep describing current Python fallback boundaries.
