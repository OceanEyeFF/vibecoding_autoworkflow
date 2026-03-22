---
title: "AI Coding 编排方法论"
status: reference
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# AI Coding 编排方法论

> 这是一份受治理的外部参考摘要，来源于一段 ChatGPT 长对话。它只提供方法论背景，不提供当前仓库真相，也不是默认执行入口。

## 使用边界

- 只有在 `docs/knowledge/` 主线文档不足以支持判断时，才进入本页
- 本页只能作为外部方法论参考，不能覆盖当前仓库的分层、路径和写作规则
- 如果本页与知识层文档冲突，以 `docs/knowledge/` 为准
- 原始对话导出已归档到 [../archive/chatgpt-ai-coding-methodology-raw-export.md](../archive/chatgpt-ai-coding-methodology-raw-export.md)

## 来源信息

| 字段 | 内容 |
|---|---|
| 来源 | ChatGPT 对话导出 |
| 会话标题 | AI Coding 编排方法论 |
| 导出时间 | 2026-03-11 00:06:20 |
| 整理时间 | 2026-03-23 |
| 原始链接 | <https://chatgpt.com/c/69ae646e-5cc8-83a1-8df3-d23e3ce9d3a0> |

## 核心观点

- AI coding 更适合被理解成闭环系统，而不是单次生成行为
- 至少要有一个主导端或控制面，负责持有当前 phase、接收反馈并做裁决
- 白盒验证可以贴近执行层，但黑盒验证最好保留需求侧的独立视角
- 代码改完不等于任务结束，标准化流程还应包含文档沉淀和 writeback
- Prompt 和上下文需要定期清理，否则会出现污染、冲突和伪事实残留
- 比起继续堆 agent catalog，更重要的是把 shared state、任务对象和验证 gate 固化下来
- 文档系统应优先服务 AI 导航和上下文裁剪，而不是只服务人类长文阅读

## 提炼后的主题结构

### 1. 编排闭环

材料反复强调一条主线：任务需要从目标定义、执行、验证、回写、清场形成闭环，否则系统会退化成上下文污染和责任空洞。

### 2. 控制面与执行面分离

材料把“主导端”看作任务状态机拥有者，而不是最强执行者。它负责当前真相、阶段推进、验证裁决和收尾判断。

### 3. 验证应区分白盒与黑盒

材料认为白盒检测可以与执行端贴近，因为它依赖内部实现知识；黑盒检测则更适合站在需求和用户结果一侧，避免执行偏见。

### 4. 文档沉淀与上下文清场

材料把 writeback 和 Prompt cleanup 视为标准化流程的一部分。前者用于刷新团队记忆，后者用于控制上下文熵增。

### 5. 从 agent 菜单转向 state-centric kernel

材料后半段多次提出，比起继续扩充 agent / skill 数量，更关键的是抽出稳定对象，例如任务基线、决策记录、上下文入口和运行记录。

### 6. AI Friendly 文档库与任务 Gate

材料最后收束到两个系统：

- AI Friendly 文档库，用于提供可导航、可裁剪的项目长期记忆
- 任务前后 gate，用于在执行前形成正式基线，并在完成后强制回写

## 可复用的对象建议

材料里反复收束到 3 个轻量对象，适合当作方法论参考：

- `Task Contract`：任务目标、非目标、相关上下文、代码边界、验收标准、风险
- `Context Entry`：读什么、后读什么、暂时不要读什么、关键文件和限制
- `Writeback Log`：改了什么、为什么、涉及文件、文档更新点、遗留事项

## 对当前仓库的使用方式

- 可用来理解为什么当前仓库强调 `Knowledge Base / Context Routing / Writeback & Cleanup`
- 可用来补充理解“为什么不能把 `reference` 当真相层”
- 不应直接照搬其中对旧仓库的目录建议、阶段判断或产品比较结论

## 当前不应直接采纳的历史建议

- 材料中出现过把 `workflow/` 单独拉成根级主线的建议，这不再符合当前仓库的根目录分层合同
- 材料中关于旧版仓库 README、agent catalog、MyClaude 对照的判断属于当时上下文，不是当前仓库真相
- 涉及外部项目、公司实践或产品定位的结论，需要单独核查，不能直接写回知识层

## 主题索引

- 编排闭环与控制论视角
- 主导端、执行端、白盒验证、黑盒验证
- 文档沉淀与 Prompt cleanup
- state-centric orchestrator kernel
- AI Friendly 文档库
- `Task Contract / Context Entry / Writeback Log`
- 外部工作流系统与当前仓库的对照分析
