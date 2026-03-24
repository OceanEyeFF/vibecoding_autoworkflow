---
title: "Memory Side Repo-local Prompt 改进闭环"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Memory Side Repo-local Prompt 改进闭环

> 目的：把当前仓库怎么用固定测试仓库、同一组关键问题和简单测试评分，持续改进 `Memory Side` 的 `Codex` / `Claude` prompt 与 wrapper 说明清楚。本页属于仓库实现层，不是跨仓库通用工作流合同。

先建立通用边界，再读本页：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)

## 一、当前优化对象

当前阶段不把这条闭环用在真相层上，而只用在 prompt、wrapper 和测试提示上。

可优化层：

- `docs/knowledge/memory-side/prompts/`
- `product/memory-side/adapters/`
- `toolchain/evals/memory-side/program.md`

执行面：

- `.agents/skills/`
- `.claude/skills/`

不可在测试中漂移的层：

- `docs/knowledge/` 仍然是项目真相层
- `product/memory-side/skills/` 仍然是 canonical skill 源码层
- 基准场景 ID 和 JSON schema 仍然是稳定测量面

## 二、最小实验回路

建议先用下面的固定回路：

1. 固定一个测试仓库和一组关键问题，例如 `CR-1` 或 `CR-2`
2. 固定基础测试提示、问题列表和测试记录格式
3. 更新 `product/` 下的 adapter 源码
4. 用 `adapter_deploy.py local` 同步到 `.agents/` 或 `.claude/`
5. 分别用 `codex` 与 `claude` 的无交互模式跑同一组问题
6. 保存测试记录并做测试评分，只保留回答更好的 prompt 修改

## 三、本仓库的最小 runner 落点

```text
toolchain/evals/memory-side/
  program.md          # 基础测试提示
  scenarios.json      # 关键问题列表
  scoring/            # 测试评分规则
    knowledge-base-rubric.json
    context-routing-rubric.json
    writeback-cleanup-rubric.json
  schemas/            # 测试记录格式
    knowledge-base-card.schema.json
    route-card.schema.json
    writeback-card.schema.json

toolchain/scripts/
  deploy/
    adapter_deploy.py
  research/
    memory_side_autoresearch.py
    memory_side_autoresearch_score.py
```

测试记录默认写到：

- `.autoworkflow/memory-side-autoresearch/`

## 四、最小使用方式

列出场景：

```bash
python3 toolchain/scripts/research/memory_side_autoresearch.py list
```

先把 adapter 同步到本地挂载点：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend all
```

做一次命令级 dry run：

```bash
python3 toolchain/scripts/research/memory_side_autoresearch.py run \
  --backend codex \
  --backend claude \
  --scenario CR-1 \
  --dry-run
```

## 五、当前阶段不做什么

- 不让测试直接修改 `docs/knowledge/`
- 不把 prompt 改进写成复杂 agent swarm
- 不在没有固定问题列表和评分规则的情况下比较输出好坏
- 不为了提分去放宽 truth boundary

如果后续要扩到更多主题或更多 backend，先按：

- [Repo-local Prompt 测试与改进流程](../eval-method-evolution.md)

## 六、相关文档

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side-eval-baseline.md)
- [Repo-local Prompt 测试与改进流程](../eval-method-evolution.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](../../operations/memory-side/codex-deployment-help.md)
- [Claude Memory Side Repo-local Adapter 适配帮助](../../operations/memory-side/claude-adaptation-help.md)
