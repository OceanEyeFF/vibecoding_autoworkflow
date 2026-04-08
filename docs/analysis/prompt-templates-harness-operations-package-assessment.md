---
title: "Prompt Templates 与 Harness Operations Package 评估"
status: superseded
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Prompt Templates 与 Harness Operations Package 评估

> 说明：本文保留为上一轮问题 framing 的 lineage 记录。它建立在“`docs/operations/prompt-templates/` 仍可被视为 repo-local execution template layer，并需要继续评估包本体 vs repo-local 实例化层”的前提上。

> 当前这个前提已经被替换。当前默认入口请先回到 [Analysis README](./README.md)，再进入 [Prompt Templates 产品化与 Skills 分发评估](./prompt-templates-productization-and-skill-distribution-assessment.md)。

> 目的：在调整 `docs/operations/prompt-templates/` 或规划通用分发资产之前，先固定当前对象边界、候选分发包范围、架构影响、deploy/eval 影响与决策出口条件，避免把目录动作误写成产品结论。

## 一、评估范围

本文只评估下面问题：

- `docs/operations/prompt-templates/` 当前到底承载什么对象
- 哪些模板可能属于“可分发的 harness 操作包”
- 哪些模板只属于当前仓库的 repo-local execution scaffold
- 如果未来新增一个通用 harness 操作包，会影响哪些知识、运行、部署、验证与评测承接位
- 这个通用包是否应默认纳入 skills 的训练 / 评测 / 改进闭环

本文不直接做下面动作：

- 不直接迁移目录
- 不直接新增 `product/` 下的新 partition
- 不直接新增 canonical skill
- 不直接修改 deploy / eval / governance 脚本
- 不预先认定它必须叫 `Harness-Orchestrator`

## 二、当前已确认任务

当前讨论里，下面两点已经不是开放问题，而是后续设计必须满足的明确任务：

1. 基础 skills / templates 需要从当前的模板形态，进一步收敛成可分发、可安装、可维护的封包内容。
2. harness skills 需要共用一套 `Shared Harness Template`，而不是继续各自复制一份相似但不完全一致的 harness 结构。

这两条的含义分别是：

- 第一条要求后续设计必须回答“哪些对象进入通用分发包、哪些留在 repo-local 实例化层”。
- 第二条要求后续设计必须抽出一套共享的 harness contract / workflow interface / repo-local bindings，而不是只保留隐式共通模式。

## 三、原来是什么

当前 `docs/operations/prompt-templates/` 的定位已经比较明确：

- 它是 `docs/operations/` 下的 `repo-local execution template layer`
- 它消费 `docs/knowledge/` 主线真相，但不重写主线 truth
- 它服务 repo-local harness 或人工协作，不是独立 truth partition

当前平铺模板实际混合了两类对象：

### 1. 更接近 `Task Interface` 消费层的模板

- `execution-contract-template.md`
- `task-planning-contract.md`
- `simple-subagent-workflow.md`
- `strict-subagent-workflow.md`

这些模板的共同特点是：

- 强依赖 `Task Contract` 结构
- 用于在进入执行前冻结边界、计划、验证与退出条件
- 本质是 `Task Interface` 的 repo-local consumption layer，而不是 `Task Interface` truth 本体

### 2. 更接近 harness 操作壳的模板

- `harness-contract-template.md`
- `review-loop-code-review.md`
- `task-list-subagent-workflow.md`
- `repo-governance-evaluation.md`

这些模板的共同特点是：

- 直接依赖 `.autoworkflow/` 下的 state / contract 文件
- 直接调用 `toolchain/scripts/test/` 下的 gate / backfill / governance 工具
- 更像 harness state contract、workflow shell 与治理收口壳

### 3. 当前不存在清晰独立的 `memory-side` 专属模板簇

现有模板里，没有一组稳定文档是在直接承接：

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

的专属 repo-local execution template。

这意味着当前如果强行把 `prompt-templates/` 物理拆成 `task-interface / harness-orchestrator / memory-side`，会出现：

- `task-interface` 有实质内容
- harness 相关模板有实质内容
- `memory-side` 大概率为空，或被塞入语义并不准确的模板

## 四、现在想做什么

当前讨论中的目标，不应该被定义成“把目录拆成三块”，而应该先被定义成下面两个候选目标之一。

### 路线 A：只做 `operations` 局部分组

目标：

- 提高 `prompt-templates/` 的可发现性
- 降低 `Task Contract` 消费模板与 harness 操作壳模板的混杂度
- 不改变当前仓库的正式 partition 模型

这个路线下，harness 相关内容只是：

- `docs/operations/` 下的 repo-local execution concern
- `prompt-templates/` 内部的逻辑分类
- 或未来 `docs/operations/` 下的一个稳定子簇

### 路线 B：定义一个通用分发包

目标：

- 新增一个可市场分发、可跨仓库复用的通用操作包
- 把“包本体”和“本仓库实例化层”分开
- 只把真正通用的 harness 操作资产升格为正式对象
- 必要时新增 canonical package / adapters / eval 闭环

这个路线下，当前目录整理只是副产物，不是主目标。

## 五、当前判断

基于当前讨论的新前提，现阶段更合理的判断是：

- 当前真正需要评估的不是“是否要建 `Harness-Orchestrator` 目录”，而是“是否要定义一个通用 harness 操作包”
- `Harness-Orchestrator` 这个名字目前不够稳，它容易误导为“所有东西都属于 orchestrator”
- 更中性的工作名当前建议使用 `Harness Operations Package`
- 这个候选通用包如果成立，应该是一个正式分发对象，而不只是 `docs/operations/` 下的 repo-local concern
- 但它也不应把所有 harness 相关模板都无差别打包进去

当前这样判断的依据包括：

- `partition-model.md` 当前只固定 `Knowledge Base / Context Routing / Task Contract / Writeback & Cleanup`
- `task-contract.md` 明确 `Task Contract` 不是宿主运行时编排器
- `memory-side/layer-boundary.md` 已把 `docs/operations/prompt-templates/` 固定为统一的 repo-local execution template layer
- `research-eval-contracts.md` 明确 backend runner 抽象不是引入新的 orchestrator 层

## 六、预期效果应该怎么定义

如果沿着“先评估、后决定”的方式推进，预期效果应按两种路线分别定义。

### 1. 若最终结论是 `operations-only`

预期效果应是：

- `prompt-templates/` 内部模板更容易按用途被找到
- `Task Interface` 消费模板与 harness 操作壳模板不再混看
- 不改变当前知识层 partition
- 不引入新的 deploy target、skill family 或 eval family

### 2. 若最终结论是“通用分发包成立”

预期效果才应是：

- 新增一套稳定的通用包定义
- 明确哪些资产属于包本体，哪些只属于仓库实例化层
- 明确 source of truth 落点
- 补齐 deploy / verify / eval / acceptance / training 的承接位
- 让这个通用包成为被验证、可复用、可演进的正式能力对象

## 七、工作名与命名判断

当前不建议直接把对象名固定成 `Harness-Orchestrator`。

原因：

- 这个名字会让人误以为所有模板都属于 orchestrator
- 现有模板里有不少对象只是 contract、workflow shell、governance prompt，不适合直接被叫作 orchestrator skill
- 名称一旦过早固定，会把产品边界、控制面边界和模板边界混写

当前更稳的工作名建议是：

- `Harness Operations Package`

这个名字的好处是：

- 不预设它一定是 orchestrator
- 能容纳 contract、workflow shell、review-loop、task-list 这类操作资产
- 允许后续再拆成更细的对象族，而不是一开始就套进 orchestrator 概念

## 八、包本体 vs repo-local 实例化

如果未来真的要分发一个通用 harness 操作包，必须先分清两层。

### 1. 包本体

更可能属于包本体的内容：

- 通用的 harness contract shape
- 通用的 review-loop workflow shell
- 通用的 task-list workflow shell
- 可跨仓库复用的治理评估 prompt 结构

这些对象如果成立，应逐步进入：

- `docs/knowledge/` 的对象定义
- `product/` 的可分发承接位
- 必要时进入 `product/*/adapters/` 与 `product/*/manifests/`

### 2. 本仓库实例化层

更可能只属于本仓库实例化层的内容：

- `.autoworkflow/` 的具体 state 文件名
- 当前仓库 gate 命令
- 当前仓库 review / verify 规则
- 当前仓库 closeout 口径
- 当前仓库 path governance 与 handoff 规则

这些对象应继续主要落在：

- `docs/operations/`
- `toolchain/scripts/test/`
- repo-local state layer

## 九、哪些模板不应直接规划进通用包

当前至少不应把下面对象直接等同于通用包本体：

- 所有 `Task Interface` 消费模板
- 所有带有当前仓库 `.autoworkflow/` 文件路径的 state 约定
- 所有直接依赖当前仓库 gate 命令的 workflow 模板
- 所有只服务当前仓库 closeout / governance 的提示壳

更准确的做法应是：

- 先抽出“通用 contract / workflow shell / prompt shape”
- 再把当前仓库特有的路径、命令、状态文件、verify 口径留在实例化层

## 十、关键架构问题

在进入任何目录或结构动作前，至少要先回答下面问题。

### 1. 通用包到底是什么对象族

必须先明确它是下面哪一种：

- contract family
- workflow shell family
- prompt asset package
- 可部署的 canonical skill family
- 新的 product family
- 上述几者的受控组合

如果这个问题不先固定，后续所有分类和分发动作都会混乱。

### 2. 它与 `Task Contract` 的边界是什么

当前 `Task Contract` 已经负责：

- 目标
- 范围
- 验收
- 依赖
- 风险
- 验证要求

所以通用 harness 操作包如果成立，必须说明它不重复拥有这些真相；更合理的关系应是：

- `Task Contract` 提供正式执行基线
- 通用包只消费该基线，并提供 workflow shell、contract shape 或治理操作壳
- 当前仓库实例化层再补 state transition、gate binding 与 closeout control

### 3. 它与 `Memory Side` 中的 `Agent / Workflow Shell` 是什么关系

`memory-side/skill-agent-model.md` 当前已经保留了：

- `Agent / Workflow Shell` 是可选调用层
- 它不是当前仓库知识主线的一部分

因此如果未来要稳定建设这个通用包，就必须明确：

- 它只是这个“可选调用层”的一组可分发操作资产
- 还是要把“调用层”本身升格成主线对象族

### 4. 它的 source of truth 应落在哪层

必须先判断清楚：

- 如果只是 repo-local 流程壳，真相主要在 `docs/operations/` 与 `toolchain/`
- 如果是稳定规则对象，知识边界应进入 `docs/knowledge/`
- 如果是可分发能力，源码与分发元数据应进入 `product/`

目录动作必须晚于这个判断。

## 十一、对分发与 DeploySkills 的影响

这是本次讨论最容易被低估的一部分。

当前 deploy 主线只认：

- `product/memory-side/`
- `product/task-interface/`

`toolchain/scripts/deploy/adapter_deploy.py` 当前也只枚举这两个 partition。

这意味着：

### 1. 若只停留在 `operations`

它对分发与 DeploySkills 的影响应为零或极小：

- 不新增 `product/` 分区
- 不新增 adapter source root
- 不新增 repo-local deploy target
- 不改 `adapter_deploy.py` 的 partition 列表

### 2. 若通用包进入正式分发面

它会连带触发至少这些改动：

- `product/` 下新增承接位
- 对应 backend adapters 增加 source roots
- `product/*/manifests/` 补充打包 / 市场分发元数据
- `adapter_deploy.py` 的 `PRODUCT_PARTITIONS` 更新
- repo-local mounts 新增 deploy / verify 覆盖
- `docs/operations/deploy*` 文档补充新的 deploy / smoke / verify 路径

因此，对分发与 DeploySkills 的正确态度应是：

- 现在先评估，不默认承诺接入
- 只有在包本体已经被定义成正式分发对象时，才把它视为 DeploySkills 改造范围

## 十二、对训练 / 评测 / 改进闭环的影响

当前仓库的评测闭环是围绕已存在 skill family 建立的：

- runner 在 `toolchain/scripts/research/`
- eval assets 在 `toolchain/evals/`
- acceptance / suite / judge 逻辑已围绕现有 skills 收口

因此，不能默认把整个通用 harness 操作包直接加入闭环。

### 1. 不应默认纳入的情况

如果某部分内容主要是下面这些对象：

- workflow shell
- harness state schema
- closeout contract
- governance / gate orchestration 壳

那它更应该优先进入：

- `docs/operations/`
- `toolchain/scripts/test/`

这条 verify / governance 路，而不是 skill train loop。

### 2. 只有满足下面条件，才考虑纳入闭环

- 它已被定义成稳定、可部署、可单独调用的 package object 或 canonical skill family
- 它有清晰输入 / 输出 contract
- 它的质量可以被独立评测，而不是只能依附人工流程判断
- 它能被 suite / acceptance / judge 明确覆盖

只有这种情况下，才需要补：

- eval prompt
- suite manifest
- acceptance coverage
- 可能的 train / validation loop

## 十三、影响面矩阵

如果未来真的引入一个通用 harness 操作包，最小影响面如下。

### 1. 只做 `operations` 分类时

最小需同步：

- `docs/operations/prompt-templates/README.md`
- `docs/operations/README.md`
- `docs/operations/review-verify-handbook.md`
- `docs/operations/path-governance-checks.md`

可能需要补充说明的知识文档：

- `docs/knowledge/foundations/docs-governance.md`
- `docs/knowledge/foundations/path-governance-ai-routing.md`

### 2. 进入正式分发面时

至少还要同步：

- `docs/knowledge/foundations/partition-model.md`
- `docs/knowledge/task-interface/task-contract.md`
- `docs/knowledge/memory-side/skill-agent-model.md`
- `docs/knowledge/memory-side/layer-boundary.md`
- `product/` 对应 source layer 与 manifests
- `toolchain/scripts/deploy/adapter_deploy.py`
- `toolchain/evals/` 对应 eval assets
- `toolchain/scripts/test/` 与相关测试

## 十四、出口条件

在进入目录或结构调整前，本议题至少应满足下面出口条件。

### 最小出口条件

- 明确工作名是否继续使用 `Harness-Orchestrator`
- 明确通用包和 repo-local 实例化层的边界
- 明确基础 skills / templates 进入可分发封包的最小对象清单
- 明确 `Shared Harness Template` 的共享字段、扩展位与 repo-local bindings
- 明确哪些模板属于通用包本体，哪些不属于
- 明确它与 `Task Contract` 的边界
- 明确它与 `Memory Side` 中 `Agent / Workflow Shell` 的关系
- 明确它是否会影响 deploy source roots
- 明确它是否进入 eval / acceptance / training 闭环

### 若要进入正式改造阶段

还需补齐：

- source of truth 落点
- 包本体清单
- repo-local 实例化清单
- shared harness template 清单
- 同步文档清单
- deploy / verify 变更清单
- eval / acceptance 变更清单
- governance tests 更新清单

## 十五、当前建议路径

当前最稳的推进顺序如下：

1. 保持 `docs/operations/prompt-templates/` 的物理路径不动。
2. 先不要把名字固定成 `Harness-Orchestrator`。
3. 先以 `Harness Operations Package` 作为工作名，继续收口包本体边界。
4. 在本评估基础上做一次结论收束：
   - `operations-only`
   - `generic distributable package`
5. 抽出一份 `Shared Harness Template` 设计稿，明确 core fields、workflow extensions 与 repo-local bindings。
6. 梳理基础 skills / templates 进入可分发封包的最小对象清单。
7. 如果结论只是 `operations-only`，先只改 `prompt-templates/README.md` 的逻辑分组说明。
8. 只有当结论明确为“通用分发包成立”时，再进入 foundations / product / deploy / eval / tests 的联动改造。

## 十六、非目标

本文当前不主张：

- 立即迁目录
- 立即新增 `.autoworkflow/` 状态模型
- 立即把所有 harness 壳都包装成 canonical skill
- 立即把 repo 变成 runtime orchestrator 项目

## 十七、相关文档

- [项目 Partition 模型](../knowledge/foundations/partition-model.md)
- [Task Contract 基线](../knowledge/task-interface/task-contract.md)
- [Memory Side 层级边界](../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../knowledge/memory-side/skill-agent-model.md)
- [Prompt Templates](../operations/prompt-templates/README.md)
- [Deploy / Verify / Maintenance](../operations/deploy/README.md)
- [Research 评测契约与边界](./research-eval-contracts.md)
- [Governance Checks](../../toolchain/scripts/test/README.md)
