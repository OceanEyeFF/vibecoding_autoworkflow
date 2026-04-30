---
name: doc-catch-up-worker-skill
description: 当工作追踪需要把已验证实现事实追平到正确文档层，减少后续开发引用过期上下文时，使用这个技能。
---

# 文档追平 Worker 技能

## 概览

本技能是 Harness 执行平面的文档追平 worker。它负责在每个 worktrack 的实现或验证事实稳定后，把事实同步到正确的长期文档层，减少后续开发因为引用旧文档、旧计数、旧路径或旧操作流程导致的错误。

本技能只追平已经验证的事实，不把推测、计划或未通过验证的中间结论写进 `docs/`。它不替代设计、review、gate 或 repo-goal 变更；它只做文档基线对齐。

## 何时使用

当满足以下任一条件时使用：

- 当前 worktrack 已改变 operator-facing 行为、部署流程、验证命令、skill set、目录结构或治理规则
- 实现已通过匹配验证，但长期文档仍引用旧路径、旧数量、旧命令或旧边界
- closeout 前需要确认文档是否与已验证事实一致
- 一个任务完成后需要为后续 worktrack 拉平上下文基线

不适用于：

- 写未验证的设计愿景
- 把研究草稿直接升格为长期真相
- 大范围改写 docs 叙事结构
- 替 `repo-change-goal-skill` 修改 Repo 级目标
- 替 `gate-skill` 做最终放行判断

## 输入约定

调用本技能时，任务 Prompt 至少应包含：

- `已验证事实`
- `触及实现或配置`
- `可能过期的文档范围`
- `应同步的 truth layer`
- `不应同步的内容`
- `验证证据`
- `完成信号`

默认 truth layer：

- 项目维护规则、governance、deploy、usage-help 写入 `docs/project-maintenance/`
- Harness doctrine、workflow family、artifact 与 adjacent-system 合同写入 `docs/harness/`
- 可执行合同写入 `product/` 或 `toolchain/`
- 不把长期事实写入 `.agents/`、`.claude/`、`.nav/`

## 工作流

1. 读取任务 Prompt、当前 diff 和验证证据，提取已验证事实。
2. 定位最小文档范围，优先更新承接层正文和最近入口页。
3. 查找旧路径、旧数量、旧命令、旧行为描述和旧准入条件。
4. 只写入已验证事实；对未验证事项保留为待办或不写入长期文档。
5. 更新文档 frontmatter 的 `updated` / `last_verified`，仅限本轮实际复核过的文档。
6. 运行与文档和治理面匹配的检查。
7. 返回文档追平报告，不输出 gate 判定。

## 硬约束

- 不要把未验证计划写成长期真相。
- 不要把 docs 当成临时 scratchpad。
- 不要在 `.agents/`、`.claude/` 或 `.nav/` 写长期事实。
- 不要为了同步一个事实而重写整篇文档。
- 不要改变实现以配合文档，除非任务 Prompt 明确要求并且仍在当前范围内。
- 不要更新未实际复核过的 `last_verified`。
- 不要引入双份主线；新增或接管文档作用域时必须同步最近入口页并清理旧入口。

## 预期输出

使用本技能时，返回一份 `文档追平报告`，至少包含：

- `已验证事实`
- `文档同步范围`
- `已更新文档`
- `未同步内容`
- `验证结果`
- `返回 Harness`

字段至少包括：

- `truth layer`
- `引用的验证证据`
- `旧上下文清理`
- `剩余文档风险`
- `建议下一动作`

## 资源

使用当前 worktrack 的实现 diff、验证命令输出、`AGENTS.md`、`docs/README.md`、`docs/project-maintenance/README.md`、`docs/harness/README.md` 和相关承接层文档作为输入。
