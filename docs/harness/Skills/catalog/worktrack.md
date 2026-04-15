---
title: "Harness Skill Catalog / WorktrackScope"
status: draft
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# WorktrackScope Skill Catalog

> 目的：固定 `WorktrackScope` 下直接面向 `Codex` 的 Harness skills catalog。

这里记录的是 worktrack 闭环里实际会被 supervisor 选择和调用的 skills，而不是再额外维持一组抽象 function 名字。

## 当前原则

- `WorktrackScope` skills 负责局部状态转移闭环
- 它们消费 `contract / plan / evidence / control state`
- 它们可以派发下游 subagent，但自身不应伪装成“控制平面 + 执行平面一体”

## Catalog

### 1. init-worktrack-skill

职责：

- 初始化 branch、baseline 和 `Worktrack Contract`
- 建立最小 `Plan / Task Queue`

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Harness Control State`

当前状态：

- `draft catalog target`

### 2. schedule-worktrack-skill

职责：

- 根据当前 contract、证据和阻塞情况刷新任务队列
- 决定当前下一动作

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Gate Evidence`

当前状态：

- `draft catalog target`

### 3. dispatch-skills

职责：

- 接收当前 `Worktrack` 的下一任务
- 组装 bounded task 和最小信息包
- 优先选择合适的专门 skill 或 subagent 执行方式
- 当系统中没有合适的专门 skill 时，自动 fallback 到通用任务完成 `SubAgent`
- 跑一轮 bounded execution
- 回传 evidence 和状态结果

主要依赖：

- `Worktrack Contract`
- `Plan / Task Queue`
- `Harness Control State`
- 当前任务相关的最小上下文

当前状态：

- `draft catalog target`

### 4. review-evidence-skill

职责：

- 汇总 code review、静态检查和结构评估结果
- 形成 review 证据面

主要依赖：

- `Gate Evidence`

当前状态：

- `draft catalog target`

### 5. test-evidence-skill

职责：

- 汇总测试执行结果与验收条件覆盖情况
- 形成 validation 证据面

主要依赖：

- `Gate Evidence`
- `Worktrack Contract`

当前状态：

- `draft catalog target`

### 6. rule-check-skill

职责：

- 检查项目规则、边界和治理约束
- 形成 policy 证据面

主要依赖：

- `Gate Evidence`
- repo governance rules

当前状态：

- `draft catalog target`

### 7. gate-skill

职责：

- 汇总 implementation / validation / policy 三类证据
- 生成当前 round 的 gate verdict

主要依赖：

- `Gate Evidence`

当前状态：

- `draft catalog target`

### 8. recover-worktrack-skill

职责：

- 在 gate fail 或 blocked 时，选择重试、回滚、拆分或刷新 baseline

主要依赖：

- `Gate Evidence`
- `Plan / Task Queue`
- `Harness Control State`

当前状态：

- `draft catalog target`

### 9. close-worktrack-skill

职责：

- 处理 `PR -> merge -> cleanup -> repo refresh handoff`
- 明确 closeout 后的下一层级动作

主要依赖：

- `Gate Evidence`
- `Harness Control State`

当前状态：

- `draft catalog target`
