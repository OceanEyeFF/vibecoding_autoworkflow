---
title: "Codex Memory Side 部署帮助"
status: active
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Codex Memory Side 部署帮助

> 目的：说明如何在本仓库把 `Memory Side` 的 canonical skill 通过 `.agents/skills/` 适配给 `Codex` / `OpenAI` 侧运行时，同时不把真相层搬离 `docs/knowledge/`。

## 一、适用范围

本页针对：

- 本仓库当前的 `Memory Side` 三个 skill
- 本机已验证版本：`codex-cli 0.116.0`
- repo-local backend adapter 资产，而不是全局 skill 市场

## 二、当前落点

当前落点分三层：

```text
docs/knowledge/
  memory-side/
    ...

toolchain/skills/aw-kernel/memory-side/
  knowledge-base-skill/
  context-routing-skill/
  writeback-cleanup-skill/

.agents/skills/
  knowledge-base-skill/
    SKILL.md
    agents/openai.yaml
  context-routing-skill/
    SKILL.md
    agents/openai.yaml
  writeback-cleanup-skill/
    SKILL.md
    agents/openai.yaml
```

职责边界：

- `docs/knowledge/` 是真相层
- `toolchain/skills/...` 是 canonical skill 层
- `.agents/skills/...` 是项目级 Codex backend adapter
- `agents/openai.yaml` 只承载 interface metadata，不承载 Memory Side 规则正文

## 三、部署原则

- 不把项目真相搬进 `.agents/skills/`
- 不复制 canonical docs 到 Codex adapter 目录
- 不把 `Prompt` 当成真相层
- 不把这三个 skill 膨胀成大 catalog
- 当前阶段只做最小可用 backend adapter

## 四、最小使用方式

如果你的 Codex 运行入口已经认识 repo-local `.agents/skills/`，直接调用对应 skill 即可。

如果你的当前 Codex 入口只认识全局 `$CODEX_HOME/skills`，不要把 `docs/knowledge/` 复制出去。更稳妥的做法是：

1. 仍以仓库内 `.agents/skills/<skill>/SKILL.md` 作为入口
2. 让启动脚本或外层 runner 指向这个 repo-local wrapper
3. 由 wrapper 回指 `toolchain/skills/...` 和 `docs/knowledge/...`

原因：

- 这些 wrapper 默认使用 repo-relative 路径
- 它们的目标是“把本仓库的 canonical skill 挂给 Codex”
- 它们不是为了脱离仓库独立分发

## 五、每个 Skill 的最小职责

| Skill | 目标 | 固定输出 |
|---|---|---|
| `knowledge-base-skill` | 判断 `Bootstrap` / `Adopt`，修主线入口 | 文档体系判断与最小修正集 |
| `context-routing-skill` | 为当前任务生成最小入口集合 | `Route Card` |
| `writeback-cleanup-skill` | 为当前任务结束时生成最小回写决策 | `Writeback Card` |

## 六、落地检查项

完成适配后，至少检查下面几件事：

- `.agents/skills/*/SKILL.md` 明确先读 canonical skill，再读 canonical docs
- `.agents/skills/*/agents/openai.yaml` 只保留显示名、短说明和默认提示
- skill 输出仍然使用 canonical docs 中定义的固定格式
- adapter 内没有复制 `Memory Side` 规则正文
- 同一 skill 在 Codex 和 Claude 上的能力边界一致

## 七、不要做的事

- 不要把 `.agents/skills/` 当成第二真相层
- 不要把 `Route Card` 写成执行计划
- 不要把 `Writeback Card` 写成长复盘
- 不要因为 Codex 偏代码入口，就改掉 canonical docs 的主线规则

## 八、相关文档

- [Memory Side Skill 与 Agent 模型](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skill-agent-model.md)
- [Memory Side 评测基线](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/analysis/memory-side-eval-baseline.md)
- [Knowledge Base canonical skill](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/knowledge-base-skill/SKILL.md)
- [Context Routing canonical skill](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/context-routing-skill/SKILL.md)
- [Writeback & Cleanup canonical skill](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/writeback-cleanup-skill/SKILL.md)
