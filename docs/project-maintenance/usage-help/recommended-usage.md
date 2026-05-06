---
title: "Recommended Harness Usage"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Recommended Harness Usage

> 目的：给新 operator 一条从选择 backend、完成最小准备、初始化 Harness，到推进、验证和收尾的推荐路径。本页只讲使用顺序和边界，不重复 backend 安装细节。

## 一、选择 backend 路径

默认选择 `agents` backend，也就是 Codex 主路径。它面向当前 public/near-public trial，使用 repo-local `.agents/skills/`，并由 [codex.md](./codex.md) 承接具体 diagnose、update、verify 和 Codex manual run 细节。

只有在明确试用 Claude Code compatibility lane 时选择 `claude` backend。它使用 `.claude/skills/` 或 `~/.claude/skills`，完整差异见 [claude.md](./claude.md)。

## 二、先做 readiness / install check

在有真实工作的目标仓库里，先运行当前 backend 的只读检查，再决定是否执行安装或 destructive reinstall：

- `agents`：先看 [Codex Usage Help](./codex.md) 的 `diagnose --json` 和 `update --json` 路径，再执行 `update --yes` 与 `verify`
- `claude`：先看 [Claude Repo-local Usage Help](./claude.md) 的 package/local install 与 verify 路径

不要把 backend root override 指向敏感目录。已有内容的目标仓库先做 dry-run / diagnose，确认 target root、payload source 和 cleanup 范围都符合预期。

## 三、用清晰目标初始化 Harness

安装完成后，在目标仓库使用 `set-harness-goal-skill` 初始化 `.aw/`。目标描述要写成可执行的工作边界，而不是宽泛愿望：

- 说明要达成的最终结果
- 明确当前非目标和禁止触碰范围
- 给出可验证的验收标准
- 列出必须遵守的目录、命令、审批和写回约束

初始化只建立控制面和目标契约；不要在同一步混入 release、remote publish 或 package 变更。

## 四、通过有边界的请求和 worktrack 推进

后续推进时，把请求拆成可验收的 bounded worktrack。每轮请求应包含范围、允许改动的路径、验收标准、验证命令和禁止事项。

推荐节奏：

1. 先让 Harness 观察当前状态和下一步
2. 再分派一个明确的实现或文档任务
3. 完成后收集测试、审查和规则证据
4. 通过 gate 判定后再 closeout / writeback

不要把“顺手修所有相邻问题”作为默认授权。发现相邻风险时，应先记录并请求下一轮明确范围，除非它直接阻塞当前验收。

## 五、安全使用 SubAgents

SubAgent 适合做限定范围的实现、审查、测试证据或文档追平。给 SubAgent 的 prompt 应包含：

- 当前 worktrack 的目标和非目标
- 允许读写的路径
- 禁止触碰的文件、控制 artifacts 和外部动作
- 期望返回的证据格式
- 是否允许运行命令，以及哪些命令需要审批

不要让 SubAgent 自行扩大到 release、remote、package publish、全仓重构或 `.aw/` 控制面改写。SubAgent 产物回到主 Harness 后，仍需要主流程做 review、verify 和 gate。

## 六、验证、gate 与 closeout

每个 worktrack 完成后先跑与改动面匹配的验证。文档变更至少要人工对照 frontmatter、入口链接和相关 governance 规则；涉及路径、根目录、部署、adapter 或 closeout/gate 的变更再补对应脚本验证。

Gate 只应基于已收集证据判定是否通过。Closeout 负责合并已验证结果、整理写回、清理失效上下文，并把下一步状态交还给 repo scope。未验证结论不要写成长期项目真相。

## 七、明确审批边界

以下动作必须有明确审批，不能被普通实现请求、SubAgent prompt 或 closeout 暗含授权：

- release、dist-tag、npm/package publish
- 远程推送、开 PR、合并 PR、修改远端分支
- 对非临时或已有内容的 target 执行 destructive reinstall、删除目录、重写历史或大范围 cleanup
- 修改 backend command semantics、runtime adapters 或 package behavior
- 改写 `.aw/` 控制 artifacts、目标契约或 gate 结果

如果请求没有明确授权，Harness 应停在计划、诊断、dry-run、证据收集或等待审批状态。
