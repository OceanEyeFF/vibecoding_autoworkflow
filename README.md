---
title: "AutoWorkflow"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# AutoWorkflow

> 本项目的核心目标，是构建一个 `Codex-first` 的 AI coding harness 平台，并将其作为 repo-side contract layer 分发到多个项目中使用。

## 项目目标

这个项目主要做两件事：

1. `Harness 平台搭建`
   构建一个 `Codex-first` 的 AI coding harness，统一任务收束、上下文路由、执行、验证和回写。
2. `Harness 分发`
   把这套 harness 作为可复用能力分发到包括本项目在内的多个仓库。

## 使用 `aw-installer`

`aw-installer` 是当前仓库内分发入口、CLI bin 和文档中的工作名，不表示最终 npm 包名已经确认。npm release channel 尚未发布；当前仓库已经验证 root package envelope、tarball smoke 和 publish dry-run。外部试用的复制粘贴入口见 [`aw-installer Public Quickstart Prompts`](./docs/project-maintenance/deploy/aw-installer-public-quickstart-prompts.md)。最终包名确认并完成发布后，使用者应在目标项目根目录通过已批准的 package entrypoint 运行同等命令语义：

```bash
npx <approved-package>
npx <approved-package> tui
```

交互式终端中，已批准 package entrypoint 可以进入最小 TUI；CI、脚本或非交互环境应使用显式 CLI：

```bash
npx <approved-package> --version
npx <approved-package> diagnose --backend agents --json
npx <approved-package> verify --backend agents
npx <approved-package> update --backend agents
npx <approved-package> update --backend agents --yes
npx <approved-package> install --backend agents
```

这里的 `<approved-package>` 是未来确认后的 npm package entrypoint；当前不能把它替换成公开可用的 `aw-installer` npm 包。`diagnose` 和 `verify` 是只读检查；`install` 是显式写入当前 payload 的底层命令；`update` 默认只输出 dry-run plan。推荐写入路径是在确认 plan 后运行 `update --yes`，它会按 `prune --all -> check_paths_exist -> install -> verify` 写入目标仓库的 `.agents/skills`。完整入口合同见 [`Distribution Entrypoint Contract`](./docs/project-maintenance/deploy/distribution-entrypoint-contract.md)，维护者验证与本地 tarball smoke 见 [`Deploy Runbook`](./docs/project-maintenance/deploy/deploy-runbook.md)。

`aw-installer` 当前只使用 package 或 checkout 中的 source payload；`update` 不做远程 fetch、channel 解析、自升级、验签或自动回滚。payload provenance 与 update trust boundary 见 [`Payload Provenance And Update Trust Boundary`](./docs/project-maintenance/deploy/payload-provenance-trust-boundary.md)。

在 npm release channel 发布前，可以从当前 checkout 打一个本地 `.tgz`，再在目标项目根目录用同一 package 入口试跑：

```bash
tmpdir="$(mktemp -d)"
npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
package_file="$(node -e "const fs = require('node:fs'); const payload = JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); console.log(payload[0].filename);" "$tmpdir/pack.json")"

cd /path/to/target-project
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer diagnose --backend agents --json
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer update --backend agents
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$tmpdir/$package_file" -- aw-installer update --backend agents --yes
```

这条 pre-release 试用路径显式清空 `AW_HARNESS_REPO_ROOT` 与 `AW_HARNESS_TARGET_REPO_ROOT`，因此会从 `.tgz` 包内读取 source payload，并把命令运行时所在的目标项目作为 target repo；写入只发生在该目标项目的 `.agents/skills` 下。如果显式设置这些 override，则以 override 指向的 source/target 边界为准。

## 我们在构建什么

从产品视角看，这不是一个只服务单仓库的脚手架，而是一套可以持续复用和迭代的能力系统：

- 一套统一的任务进入和收束方式
- 一套统一的上下文路由与执行边界
- 一套可分发到多个仓库的 harness 形态

`repo-side contract layer` 可以保留为当前实现形态的描述，但它不是项目第一句，也不是目标本身。

## 仓库定位

当前仓库主线仍然只认三块正式内容区：

- [`product/`](./product/README.md)：业务代码唯一源码根
- [`docs/`](./docs/README.md)：文档真相、能力合同与治理规则
- [`toolchain/`](./toolchain/README.md)：部署、治理检查、测试与 research 工具

这三块之外：

- `.agents/`、`.claude/`、`.opencode/` 是 repo-local deploy target
- `.autoworkflow/`、`.spec-workflow/` 是 repo-local state / config
- `.nav/` 只是 compatibility navigation，不是结构定义层

更完整的分层定义见 [`根目录分层`](./docs/project-maintenance/foundations/root-directory-layering.md)。

## 当前仓库如何承接这些目标

### 1. Memory Side

负责项目长期记忆和任务上下文治理，支撑任务收束前后的信息边界管理。当前固定为三个组件：

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

对应合同入口：

- [`docs/harness/adjacent-systems/memory-side/overview.md`](./docs/harness/adjacent-systems/memory-side/overview.md)
- [`docs/harness/adjacent-systems/memory-side/skill-agent-model.md`](./docs/harness/adjacent-systems/memory-side/skill-agent-model.md)

当前仓库状态：

- `Memory Side` 目前只保留在 `docs/harness/adjacent-systems/memory-side/` 的合同层
- repo 内不再保留独立的 `product/memory-side/` 源码树

### 2. Task Interface

负责把讨论压缩成一份正式执行基线，核心对象是 `Task Contract`。

对应合同入口：

- [`docs/harness/adjacent-systems/task-interface/task-contract.md`](./docs/harness/adjacent-systems/task-interface/task-contract.md)

当前仓库状态：

- `Task Interface` 目前只保留在 `docs/harness/adjacent-systems/task-interface/` 的合同层
- repo 内不再保留独立的 `product/task-interface/` 源码树

### 3. Harness Doctrine

负责承接 Harness 的 doctrine、scope、artifact、workflow family 与 adjacent-system 定义。

对应文档入口：

- [`docs/harness/`](./docs/harness/README.md)

当前这部分以文档真相层为主，不再对应仓库内单独的 harness skill/source 分区。

## 典型工作链路

这个仓库当前最值得把握的不是某个单独 skill，而是整条链路：

```text
目标 / 需求
  ↓
Task Contract
  ↓
Context Routing
  ↓
AI 执行
  ↓
Writeback & Cleanup
  ↓
验证与回灌
```

含义是：

- 先把讨论收束成正式边界
- 再限制 AI 的阅读入口
- 执行完成后只把已验证结果写回真相层
- backend-specific prompt 和 deploy wrapper 不能反过来定义主线真相

## 根级入口怎么分工

`README.md` 负责讲清楚项目目标、当前承接结构和主线入口。
`INDEX.md` 负责按任务目标把人或 agent 导向正确入口。
`GUIDE.md` / `ROADMAP.md` 只是兼容入口，不单独定义主线。
`AGENTS.md` 是 agent-facing 的最小工作规则入口；若冲突，以 `docs/project-maintenance/` 与 `docs/harness/` 为准。

## 从哪里进入

1. [`docs/README.md`](./docs/README.md)
2. [`docs/project-maintenance/README.md`](./docs/project-maintenance/README.md)
3. [`docs/project-maintenance/foundations/root-directory-layering.md`](./docs/project-maintenance/foundations/root-directory-layering.md)
4. [`AGENTS.md`](./AGENTS.md)
5. 按任务进入：
   - Harness 主线与 adjacent-system 合同：[`docs/harness/README.md`](./docs/harness/README.md)
   - 业务源码：[`product/README.md`](./product/README.md)
   - 工具层：[`toolchain/README.md`](./toolchain/README.md)

首次进入仓库时，通常这样选：

- 想快速按任务定位入口：看 [`INDEX.md`](./INDEX.md)
- 想理解文档真相层：看 [`docs/README.md`](./docs/README.md)
- 想理解 `Harness 平台` 的承接结构：看 [`product/README.md`](./product/README.md)
- 想理解 `Task Contract`：看 [`docs/harness/adjacent-systems/task-interface/task-contract.md`](./docs/harness/adjacent-systems/task-interface/task-contract.md)
- 想理解 `Memory Side`：看 [`docs/harness/adjacent-systems/memory-side/README.md`](./docs/harness/adjacent-systems/memory-side/README.md)
- 想部署或跑治理检查：看 [`toolchain/README.md`](./toolchain/README.md)
- 想看 repo-local 使用帮助：看 [`docs/project-maintenance/usage-help/README.md`](./docs/project-maintenance/usage-help/README.md)

## 非目标

- 不是某个单独 agent 的完整 runtime
- 不是某家模型私有的 prompt 仓库
- 不是只服务当前仓库的一次性脚手架
- 不是把 deploy target 当成 source of truth
- 不是让首页充当完整操作手册

## 当前提醒

- `.agents/`、`.claude/`、`.opencode/` 只是 deploy target，不是源码层或真相层
- `.autoworkflow/`、`.spec-workflow/` 只是 repo-local state / config，不是默认阅读主线
- `.nav/` 只是 compatibility navigation，不是结构定义层
- 某个后端的 prompt / wrapper 不能替代跨后端共享 truth

## 许可证

- 当前仓库采用 MIT License。
- 正式授权文本以根目录 [`LICENSE`](./LICENSE) 文件为准。
- 当前仓库的授权边界只看正式许可证文件，不依赖 README 文案。
