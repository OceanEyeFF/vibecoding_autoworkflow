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

`aw-installer` 是已批准的 unscoped npm package identity，也是当前仓库内分发入口和 CLI bin。`aw-installer@0.4.0-rc.1` 已发布为 npm registry RC；当前 registry 的 `next` 和 `latest` 都指向这个唯一 RC 版本。当前 checkout 已准备 `0.4.0-rc.2` 候选修复，包含 Windows/Unix Python launcher fallback 和最新 19 个 agents skills；在 `rc.2` 发布前，论坛外部试用不要把 registry `0.4.0-rc.1` 当作最终候选。复制粘贴入口见 [`aw-installer Public Quickstart Prompts`](./docs/project-maintenance/deploy/aw-installer-public-quickstart-prompts.md)，rc2 安装就绪与发布边界见 [`aw-installer RC2 npx Install Readiness`](./docs/project-maintenance/deploy/aw-installer-rc2-npx-install-readiness.md) 和 [`aw-installer RC2 Approval Package`](./docs/project-maintenance/deploy/aw-installer-rc2-approval-package.md)。

```bash
npx aw-installer
npx aw-installer tui
```

交互式终端中，已批准 package entrypoint 可以进入最小 TUI；CI、脚本或非交互环境应使用显式 CLI：

```bash
npx aw-installer --version
npx aw-installer diagnose --backend agents --json
npx aw-installer verify --backend agents
npx aw-installer update --backend agents
npx aw-installer update --backend agents --yes
npx aw-installer install --backend agents
```

这里的裸 `npx aw-installer` 解析到当前唯一 registry RC；这不是稳定 release 批准，稳定版本和未来 publish 仍需单独审批。`diagnose` 和 `verify` 是只读检查；`install` 是显式写入当前 payload 的底层命令；`update` 默认只输出 dry-run plan。推荐写入路径是在确认 plan 后运行 `update --yes`，它会按 `prune --all -> check_paths_exist -> install -> verify` 写入目标仓库的 `.agents/skills`。完整入口合同见 [`Distribution Entrypoint Contract`](./docs/project-maintenance/deploy/distribution-entrypoint-contract.md)，registry npx smoke 与反馈日志见 [`aw-installer Registry npx Smoke`](./docs/project-maintenance/deploy/aw-installer-registry-npx-smoke.md)。

`aw-installer` 的 Node wrapper 需要目标机器可启动 Python。当前 checkout 的 `rc.2` 候选在 Windows 上按 `py -3`、`python`、`python3` 尝试，在 Linux/macOS 上按 `python3`、`python` 尝试；不依赖 `PYTHON` 或 `PYTHON3` 环境变量覆盖。registry `0.4.0-rc.1` 仍只硬编码 `python3`，因此 Windows PowerShell 论坛试用应等待 `rc.2` 发布。

`aw-installer` 当前只使用 package 或 checkout 中的 source payload；`update` 不做远程 fetch、channel 解析、自升级、验签或自动回滚。payload provenance 与 update trust boundary 见 [`Payload Provenance And Update Trust Boundary`](./docs/project-maintenance/deploy/payload-provenance-trust-boundary.md)。

### 外部试用路径：目标仓库里运行

当前 RC 最短路径是在目标项目根目录运行裸 `npx aw-installer`：

```bash
npx aw-installer diagnose --backend agents --json
npx aw-installer update --backend agents
npx aw-installer update --backend agents --yes
npx aw-installer verify --backend agents
```

需要显式锁定 RC channel 时，用 `npx aw-installer@next ...`；维护者验证当前 checkout 时仍可使用本地 `.tgz` 或明确 checkout source。完整复制粘贴流程见 [`aw-installer Public Quickstart Prompts`](./docs/project-maintenance/deploy/aw-installer-public-quickstart-prompts.md)。

### 干净目录初始化

如果目标目录是一个新仓库或空工作目录，推荐先建立 git worktree，再从该目录运行 installer：

```bash
mkdir target-project
cd target-project
git init

npx aw-installer diagnose --backend agents --json
npx aw-installer update --backend agents
npx aw-installer update --backend agents --yes
npx aw-installer verify --backend agents
```

这一步只安装 AW skill payload 到目标项目的 `.agents/skills/`。之后在 Codex 中运行 `$set-harness-goal-skill`，再创建 `.aw/` 控制面；不要把 `.aw/` 初始化和 skill payload 安装混成同一个隐式写入步骤。

### 已有工作内容的目录初始化

如果目标仓库已经有代码、文档或进行中的工作，先用只读命令看计划，再由目标 owner 批准写入：

```bash
npx aw-installer diagnose --backend agents --json
npx aw-installer update --backend agents
```

确认 dry-run 只会写入目标仓库的 `.agents/skills/aw-*` 受管目录后，再运行：

```bash
npx aw-installer update --backend agents --yes
npx aw-installer verify --backend agents
```

随后让 Codex 初始化 `.aw/` 时，应要求它保留现有源码和文档，把已有仓库事实当作 discovery input，而不是覆盖已确认的项目真相。若目标仓库已经有 `.aw/`，必须先检查现有 control state；未经 operator 确认，不要覆盖 `.aw/goal-charter.md`。

外部试用反馈请走 [`aw-installer External Trial Feedback Contract`](./docs/project-maintenance/deploy/aw-installer-external-trial-feedback.md)、[`trial feedback issue template`](./.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 或 [`bug/blocker issue template`](./.github/ISSUE_TEMPLATE/aw-installer-bug.yml)；registry npx smoke 会生成每个目标的 `aw-installer-npx-run.log`，使用方式见 [`aw-installer Registry npx Smoke`](./docs/project-maintenance/deploy/aw-installer-registry-npx-smoke.md)。本地 `.tgz` 多临时目录 smoke 路径见 [`aw-installer Multi Temporary Workdir Smoke`](./docs/project-maintenance/deploy/aw-installer-multi-temp-workdir-smoke.md)。

也可以从当前 checkout 打一个本地 `.tgz`，再在目标项目根目录用同一 package 入口试跑：

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
