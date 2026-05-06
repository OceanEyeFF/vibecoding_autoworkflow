---
title: "AutoWorkflow"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
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

`aw-installer` 是当前仓库的分发入口和 CLI bin。根 README 只保留试用入口和文档分流；registry 事实、release channel、package smoke 与 publish 准入以 project-maintenance 文档为准。

```bash
npx aw-installer@next
npx aw-installer@next tui
```

交互式终端中，已批准 package entrypoint 可以进入最小 TUI；CI、脚本或非交互环境应使用显式 CLI：

```bash
npx aw-installer@next --version
npx aw-installer@next diagnose --backend agents --json
npx aw-installer@next verify --backend agents
npx aw-installer@next update --backend agents
npx aw-installer@next update --backend agents --yes
npx aw-installer@next install --backend agents
```

当前 public / near-public 主路径仍是 `agents` backend，也就是 Codex 使用的 `.agents/skills/` payload。推荐从目标仓库根目录先做只读观察，再显式 apply：

```bash
npx aw-installer@next diagnose --backend agents --json
npx aw-installer@next update --backend agents
npx aw-installer@next update --backend agents --yes
npx aw-installer@next verify --backend agents
```

Claude Code 目前是 compatibility lane，使用 `claude` backend 和 `.claude/skills/` payload，不替代 `agents` 主路径。

分发相关入口：

- Codex / `agents` 使用帮助：[`docs/project-maintenance/usage-help/codex.md`](./docs/project-maintenance/usage-help/codex.md)
- Claude 使用帮助：[`docs/project-maintenance/usage-help/claude.md`](./docs/project-maintenance/usage-help/claude.md)
- 通用 deploy 主流程：[`docs/project-maintenance/deploy/deploy-runbook.md`](./docs/project-maintenance/deploy/deploy-runbook.md)
- CLI / TUI 包装层合同：[`docs/project-maintenance/deploy/distribution-entrypoint-contract.md`](./docs/project-maintenance/deploy/distribution-entrypoint-contract.md)
- source / target / trust boundary：[`docs/project-maintenance/deploy/payload-provenance-trust-boundary.md`](./docs/project-maintenance/deploy/payload-provenance-trust-boundary.md)
- npx / `.tgz` smoke：[`docs/project-maintenance/testing/npx-command-test-execution.md`](./docs/project-maintenance/testing/npx-command-test-execution.md)
- release channel 与 publish 准入：[`docs/project-maintenance/governance/aw-installer-release-channel-governance.md`](./docs/project-maintenance/governance/aw-installer-release-channel-governance.md)

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

- `.agents/`、`.claude/` 是 repo-local deploy target
- `.autoworkflow/`、`.spec-workflow/` 是 repo-local state / config
- `.nav/` 只是 compatibility navigation，不是结构定义层

更完整的分层定义见 [`根目录分层`](./docs/project-maintenance/foundations/root-directory-layering.md)。

## 当前仓库如何承接这些目标

### 1. Harness 文档真相

[`docs/harness/`](./docs/harness/README.md) 负责承接 Harness 的 doctrine、scope、artifact、catalog 与 workflow family。

当前已退役 `memory-side`、`task-interface` 和 `docs/harness/adjacent-systems/` 独立文档域。已批准输入会被收束进 Harness artifact，尤其是 [`Worktrack Contract`](./docs/harness/artifact/worktrack/contract.md) 与 [`Plan / Task Queue`](./docs/harness/artifact/worktrack/plan-task-queue.md)。

### 2. Harness 可执行源码

[`product/harness/`](./product/harness/README.md) 负责承接 canonical skills 与 adapters。这里是可执行实现层，不承接 ontology 正文。

### 3. 项目维护与治理

[`docs/project-maintenance/`](./docs/project-maintenance/README.md) 负责 repo-local 维护、治理、deploy、testing 和 usage help。阅读路由由 [`AGENTS.md`](./AGENTS.md) 承接；writeback 和 review/verify 由 [`review-verify-handbook.md`](./docs/project-maintenance/governance/review-verify-handbook.md) 承接。

## 典型工作链路

这个仓库当前最值得把握的不是某个单独 skill，而是整条链路：

```text
目标 / 需求
  ↓
Worktrack Contract
  ↓
Plan / Task Queue
  ↓
AI 执行
  ↓
Review / Verify / Writeback
  ↓
验证与回灌
```

含义是：

- 先把已批准输入收束成正式工作追踪边界
- 再把工作追踪约定展开成可调度队列
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
   - Harness 主线与 artifact 合同：[`docs/harness/README.md`](./docs/harness/README.md)
   - 业务源码：[`product/README.md`](./product/README.md)
   - 工具层：[`toolchain/README.md`](./toolchain/README.md)

首次进入仓库时，通常这样选：

- 想快速按任务定位入口：看 [`INDEX.md`](./INDEX.md)
- 想理解文档真相层：看 [`docs/README.md`](./docs/README.md)
- 想理解 `Harness 平台` 的承接结构：看 [`product/README.md`](./product/README.md)
- 想理解执行前边界：看 [`Worktrack Contract`](./docs/harness/artifact/worktrack/contract.md)
- 想理解任务队列：看 [`Plan / Task Queue`](./docs/harness/artifact/worktrack/plan-task-queue.md)
- 想部署或跑治理检查：看 [`toolchain/README.md`](./toolchain/README.md)
- 想看 repo-local 使用帮助：看 [`docs/project-maintenance/usage-help/README.md`](./docs/project-maintenance/usage-help/README.md)

## 非目标

- 不是某个单独 agent 的完整 runtime
- 不是某家模型私有的 prompt 仓库
- 不是只服务当前仓库的一次性脚手架
- 不是把 deploy target 当成 source of truth
- 不是让首页充当完整操作手册

## 当前提醒

- `.agents/`、`.claude/` 只是 deploy target，不是源码层或真相层
- `.autoworkflow/`、`.spec-workflow/` 只是 repo-local state / config，不是默认阅读主线
- `.nav/` 只是 compatibility navigation，不是结构定义层
- 某个后端的 prompt / wrapper 不能替代跨后端共享 truth

## 许可证

- 当前仓库采用 MIT License。
- 正式授权文本以根目录 [`LICENSE`](./LICENSE) 文件为准。
- 当前仓库的授权边界只看正式许可证文件，不依赖 README 文案。
