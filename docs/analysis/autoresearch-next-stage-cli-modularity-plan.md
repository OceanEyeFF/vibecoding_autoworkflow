---
title: "Autoresearch：下一阶段 CLI 模块化与插拔化建议"
status: active
updated: 2026-04-09
owner: aw-kernel
last_verified: 2026-04-09
---
# Autoresearch：下一阶段 CLI 模块化与插拔化建议

> 说明：本文承接当前 `autoresearch` 从“research scripts 集合”向“更适合 `codex | claude` 交互使用的 CLI 软件”演进的下一阶段建议。它属于 `analysis`，用于固定问题判断、模块化方向和后续拆分建议，不替代 `docs/operations/` 的现行 runbook，也不替代 `toolchain/` 的当前实现合同。

## 一、本文定位

本文只回答下面这组问题：

- 当前 `autoresearch` 是否值得继续往交互式 CLI 软件方向收敛
- 当前实现中最妨碍这一步的结构问题是什么
- 下一阶段的模块化和插拔化应该优先改哪几层
- 后续任务应该如何拆，避免再次落回“大脚本继续堆功能”

本文不直接定义：

- 已验证的长期真相
- 当前默认执行计划
- 具体实现完成后的 repo-local 操作说明

## 二、当前判断

当前 `autoresearch` 已经证明了两件事：

1. 它不只是一次性研究脚本，已经具备成为稳定 CLI 工具的价值。
2. 它当前最大的结构问题不是“功能太少”，而是很多能力还不够插拔，新增功能时改动面过大。

这里的“有价值”主要体现在：

- 已经存在清晰的命令入口：`init / baseline / prepare-round / run-round / decide-round / promote-round / discard-round / cleanup-round`
- 已经存在 backend 层抽象，且 `codex / claude / opencode` 的差异开始收敛
- 已经存在稳定的 repo-local artifact 面与运行状态面
- 已经开始出现 operator-facing 需求，而不只是一次性实验需求

这里的“最大问题”主要体现在：

- 主流程脚本同时承担 CLI dispatch、phase orchestration、policy 选择、artifact 写盘和局部特例处理
- 新增一个 operator-facing 能力时，往往需要穿透多个模块同时改，而不是挂到稳定接口上
- 当前很多行为是“可以扩展”，但还没有被固定成“可插拔 contract”

## 三、当前最明显的结构瓶颈

### 1. `run_autoresearch.py` 承担的职责过多

当前它同时承接：

- CLI 参数解析与命令 dispatch
- baseline 执行与 runtime 同步
- prepare 阶段的 stop gate、registry 选择、authority 冻结
- round 入口切换
- status 索引刷新
- P2 专属 preflight 接线

这会导致：

- 新增一个 phase 或 operator-facing 视图时，很容易继续往主入口叠逻辑
- phase contract 不稳定，测试也更容易跟着主入口耦合放大

### 2. `autoresearch_round.py` 混合了 orchestration、policy 与 artifact 逻辑

当前它同时承接：

- round lifecycle
- diff scope / mutation scope 校验
- scoreboard 驱动的 decision 规则
- replay 执行
- feedback distill 与 ledger 写盘
- baseline scoreboard 前移

这会导致：

- fixed-rule decision、replay policy、feedback artifact 很难独立演进
- 任何一个子能力升级，都容易触碰整个 round orchestration

### 3. “可扩展”与“可插拔”之间还差一层 contract

当前已有的能力，如：

- backend registry
- selector
- stop gate
- feedback distill
- status aggregation

都已经有了“可分模块放置”的形态，但还没有彻底固定为：

- 明确输入输出
- 可注册或可替换
- 可以被主流程稳定消费

结果是它们虽然存在独立文件，但很多时候仍属于“主流程硬编码调用的 helper”，而不是稳定插件点。

## 四、下一阶段的架构目标

下一阶段不应把 `autoresearch` 扩成更重的平台，而应把它收成：

- 一套更稳定的 CLI command surface
- 一组更清晰的 phase contracts
- 一组可替换但默认实现内置的 policy modules
- 一组 operator-facing outputs，而不是把内部 artifact 直接暴露给用户

建议目标口径是：

- 对 operator 而言，它是一个更稳定、更适合 `codex | claude` 交互的 CLI 软件
- 对实现层而言，它仍然保持 repo-local、低侵入、可回放，不扩成独立服务系统

## 五、建议优先插拔化的对象

### 1. Command registry

把 `init / baseline / prepare-round / run-round / decide-round / promote-round / discard-round / cleanup-round / refresh-status` 统一为显式命令表，而不是继续增长 `if args.command == ...` 分支。

目标：

- 命令入口稳定
- 每个命令的依赖和副作用更容易单测
- 后续新增只读命令或 operator summary 命令时，不再继续污染主入口

### 2. Phase runner contract

把每个 phase 的输入输出和前后置约束固定成更薄的 phase contract，例如：

- 输入哪些 authority artifacts
- 产出哪些 runtime / observability artifacts
- 失败时允许什么类型的恢复

目标：

- phase orchestration 与 phase implementation 分离
- 让 CLI shell 更薄

### 3. Policy modules

当前最适合抽成 policy contract 的对象包括：

- stop rule
- mutation selector
- feedback distiller
- replay trigger / replay acceptance rule
- status summarizer

建议原则：

- 默认实现仍内置
- 先固定输入输出 contract，再讨论是否开放多实现切换
- 不在下一阶段引入“模型自由生成 policy”

### 4. Backend interaction profile

当前 backend adapter 已经存在，但 operator-facing CLI profile 还不够独立。

建议下一阶段把下面几类差异进一步收口：

- backend executable / sandbox / permission defaults
- worker backend 与 judge backend 组合
- 适合交互模式的 profile 预设

目标：

- operator 切换 `codex` / `claude` 时，不需要理解太多底层接线细节
- backend 差异更多停留在 profile 和 adapter，而不是继续散落到 orchestration 脚本

### 5. Artifact projection layer

当前已经有 authority artifacts、scoreboard、feedback、status index 等多种输出。

下一阶段建议明确分成三层：

- authority artifacts：供脚本重算、恢复和 fail-closed 校验
- observability artifacts：供复盘和诊断
- operator summaries：供人直接查看的简洁输出

目标：

- 不再把“给机器用的 JSON”直接当 operator UI
- 新增 summary 时不需要修改核心流程语义

## 六、建议避免的方向

### 1. 不要先做“大重构”

如果下一阶段以“大重写 `run_autoresearch.py`”开场，风险很高。

更好的做法是：

- 先抽 contract
- 再迁移调用点
- 最后再收薄主入口

### 2. 不要先做通用 plugin marketplace

当前需要的是 repo 内可插拔，不是对外开放的 plugin system。

下一阶段更合适的范围是：

- internal registry
- internal contracts
- local defaults

而不是：

- 外部动态插件加载
- 跨 repo 发布协议

### 3. 不要把 operator-facing CLI 和研究控制面混成一层

如果以后同时出现：

- “日常发起和查看 run 的命令”
- “底层实验开关”

应优先让前者稳定，再把后者继续收在 expert / internal 层，而不是全部平铺给 operator。

## 七、建议的任务拆分

### T-301：Command registry 收口

目标：

- 把 `run_autoresearch.py` 的命令分发改成显式 command registry

完成标准：

- 新增命令不需要继续堆 `if args.command == ...`
- 每个命令 handler 的依赖更清楚

### T-302：Phase contract 收口

目标：

- 为 baseline / prepare / run / decide 等 phase 建立显式输入输出 contract

完成标准：

- phase 逻辑不再隐式依赖主入口局部状态
- phase handler 可单独测试

### T-303：Policy 模块抽离

目标：

- 把 stop rule、selector、feedback distill、status summarizer 明确成 policy modules

完成标准：

- policy 变化不需要修改主 orchestration 结构
- 默认实现与未来替代实现共用同一 contract

### T-304：CLI profile 收口

目标：

- 为 `codex` 与 `claude` 形成更适合交互使用的 profile 入口

完成标准：

- operator 不需要再在多个脚本和多个 flag 之间手工拼接常用组合
- backend 差异更少泄漏到 phase orchestration

### T-305：Operator summary 层

目标：

- 在 authority / observability artifact 之上提供更适合人读的 CLI 输出

完成标准：

- 当前 run 状态、skill 状态、最近 decision、活跃 round 能用单独 summary 视图查看
- summary 视图不改变 authority artifact 语义

## 八、当前优先级建议

建议顺序：

1. 先做 command registry 和 phase contract
2. 再做 policy 模块抽离
3. 然后做 operator-facing summary / profile
4. 最后再评估是否需要更强的 plugin-style 扩展点

原因：

- 当前最大的痛点是新增功能时必须穿透主流程
- 这个问题不先解决，后续任何 CLI 软件化都会继续放大脚本耦合
- summary 和 profile 很有价值，但前提是底层 contract 先稳住

## 九、与现有文档体系的关系

本文是下一阶段建议，不是当前默认执行计划。

如果后续某条建议被接受并开始实现，应承接到：

- `docs/analysis/` 下更收敛的 task-plan
- `toolchain/scripts/research/README.md` 的实现入口说明
- `docs/operations/` 的 repo-local CLI 帮助

如果后续某条边界被验证并长期稳定，再考虑升格到：

- `docs/knowledge/`

## 十、一句话结论

`autoresearch` 继续演进的价值是存在的，但下一阶段最值得优先解决的不是“继续加功能”，而是把它收成一个更模块化、更可插拔、也更适合 `codex | claude` 交互使用的 CLI 软件。
