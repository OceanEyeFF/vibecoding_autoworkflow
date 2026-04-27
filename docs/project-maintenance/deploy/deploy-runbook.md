---
title: "Deploy Runbook"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# Deploy Runbook

> 目的：提供当前仓库的 deploy 快速上手指南，固定 destructive reinstall model：`prune --all -> check_paths_exist -> install --backend agents`。`diagnose` 与 `verify` 只保留为辅助、只读的诊断与复验命令。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先了解以下背景：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [Deploy Mapping Spec](./deploy-mapping-spec.md) —— 部署映射规范

本页只保留快速入门和主流程。维护诊断请查看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)，业务生命周期边界请查看 [skill-lifecycle.md](./skill-lifecycle.md)。

外部试用不要直接从本文截取 `npx aw-installer` 目标形态作为已发布事实。先使用 [aw-installer Public Quickstart Prompts](./aw-installer-public-quickstart-prompts.md) 的 pre-release `.tgz` 路径；反馈走 [aw-installer External Trial Feedback Contract](./aw-installer-external-trial-feedback.md)、[trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 或 [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)；发布前多目标隔离验证走 [aw-installer Multi Temporary Workdir Smoke](./aw-installer-multi-temp-workdir-smoke.md)。

## 一、什么时候看这页

以下场景建议先读本文：

- 首次给 `agents` backend 做安装
- 已有安装，但想按当前 live source 完整重装
- 想确认 deploy 主流程现在到底只剩哪三步
- 想确认 `verify` 还做什么、但不再属于哪条主线

## 二、当前实现状态

统一入口脚本：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py
```

当前已实现的后端：

- `agents` —— 对应 `Codex / OpenAI`

当前还提供一个语义等价的本地薄包装入口，用于后续分发包装复用：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py
```

`harness_deploy.py` 不表示 npm release channel 已发布；它只包装当前 `adapter_deploy.py` 命令面。当前根目录 `package.json` 是 self-contained `aw-installer` npm 包络，本地 package scaffold 仍暴露 `aw-installer` bin、`aw-installer tui` 最小交互 shell和 `aw-harness-deploy` 兼容别名；`tui` 主入口是 guided update flow，按 `diagnose -> update dry-run plan -> explicit yes -> update --yes` 调用同一 wrapper。当前还没有执行 npm publish，也没有引入 full-screen TUI framework。

本地 npm-style scaffold 可用下面的 smoke 命令验证 bin 入口能打开同一 help surface：

```bash
npm --prefix toolchain/scripts/deploy run smoke --silent
```

如果要检查目标 `npx aw-installer` package envelope，在仓库根目录运行 dry-run：

```bash
npm pack --dry-run --json
```

该 packlist 必须包含 `product/harness/skills`、`product/harness/adapters/agents/skills` 与 `toolchain/scripts/deploy/` wrapper 文件，并且不得包含 `.aw/`、`.agents/` 或 `.autoworkflow/`。

`aw-installer` package payload provenance、source/target root 解析与 `update` trust boundary 见 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)。当前 `update` 只使用当前 package 或 checkout 中的 source payload，不执行远程 fetch、channel 解析、自升级、验签或自动回滚。

发布前 dry-run 只验证 npm publish 包面和 registry 配置，不上传 package：

```bash
npm run publish:dry-run --silent
```

根 package 的 `publishConfig.registry` 固定为 `https://registry.npmjs.org/`，避免本机 npm mirror 配置影响目标 release channel。根 package 的 `prepublishOnly` guard 会允许这个 dry-run；真实 `npm publish` 必须满足 [aw-installer Release Channel Contract](./release-channel-contract.md) 中定义的非 local semver、release channel、npm dist-tag、CI、审批信号和 git tag 准入。真实发布仍需要单独确认 npm 凭证、release notes 和回滚/撤回计划。

本地 scaffold packlist 仍在 scaffold package root 内检查：

```bash
cd toolchain/scripts/deploy
npm pack --dry-run --json
```

该 dry-run 不应在仓库中留下 `.tgz` package artifact。

更接近真实分发路径的 smoke 应从根目录把 package 打到临时目录，再从 `.tgz` 在隔离 target repo 中执行 bin：

```bash
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
package_file="$(node -e "const fs = require('node:fs'); const payload = JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); console.log(payload[0].filename);" "$tmpdir/pack.json")"
target_repo="$tmpdir/target-repo"
mkdir -p "$target_repo"
(
  cd "$target_repo"
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer --help
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer --version
  if AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer tui > "$tmpdir/tui.out" 2> "$tmpdir/tui.err"; then
    echo "expected aw-installer tui to require an interactive terminal" >&2
    exit 1
  fi
  test ! -s "$tmpdir/tui.out"
  grep -F "aw-installer tui requires an interactive terminal" "$tmpdir/tui.err"
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer diagnose --backend agents --json
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer update --backend agents --json
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer install --backend agents
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer verify --backend agents
  AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer update --backend agents --yes
)
```

这里显式清空 `AW_HARNESS_REPO_ROOT` 与 `AW_HARNESS_TARGET_REPO_ROOT`，用于验证 packaged wrapper 会从 package 内读取 source payload，并把当前工作目录作为 target repo root。packaged `tui` 在非交互环境必须明确拒绝；`update --json` 只运行 dry-run JSON plan；随后 `install` 只写临时 target repo 的 `.agents/skills`，`verify` 复验该临时安装，最后 `update --yes` 覆盖同一临时 target 上的显式 apply + strict verify 路径。

CI 的 Governance Checks workflow 会显式设置 Node，并运行本地 scaffold smoke、本地 scaffold pack/tarball smoke、根 package pack dry-run、根 package publish dry-run，以及无 `AW_HARNESS_REPO_ROOT` 的根 `.tgz` help / version / TUI non-interactive guard / diagnose / update dry-run / install / verify / update apply smoke。该 CI 覆盖验证 package envelope 和 publish preflight，不代表 npm release channel 已发布；真实 release 还必须通过 release-channel guard。

暂不实现：

- `claude`
- `opencode`

当前边界说明：

- 当前只实现 `agents`
- 主流程固定为：
  - `prune --all`
  - `check_paths_exist`
  - `install --backend agents`
- `diagnose --backend agents --json` 是只读结构化诊断命令，发现问题时仍以 0 退出，用于给 operator 或外层自动化读取当前 deploy 状态
- `verify --backend agents` 是只读辅助命令，不属于安装主线
- 本地 `harness_deploy.py` wrapper、当前 `aw-installer` scaffold、`aw-harness-deploy` 兼容别名和目标 `npx aw-installer` wrapper 必须保持这些语义；包装层合同见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)
- `aw-installer` 的目标形态是 CLI + TUI 双模式：CLI 是脚本化合同，当前 `tui` shell 是同一 deploy 合同上的交互式引导层，guided update flow 先展示 `diagnose` 和 dry-run plan，再要求显式 `yes` 后调用 `update --yes`；它不能绕过只读 `diagnose / verify`、显式三步 reinstall 或 `update --yes` 确认边界
- `update` 是三步 destructive reinstall 的 one-shot 包装；默认只输出 dry-run plan，只有显式传入 `--yes` 才会执行 `prune --all -> check_paths_exist -> install -> verify`
- `update` 只把 planned / known AW target path 上的 unrecognized / foreign 内容作为阻塞项；target root 下无关用户目录不阻止 dry-run 或 apply
- `update` 的 payload provenance 与 trust boundary 见 [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md)；远程更新能力不属于当前实现
- 原始来源（canonical source）、后端部署包（backend payload source）、目标入口（target entry）之间的正式映射规则，见 [Deploy Mapping Spec](./deploy-mapping-spec.md)
- `prune --all` 只删除带可识别、且属于当前 backend 的受管 `aw.marker` 目录；无 marker、不可识别 marker 或 foreign 目录一律不碰
- `check_paths_exist` 会基于当前 source 声明的 live bindings 解析目标路径；只要任一路径已存在，就全量列出冲突并失败退出，不做任何业务写入
- `install --backend agents` 只写当前 source 声明的 live payload；若 source 存在重复 `target_dir` 或目标路径冲突，必须在写入前失败
- `aw.marker` 是 runtime-generated artifact，只表达“这是当前 backend 的受管 live install 目录”
- 不再承接 `retired-target-dir`、`prune --outdated`、archive/history、增量修复、旧版本保活或 “确认新目录可用再删旧目录”
- backend-specific target root 解析与 override 参数见 [Codex Usage Help](../usage-help/codex.md)

## 三、三步主流程

默认主流程固定为：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
```

如果当前 backend 需要显式 root override，例如 `agents` 通过 `--agents-root` 指到非默认 target root，就在这三条命令上附加对应参数。参数来源见 [Codex Usage Help](../usage-help/codex.md)。

如果需要一个包装命令，先查看 dry-run plan，再显式 apply：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py update --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py update --backend agents --yes
```

`update --json` 只输出 dry-run plan，不和 `--yes` 组合使用。

### 1. `prune --all`

- 清理当前 backend 受管的旧安装目录
- 删除条件只有一个：目录里存在可识别、属于当前 backend 的 `aw.marker`
- 没有 marker、marker 不可识别、或明显不是我方受管目录时，脚本不会碰它们
- 这一步是 destructive reinstall 的显式清理阶段，不负责保留历史副本

### 2. `check_paths_exist`

- 基于当前 source 声明的 live bindings，解析即将写入的全部目标路径
- 如果任何目标路径已经存在，命令必须一次性列出全部冲突并非零退出
- 这一步不写任何业务文件，也不替 operator 做“可不可以覆盖”的判断

### 3. `install --backend agents`

- 只写当前 source 声明的 live payload
- 这一步不承接 archive/history、增量修复或旧版本保活
- 如果 source 中出现重复 `target_dir` 或其他 source contract 非法情形，必须在写入前失败
- 如果冲突路径未清理完，也必须在写入前失败

## 四、可选复验

如果需要先拿结构化状态摘要，执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py diagnose --backend agents --json
```

`diagnose` 当前只读输出 backend、target root、受管安装数量、issue 数量、issue code，以及 unrecognized / conflict 摘要。它用于状态观察；即使发现 drift 或 root 问题，也返回 0。

主流程跑完后，如需只读复验，再执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

`verify` 当前只负责：

- source 合法性
- target root 是否存在、是否是目录、是否是坏链路
- live install 与当前 source 的对齐状态
- target root 下的 conflict / unrecognized 情形

## 五、常见恢复路径

- `check_paths_exist` 报出冲突路径：
  - 先由 operator 手工清理这些目录或修正 source
  - 然后从 `prune --all` 重新开始
- `install` 在写入前失败：
  - 先修 source contract，例如重复 `target_dir`
  - 再从 `prune --all` 重新开始
- `verify` 报 drift：
  - 先确认是 source 问题、target root 问题还是 unrecognized / foreign 目录
  - 修正后重新跑三步主流程

## 六、下一步去哪页

- 根目录不一致（drift）、损坏链路、root 类型错误：查看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- skills / `.aw_template` 的增删改查：查看 [skill-lifecycle.md](./skill-lifecycle.md)
- 原始来源、后端部署包、目标入口的正式规则：查看 [Deploy Mapping Spec](./deploy-mapping-spec.md)
- package payload、source/target root 和 update trust boundary：查看 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)
- `claude` / `opencode` 当前暂不在部署接口中实现；Claude skills 分发是慢车道兼容项，恢复前不要将它们写成稳定的 operator 流程
