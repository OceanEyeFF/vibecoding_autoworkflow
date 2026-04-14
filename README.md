---
title: "AutoWorkflow"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# AutoWorkflow

> 本项目的核心目标，是构建一个 `Codex-first` 的 AI coding harness 平台，并将其分发到多个项目中使用；同时建设一个面向 skills 的 `autoresearch` 系统，用于持续评测、改进和回灌这些能力。

## 项目目标

这个项目主要做三件事：

1. `Harness 平台搭建`
   构建一个 `Codex-first` 的 AI coding harness，统一任务收束、上下文路由、执行、验证和回写。
2. `Harness 分发`
   把这套 harness 作为可复用能力分发到包括本项目在内的多个仓库。
3. `Autoresearch`
   对 skills 做持续评测、改进和回灌。

## 我们在构建什么

从产品视角看，这不是一个只服务单仓库的脚手架，而是一套可以持续复用和迭代的能力系统：

- 一套统一的任务进入和收束方式
- 一套统一的上下文路由与执行边界
- 一套可分发到多个仓库的 harness 形态
- 一套围绕 skills 的评测、改进和回灌闭环

`repo-side contract layer` 可以保留为当前实现形态的描述，但它不是项目第一句，也不是目标本身。

## 仓库定位

当前仓库主线仍然只认三块正式内容区：

- [`product/`](./product/README.md)：业务代码唯一源码根
- [`docs/`](./docs/README.md)：文档真相、能力合同与治理规则
- [`toolchain/`](./toolchain/README.md)：部署、治理检查、测试与 research 工具

这三块之外：

- `.agents/`、`.claude/`、`.opencode/` 是 repo-local deploy target
- `.autoworkflow/`、`.spec-workflow/`、`.serena/` 是 repo-local state / config
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

对应源码入口：

- [`product/memory-side/`](./product/memory-side/README.md)

### 2. Task Interface

负责把讨论压缩成一份正式执行基线，核心对象是 `Task Contract`。

对应合同入口：

- [`docs/harness/adjacent-systems/task-interface/task-contract.md`](./docs/harness/adjacent-systems/task-interface/task-contract.md)

对应源码入口：

- [`product/task-interface/`](./product/task-interface/README.md)

### 3. Harness Operations

负责承接执行壳层和 workflow 级能力，例如 task planning、review loop、strict/simple workflow、execution contract 等。

对应源码入口：

- [`product/harness-operations/`](./product/harness-operations/README.md)

### 4. Autoresearch

负责对 skills 做持续评测、比较、改进和回灌，把已验证结果重新带回 canonical skills、adapters 和文档。

对应入口：

- [`docs/autoresearch/`](./docs/autoresearch/README.md)
- [`toolchain/`](./toolchain/README.md)

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
  ↓
Autoresearch 评测与改进
```

含义是：

- 先把讨论收束成正式边界
- 再限制 AI 的阅读入口
- 执行完成后只把已验证结果写回真相层
- 最后把可验证的改进回流到 skills 的评测和分发链路里
- backend-specific prompt 和 deploy wrapper 不能反过来定义主线真相

## 根级入口怎么分工

`README.md` 负责讲清楚项目目标、当前承接结构和主线入口。
`INDEX.md` 负责按任务目标把人或 agent 导向正确入口。
`GUIDE.md` / `ROADMAP.md` 只是兼容入口，不单独定义主线。
`AGENTS.md` 是 agent-facing 的最小工作规则入口；若冲突，以 `docs/project-maintenance/`、`docs/harness/` 与 `docs/autoresearch/` 为准。

## 从哪里进入

1. [`docs/README.md`](./docs/README.md)
2. [`docs/project-maintenance/README.md`](./docs/project-maintenance/README.md)
3. [`docs/project-maintenance/foundations/root-directory-layering.md`](./docs/project-maintenance/foundations/root-directory-layering.md)
4. [`AGENTS.md`](./AGENTS.md)
5. 按任务进入：
   - Harness 主线与 adjacent-system 合同：[`docs/harness/README.md`](./docs/harness/README.md)
   - 业务源码：[`product/README.md`](./product/README.md)
   - 工具层：[`toolchain/README.md`](./toolchain/README.md)
   - `autoresearch` 文档：[`docs/autoresearch/README.md`](./docs/autoresearch/README.md)

首次进入仓库时，通常这样选：

- 想快速按任务定位入口：看 [`INDEX.md`](./INDEX.md)
- 想理解文档真相层：看 [`docs/README.md`](./docs/README.md)
- 想理解 `Harness 平台` 的承接结构：看 [`product/README.md`](./product/README.md)
- 想理解 `Task Contract`：看 [`docs/harness/adjacent-systems/task-interface/task-contract.md`](./docs/harness/adjacent-systems/task-interface/task-contract.md)
- 想理解 `Memory Side`：看 [`docs/harness/adjacent-systems/memory-side/README.md`](./docs/harness/adjacent-systems/memory-side/README.md)
- 想看 `Autoresearch`：看 [`docs/autoresearch/README.md`](./docs/autoresearch/README.md)
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
- `.autoworkflow/`、`.spec-workflow/`、`.serena/` 只是 repo-local state / config，不是默认阅读主线
- `.nav/` 只是 compatibility navigation，不是结构定义层
- 某个后端的 prompt / wrapper 不能替代跨后端共享 truth

## 许可证

- 当前仓库采用 MIT License。
- 正式授权文本以根目录 [`LICENSE`](./LICENSE) 文件为准。
- 当前仓库的授权边界只看正式许可证文件，不依赖 README 文案。
