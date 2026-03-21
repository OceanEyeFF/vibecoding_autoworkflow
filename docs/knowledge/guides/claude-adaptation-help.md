---
title: "Claude Memory Side 适配帮助"
status: active
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Claude Memory Side 适配帮助

> 目的：说明如何在本仓库把 `Memory Side` 的 canonical skill 通过 `.claude/skills/` 适配给 `Claude Code`，并保持与 Codex 同一套能力边界。

## 一、适用范围

本页针对：

- 本仓库当前的 `Memory Side` 三个 skill
- 本机已验证版本：`Claude Code 2.1.7`
- 项目级 skill 适配，不先展开复杂 subagents

## 二、当前落点

```text
docs/knowledge/
  memory-side/
    ...

toolchain/skills/aw-kernel/memory-side/
  knowledge-base-skill/
  context-routing-skill/
  writeback-cleanup-skill/

.claude/skills/
  knowledge-base-skill/
    SKILL.md
  context-routing-skill/
    SKILL.md
  writeback-cleanup-skill/
    SKILL.md
```

职责边界：

- `docs/knowledge/` 是真相层
- `toolchain/skills/...` 是 canonical skill 层
- `.claude/skills/...` 是项目级 Claude backend adapter

## 三、为什么先做项目级 Skill

当前阶段优先采用项目级 skill，而不是先做复杂 subagents，原因很简单：

- `Memory Side` 目前只需要 3 个稳定能力，不需要大 catalog
- `Skill` 更适合承载固定输入输出和限读边界
- `Claude` 端先把读取顺序和输出格式稳定住，比先扩编排更重要
- 这样才能保证和 Codex 同一套真相层、同一套能力边界

## 四、最小适配要求

每个 `.claude/skills/<skill>/SKILL.md` 都应做到：

1. 先回指 `toolchain/skills/aw-kernel/memory-side/<skill>/SKILL.md`
2. 再回指对应 `references/entrypoints.md`
3. 最后只读取必要的 `docs/knowledge/memory-side/...`
4. 明确说明它只是 backend adapter，不是真相层
5. 明确说明优先用项目级 skill，不先扩复杂 subagents

## 五、与 Codex 的对齐要求

Claude 侧必须和 Codex 侧保持同一套边界：

- 同样的 3 个 skill
- 同样的 canonical docs
- 同样的固定输出契约
- 同样不允许把规则正文塞进 adapter

允许的差异只有：

- 文档裁剪和读取节奏
- 是否显式强调先别启用 subagents
- skill frontmatter 的后端格式差异

## 六、Git 与忽略规则

本仓库当前只跟踪下面这三份 Claude skill 文件：

- `.claude/skills/knowledge-base-skill/SKILL.md`
- `.claude/skills/context-routing-skill/SKILL.md`
- `.claude/skills/writeback-cleanup-skill/SKILL.md`

其余 `.claude/` 内容仍保持本地化和忽略状态，避免把临时会话资产、日志或个人配置混进仓库。

## 七、落地检查项

完成适配后，至少检查下面几件事：

- `.claude/skills/*/SKILL.md` 先读 canonical skill，再读 canonical docs
- skill 内容没有复制 `Memory Side` 规则正文
- Claude 侧默认先走项目级 skill，而不是直接起复杂 subagents
- 三个 skill 的输出契约与 Codex 侧一致
- 修改项目真相时，落点仍然是 `docs/knowledge/`

## 八、不要做的事

- 不要把 `.claude/skills/` 当成第二真相层
- 不要让 Claude skill 私自持有项目知识副本
- 不要因为 Claude 更擅长长文档，就默认把整仓库都塞进上下文
- 不要先把这轮需求扩成复杂 subagent catalog

## 九、相关文档

- [Memory Side Skill 与 Agent 模型](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skill-agent-model.md)
- [Codex Memory Side 部署帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/codex-deployment-help.md)
- [Memory Side 评测基线](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/analysis/memory-side-eval-baseline.md)
