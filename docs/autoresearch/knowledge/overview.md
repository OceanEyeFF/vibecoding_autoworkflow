---
title: "Autoresearch 模块总览"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Autoresearch 模块总览

> 目的：把当前仓库里的 `autoresearch` 作为项目核心目标之一对应的模块总览入口来收束，说明它是什么、边界在哪、不同层分别承接什么，同时保留 `docs/autoresearch / docs/project-maintenance / toolchain / .autoworkflow` 的稳定分流。

## 一、模块定位

`autoresearch` 是当前仓库中的一个 repo module，也是项目核心目标之一的知识与研究承接入口。

它不是：

- 新的 foundations partition
- 新的 Memory Side / Task Interface 组件
- 宿主工作流系统或通用 agent orchestration 平台

它是：

- 一套围绕 `toolchain/scripts/research/` 组织起来的 contract-driven research loop
- 当前仓库里承接 `Autoresearch` 目标闭环的研究模块入口
- 一个需要跨 `docs/autoresearch`、`docs/project-maintenance`、`toolchain/` 和 `.autoworkflow/` 共同描述，但必须由稳定入口统一分流的模块

## 二、模块边界

`autoresearch` 当前只拥有下面这些主线语义：

- run contract、scoreboard、round 生命周期与 authority 边界
- mutation registry、worker contract、selector、feedback distill 的最小实现合同
- repo-local 运行说明、closeout 规则和维护帮助
- 当前阶段的研究合同与 closeout 跟踪

`autoresearch` 当前不拥有：

- Memory Side 的通用合同
- Task Interface 的通用合同
- `.autoworkflow/` 中运行态文件的真相地位
- `.agents/`、`.claude/`、`.opencode/` 这类 deploy target 的结构定义权

## 三、跨层承接规则

### 1. `docs/autoresearch/knowledge/`

职责：

- 提供 `autoresearch` 的稳定知识入口
- 说明模块边界、阅读顺序和跨层映射
- 固定哪些对象属于主线入口，哪些只是实现、runbook、研究或运行态

不负责：

- 复制 CLI 用法
- 复制阶段性分析全文
- 复制 `toolchain/` 源码合同

### 2. `docs/autoresearch/`

这里承接 `autoresearch` 模块自己的 references 与 runbooks，例如：

- [Autoresearch 最小闭环运行说明](../runbooks/autoresearch-minimal-loop.md)
- [Research CLI 帮助](../references/research-cli-help.md)
- [TMP Exrepo 维护说明](../runbooks/tmp-exrepo-maintenance.md)
- [Research Eval Contracts](../references/research-eval-contracts.md)
- [Research Eval Observability](../references/research-eval-observability.md)

这些文档回答的是“这个模块怎么跑、怎么维护、当前 CLI/contract/output 怎么看”，不是模块实现真相本体。

### 3. `docs/project-maintenance/`

这里承接 repo-local workflow、deploy、governance 与 backend usage，不承接 `autoresearch` 模块专属正文。

### 4. `toolchain/`

这里承接实现与测量资产，当前核心入口包括：

- [toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)
- [toolchain/evals/fixtures/README.md](../../../toolchain/evals/fixtures/README.md)

`toolchain/scripts/research/` 是当前 `autoresearch` 实现面的 source of truth；
`docs/autoresearch/knowledge/` 只负责模块知识入口，不替代实现文档，也不扩写实现细节。

### 5. `.autoworkflow/`

这里承接运行产物和 run-local state。

限制：

- 它可以被读取用于核对 runtime 状态或 retained artifact
- 它不是默认阅读入口
- 它不是长期知识真相层

## 四、推荐阅读路径

### 1. 理解模块边界时

1. 先读本页。
2. 如果任务涉及 repo-local 操作，再按需读：
   - [Autoresearch 最小闭环运行说明](../runbooks/autoresearch-minimal-loop.md)
   - [Research CLI 帮助](../references/research-cli-help.md)
   - [TMP Exrepo 维护说明](../runbooks/tmp-exrepo-maintenance.md)
3. 如果任务涉及 phase contract、当前 active research 或输出观测，再进入 [../references/research-eval-contracts.md](../references/research-eval-contracts.md) 与 [../references/research-eval-observability.md](../references/research-eval-observability.md)。
4. 只有任务明确落到实现或 CLI 内部接线时，再读 [toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)。

### 2. 修改实现时

1. 先读本页。
2. 再读 [toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)。
3. 再进入目标脚本、测试和 fixture。
4. 只有需要阶段语义或实现边界时，再进入对应 `toolchain/scripts/research/` 源码与测试。

## 五、快速判断

如果问题是下面这些，优先看本模块：

- “`autoresearch` 到底算什么对象？”
- “这个改动属于模块边界、repo-local runbook、阶段分析，还是运行态？”
- “改 `autoresearch` 应该先读哪一层？”

如果问题是下面这些，不要只停在本模块：

- 具体 CLI 参数和操作步骤
- 某个 phase 的细节设计
- 某个脚本或测试应该怎么改
- 某次 run 的运行时残留状态

## 六、相关文档

- [Autoresearch README](../README.md)
- [AGENTS.md](../../../AGENTS.md)
- [Autoresearch 最小闭环运行说明](../runbooks/autoresearch-minimal-loop.md)
- [Research Scripts](../../../toolchain/scripts/research/README.md)
