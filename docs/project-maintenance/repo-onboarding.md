---
title: "Repository Onboarding"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---

# Repository Onboarding

> 本页面向需要理解此仓库内部结构和运行方式的维护者。如果你是外部试用者，先看 [README.md](../../README.md)。

## 仓库定位

本项目的核心目标是构建一个 Codex-first 的 AI coding harness 平台，并将其作为 repo-side contract layer 分发到多个项目中使用。

从产品视角看，这不是一个只服务单仓库的脚手架，而是一套可以持续复用和迭代的能力系统：

- 一套统一的任务进入和收束方式
- 一套统一的上下文路由与执行边界
- 一套可分发到多个仓库的 harness 形态

## 目录分层

| 目录 | 性质 |
|------|------|
| `docs/` | 真相层：project-maintenance / harness / analysis / ideas / archive |
| `product/` | 业务代码唯一源码根：harness skills + adapters |
| `toolchain/` | 脚本、评测、测试、打包、部署工具 |
| `.aw/` | runtime control-plane state（非长期真相层） |
| `.agents/` `.claude/` | deploy target（非源码层） |
| `.autoworkflow/` `.spec-workflow/` | repo-local state layer |
| `.nav/` | compatibility navigation layer（非真实结构定义） |

### 核心定位

- `docs/`：文档真相、能力合同与治理规则
- `product/`：业务代码唯一源码根
- `toolchain/`：部署、治理检查、测试与 research 工具

这三块之外：

- `.agents/`、`.claude/` 是 repo-local deploy target
- `.autoworkflow/`、`.spec-workflow/` 是 repo-local state / config
- `.nav/` 只是 compatibility navigation，不是结构定义层

更完整的分层定义见 [`根目录分层`](./foundations/root-directory-layering.md)。

## 入口分工

| 文件 | 职责 |
|------|------|
| `README.md` | 对外使用入口：skills 使用说明、安装方法、快速试用路径 |
| `INDEX.md` | 按任务目标将人或 agent 导向正确入口 |
| `AGENTS.md` | agent-facing 最小工作规则入口；若冲突，以 docs/project-maintenance/ + docs/harness/ 为准 |

## 典型工作链路

这个仓库核心的整条链路：

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

## 从哪里进入

1. [`docs/README.md`](../README.md)
2. [`docs/project-maintenance/README.md`](README.md)
3. [`docs/project-maintenance/foundations/root-directory-layering.md`](foundations/root-directory-layering.md)
4. [`AGENTS.md`](../../AGENTS.md)
5. 按任务进入：
   - Harness 主线与 artifact 合同：[`docs/harness/README.md`](../harness/README.md)
   - 业务源码：[`product/README.md`](../../product/README.md)
   - 工具层：[`toolchain/README.md`](../../toolchain/README.md)

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
