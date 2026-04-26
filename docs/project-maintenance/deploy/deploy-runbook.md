---
title: "Deploy Runbook"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
---
# Deploy Runbook

> 目的：提供当前仓库的 deploy 快速上手指南，固定 destructive reinstall model：`prune --all -> check_paths_exist -> install --backend agents`。`diagnose` 与 `verify` 只保留为辅助、只读的诊断与复验命令。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先了解以下背景：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [Deploy Mapping Spec](./deploy-mapping-spec.md) —— 部署映射规范

本页只保留快速入门和主流程。维护诊断请查看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)，业务生命周期边界请查看 [skill-lifecycle.md](./skill-lifecycle.md)。

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

`harness_deploy.py` 不表示 package / npx 发布渠道已经实现；它只包装当前 `adapter_deploy.py` 命令面。

本地 npm-style scaffold 可用下面的 smoke 命令验证 bin 入口能打开同一 help surface：

```bash
npm --prefix toolchain/scripts/deploy run smoke --silent
```

如果要检查 package packlist，进入 package root 后运行 dry-run：

```bash
cd toolchain/scripts/deploy
npm pack --dry-run --json
```

该 dry-run 不应在仓库中留下 `.tgz` package artifact。

更接近真实分发路径的 smoke 应把 package 打到临时目录，再从 `.tgz` 执行 bin：

```bash
cd toolchain/scripts/deploy
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
package_file="$(node -e "const fs = require('node:fs'); const payload = JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); console.log(payload[0].filename);" "$tmpdir/pack.json")"
npm exec --yes --package "$tmpdir/$package_file" -- aw-harness-deploy --help
AW_HARNESS_REPO_ROOT="$(pwd)/../../.." npm exec --yes --package "$tmpdir/$package_file" -- aw-harness-deploy diagnose --backend agents --json
```

`AW_HARNESS_REPO_ROOT` 是 packaged wrapper 的 source checkout override。没有该 override 时，打包后的脚本会从 npm package 解压路径解析 source root，因此只能可靠验证 help surface。

CI 的 Governance Checks workflow 会显式设置 Node，并运行本地 package smoke、pack dry-run 和带 `AW_HARNESS_REPO_ROOT` 的 tarball smoke。该 CI 覆盖仍只验证 repo-local scaffold，不代表 package 已发布。

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
- 本地 `harness_deploy.py` wrapper 和未来 reusable package / npx-style wrapper 必须保持这些语义；包装层合同见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)
- `update` 当前不是可用命令；未来若实现，只能作为同一三步 destructive reinstall 的 one-shot 包装，并必须先满足 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 的准入条件
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
- `claude` / `opencode` 当前暂不在部署接口中实现；恢复前不要将它们写成稳定的 operator 流程
