---
title: "Knowledge Base"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Knowledge Base

> 目的：定义项目长期真相如何以静态文档存在。Memory Side 总边界见 [overview.md](./overview.md)。

## 一、职责

`Knowledge Base` 负责：

- 保存项目长期真相。
- 提供稳定入口和模块边界。
- 支持 `Context Routing` 选择最小阅读范围。
- 支持 `Writeback & Cleanup` 把已验证结果写回。

它不负责：

- 执行任务。
- 保存运行状态。
- 替代源码、测试或 deploy target。
- 收纳未验证推理。

## 二、工作模式

| 模式 | 适用场景 | 最小动作 |
| --- | --- | --- |
| `Bootstrap` | 新项目或文档骨架缺失 | 建入口页、模块边界、决策位、变更位 |
| `Adopt` | 已有文档但主线混乱 | 识别主线、归类参考和归档、清理旧入口 |

两种模式都只写已确认事实。未验证结论留在任务 evidence，不进入长期 truth。

## 三、文档层级

| 层级 | 职责 | 默认读取级别 |
| --- | --- | --- |
| `Core Truth` | 目标、架构、模块入口、稳定决策 | 默认读取 |
| `Operational Truth` | runbook、验证方式、治理规则、维护流程 | 任务相关时读取 |
| `Exploratory Records` | 调研、方案比较、临时分析 | 只在 investigation 或设计追溯时读取 |
| `Archive` | 过期或被替代内容 | 默认不读 |

## 四、当前仓库投影

| 内容 | 当前承接位 |
| --- | --- |
| 项目维护、治理、deploy、testing、usage help | `docs/project-maintenance/` |
| Harness doctrine、scope、artifact、catalog、workflow families | `docs/harness/` |
| Harness adjacent systems 合同 | `docs/harness/adjacent-systems/` |
| executable source | `product/` |
| 部署、测试、治理脚本 | `toolchain/` |

`.agents/`、`.claude/`、`.aw/`、`.nav/` 不属于 Knowledge Base 真相层。

## 五、读取规则

默认先读：

- 最近的 `README.md`
- 与任务直接相关的承接层正文
- 相关治理或边界规则

默认不读：

- archive
- deploy target
- repo-local state
- 无关历史 evidence

需要扩读时，应由 `Context Routing` 明确列出原因和停止条件。

## 六、写回规则

只有已验证结果可以写回 Knowledge Base。

写回时必须：

- 写到正确承接层。
- 更新最近入口页。
- 清理旧入口或双主线。
- 保留源码、测试和文档的 owner 边界。

不写回：

- 临时推理。
- 未验证结论。
- 运行日志原文。
- 本地环境噪声。

## 七、判断标准

Knowledge Base 清楚时，应满足：

- 不同后端读到同一套项目真相。
- 入口能把任务导向正确承接层。
- 旧内容不会占据主线入口。
- 已验证事实能回写，未验证事实不会混入。
- repo-local runtime state 不替代长期文档。

## 八、相关文档

- [Memory Side 总览](./overview.md)
- [Context Routing](./context-routing.md)
- [Context Routing 规则](./context-routing-rules.md)
- [Writeback & Cleanup](./writeback-cleanup.md)
- [Writeback & Cleanup 规则](./writeback-cleanup-rules.md)
