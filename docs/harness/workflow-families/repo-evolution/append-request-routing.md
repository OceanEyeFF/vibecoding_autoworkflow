---
title: "Append Request Routing"
status: active
updated: 2026-04-25
owner: aw-kernel
last_verified: 2026-04-25
---
# Append Request Routing

> 目的：固定 `repo-evolution` family 下 append-feature / append-design 追加请求的分类与路由规则。

## 定位

追加请求 intake 发生在执行前。它回答"这条新增要求应该进入哪条控制路由"，不回答"现在怎么实现"。

支持两个 mode：

- `append-feature`
- `append-design`

两个 mode 由同一个 `repo-append-request-skill` 承接，不拆成两个 skill。

## 分类结果

### goal change

追加请求改变 repo 长期参考信号时使用：

- 改变愿景、核心目标、成功标准或系统不变量
- 需要修改 `Engineering Node Map`
- 与现有 `Goal Charter` 冲突

下一路由：`repo-change-goal-skill`。

### new worktrack

追加请求仍在当前 repo 目标内，但应独立成为新 worktrack 时使用：

- 不属于当前活跃 worktrack 的批准范围
- 可绑定到 `Engineering Node Map` 中的候选 node type
- 需要独立 branch、baseline、contract、plan 与 gate

下一路由：`init-worktrack-skill`。

### scope expansion

追加请求试图扩大当前活跃 worktrack 时使用：

- 当前存在活跃 worktrack
- 请求不在已批准范围内
- 会改变验收、影响模块、风险、验证要求或完成定义

下一路由：`scope-expansion-approval`，审批后才允许更新 worktrack contract 或重新初始化。

### design-only

追加请求只要求设计判断或设计产物，不要求同轮实现时使用：

- 设计结果可独立验收
- 证据不足以进入实现
- `append-design` 默认优先考虑该类

下一路由：设计型 worktrack，产出设计 artifact 后返回 gate。

### design-then-implementation

追加请求要求先设计、再在设计 gate 通过后实现时使用：

- 用户明确要求先设计再实现
- feature 风险或架构不确定性要求先形成设计结论
- 设计是 implementation 的前置 gate

下一路由：两阶段 worktrack；第一阶段为 design gate，第二阶段才允许 implementation。

## 优先级

- `goal change` 优先于所有其他分类。
- `scope expansion` 与 `new worktrack` 冲突时，以用户是否要求纳入当前活跃 worktrack 为判定点；要求纳入当前轮则先走 `scope expansion` 审批，否则走 `new worktrack`。
- `append-design` 只有在用户明确授权实现，或实现是请求不可分割的一部分时，才归为 `design-then-implementation`。
- 分类证据不足时，不得擅自执行；应返回最小缺失信息。

## 输出

路由结果必须至少包含：

- mode
- 原始追加请求
- 分类结果
- 分类理由
- 目标影响
- 活跃 worktrack 影响
- 建议下一路由
- 建议下一 scope
- 权限边界
- 最小缺失信息
- continuation readiness

## Continuation 规则

`approval_required`、`continuation_ready` 与 `continuation_blockers` 必须保持一致：

- 需要新审批或 authority boundary 尚未满足时，`approval_required: true`、`continuation_ready: false`
- `goal change` 与 `scope expansion` 默认停在审批边界，除非输入事实已经明确批准该边界
- 最小缺失信息会阻塞分类或路由时，`continuation_ready: false`，并在 `continuation_blockers` 中列出缺失信息
- 没有待审批项且没有阻塞性缺失信息时，才允许 `continuation_ready: true`，但本 workflow 仍只返回推荐 route，不执行后续 route

## 非目标

- 不执行 feature 或 design
- 不创建 branch
- 不改写 `Goal Charter`
- 不改写 worktrack contract
- 不替代 `repo-whats-next-skill` 的 repo 级优先级判断
