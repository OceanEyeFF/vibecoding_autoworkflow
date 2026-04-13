---
title: "AutoWorkflow"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# AutoWorkflow

> 本项目是一个 AI coding 的 repo-side contract layer。它不负责把某个 agent 做成完整 runtime，而是把 AI 在仓库里如何读取真相、收束任务、执行、回写和部署这套规则固定下来。

## 它在解决什么问题

当多个 AI 后端共同进入同一个仓库时，最容易失控的不是“能不能生成代码”，而是：

- 谁维护项目真相
- 任务开始前应该读哪些内容
- 讨论怎样收束成可执行基线
- 任务结束后哪些结果必须回写
- backend-specific prompt / wrapper / deploy target 会不会反过来污染源码和文档主线

这个仓库的职责，就是把这些问题做成一套可维护、可部署、可验证的 repo-side contract。

## 仓库定位

仓库主线只认三块正式内容区：

- [`product/`](./product/README.md)：业务代码唯一源码根
- [`docs/`](./docs/README.md)：文档真相、能力合同与治理规则
- [`toolchain/`](./toolchain/README.md)：部署、治理检查、测试与 research 工具

这三块之外：

- `.agents/`、`.claude/`、`.opencode/` 是 repo-local deploy target
- `.autoworkflow/`、`.spec-workflow/`、`.serena/` 是 repo-local state / config
- `.nav/` 只是 compatibility navigation，不是结构定义层

更完整的分层定义见 [`根目录分层`](./docs/project-maintenance/foundations/root-directory-layering.md)。

## 三条产品主线

### 1. Memory Side

负责项目长期记忆和任务上下文治理，当前固定为三个组件：

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

对应合同入口：

- [`docs/deployable-skills/memory-side/overview.md`](./docs/deployable-skills/memory-side/overview.md)
- [`docs/deployable-skills/memory-side/skill-agent-model.md`](./docs/deployable-skills/memory-side/skill-agent-model.md)

对应源码入口：

- [`product/memory-side/`](./product/memory-side/README.md)

### 2. Task Interface

负责把讨论压缩成一份正式执行基线，核心对象是 `Task Contract`。

对应合同入口：

- [`docs/deployable-skills/task-interface/task-contract.md`](./docs/deployable-skills/task-interface/task-contract.md)

对应源码入口：

- [`product/task-interface/`](./product/task-interface/README.md)

### 3. Harness Operations

负责执行壳层和 workflow 级能力，例如 task planning、review loop、strict/simple workflow、execution contract 等。

对应源码入口：

- [`product/harness-operations/`](./product/harness-operations/README.md)

## 典型工作链路

这个仓库当前最值得把握的不是某个单独 skill，而是整条链路：

```text
用户讨论
  ↓
Task Contract
  ↓
Context Routing
  ↓
AI 执行
  ↓
Writeback & Cleanup
  ↓
仓库知识真相更新
```

含义是：

- 先把讨论收束成正式边界
- 再限制 AI 的阅读入口
- 执行完成后只把已验证结果写回真相层
- backend-specific prompt 和 deploy wrapper 不能反过来定义主线真相

## 根级入口怎么分工

| 文件 | 职责 |
|------|------|
| [`README.md`](./README.md) | 根级 landing page，先回答“这是什么仓库、主线在哪、核心链路是什么” |
| [`INDEX.md`](./INDEX.md) | quick index，按任务目标把人或 agent 导向正确入口 |
| [`GUIDE.md`](./GUIDE.md) / [`ROADMAP.md`](./ROADMAP.md) | 兼容入口，不单独定义主线 |
| [`AGENTS.md`](./AGENTS.md) | agent-facing 最小工作规则入口；若冲突，以 `docs/project-maintenance/`、`docs/deployable-skills/` 与 `docs/autoresearch/` 为准 |

## 默认阅读路径

1. [`docs/README.md`](./docs/README.md)
2. [`docs/project-maintenance/README.md`](./docs/project-maintenance/README.md)
3. [`docs/project-maintenance/foundations/root-directory-layering.md`](./docs/project-maintenance/foundations/root-directory-layering.md)
4. [`AGENTS.md`](./AGENTS.md)
5. 按任务进入：
   - 能力合同：[`docs/deployable-skills/README.md`](./docs/deployable-skills/README.md)
   - 业务源码：[`product/README.md`](./product/README.md)
   - 工具层：[`toolchain/README.md`](./toolchain/README.md)
   - `autoresearch` 文档：[`docs/autoresearch/README.md`](./docs/autoresearch/README.md)

## 首次进入仓库时怎么选入口

- 想快速按任务定位入口：看 [`INDEX.md`](./INDEX.md)
- 想理解文档真相层：看 [`docs/README.md`](./docs/README.md)
- 想理解 `Memory Side`：看 [`docs/deployable-skills/memory-side/overview.md`](./docs/deployable-skills/memory-side/overview.md)
- 想理解 `Task Contract`：看 [`docs/deployable-skills/task-interface/task-contract.md`](./docs/deployable-skills/task-interface/task-contract.md)
- 想改 canonical skills / adapters：看 [`product/README.md`](./product/README.md)
- 想部署或跑治理检查：看 [`toolchain/README.md`](./toolchain/README.md)
- 想看 repo-local 使用帮助：看 [`docs/project-maintenance/usage-help/README.md`](./docs/project-maintenance/usage-help/README.md)

## 当前提醒

- 不要把 `.agents/`、`.claude/`、`.opencode/` 当成源码层或真相层
- 不要把 `.autoworkflow/`、`.spec-workflow/`、`.serena/` 当成默认阅读主线
- 不要把 `.nav/` 当成结构定义层
- 不要把某个后端的 prompt / wrapper 当成跨后端共享 truth

## 许可证

- 当前仓库采用 MIT License。
- 正式授权文本以根目录 [`LICENSE`](./LICENSE) 文件为准。
- 当前仓库的授权边界只看正式许可证文件，不依赖 README 文案。
