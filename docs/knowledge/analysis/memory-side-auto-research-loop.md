---
title: "Memory Side Auto Research Loop"
status: active
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Memory Side Auto Research Loop

> 目的：把 `karpathy/autoresearch` 的“固定程序 + 固定测量 + 反复试验”思路，改写成适用于本仓库 `Memory Side` Prompt / Skill adapter 优化的最小闭环。

## 一、为什么适合参考 autoresearch

`autoresearch` 的关键思想不是“让 AI 随便自我修改”，而是：

- 先定义一个可迭代的 `program.md`
- 固定一组输入场景
- 固定一组测量口径
- 每次只比较局部改动是否真的更好

项目入口见：

- https://github.com/karpathy/autoresearch

当前仓库可以借用这套方法，但优化对象不是 `train.py`，而是：

- `Memory Side` 的 Prompt
- Codex / Claude 的 repo-local skill adapter
- 任务前后上下文维护的输出稳定性

## 二、本仓库里的优化对象

当前阶段不把 `Auto Research` 用在真相层上，而只用在适配层上。

可优化层：

- `docs/knowledge/memory-side/prompts/`
- `.agents/skills/`
- `.claude/skills/`
- `toolchain/evals/memory-side/program.md`

不可在实验中漂移的层：

- `docs/knowledge/` 仍然是项目真相层
- `toolchain/skills/aw-kernel/memory-side/` 仍然是 canonical skill 层
- 基准场景 ID 和 JSON schema 仍然是稳定测量面

## 三、最适合先跑的场景

最适合先做的是 `task-entry-agent` 侧，也就是：

- `knowledge-base-skill`
- `context-routing-skill`

原因：

- 输入更稳定
- 输出结构更固定
- 反馈更快
- 不需要真正修改仓库文件就能比较结果

`writeback-cleanup-skill` 也可以进入基线，但应排在第二阶段，因为它更依赖“本轮到底改了什么、验证了什么”的真实上下文。

## 四、核心问题清单

`Auto Research` 不是泛泛优化提示词，而是持续围绕同一组核心问题打磨。

### 1. Agent 层问题

- 当前任务是不是被正确识别为 `entry` 还是 `closeout`
- 当前阶段有没有调用错误的 skill
- 当前阶段有没有把结果写成自由发挥，而不是固定 contract
- 当前阶段遇到不确定性时，有没有收缩结论而不是假装知道

### 2. Knowledge Base Skill 问题

- 是否正确判断 `Bootstrap` / `Adopt`
- 是否正确区分 `Core Truth`、`Operational Truth`、`Exploratory Records`、`Archive`
- 是否只提最小入口修补，而不是大改文档体系
- 是否避免把 `ideas` / `archive` 提升为主线

### 3. Context Routing Skill 问题

- 是否生成最小 `Route Card`
- `read_first` 是否足够小且足够准
- `code_entry` 是否精确到能开工
- `do_not_read_yet` 是否真的起到降噪作用
- 是否把 `Route Card` 错写成执行计划

### 4. Writeback Cleanup Skill 问题

- 是否只写回已验证事实
- 是否把内容写回到正确层级
- 是否明确列出 `do_not_write_back`
- 是否给出足够的 `verification_basis`
- 是否把 cleanup 用于降噪，而不是误删历史

### 5. Backend Parity 问题

- Codex 和 Claude 是否读取了同一套 canonical docs
- Codex 和 Claude 是否仍保持同一能力边界
- 后端差异是否只体现在表达和节奏，而不是规则本身
- adapter 是否开始偷偷持有项目真相

## 五、最小实验回路

建议先用下面的固定回路：

1. 选择一个稳定场景，例如 `CR-1` 或 `CR-2`
2. 固定 `program.md`、场景定义和输出 schema
3. 分别用 `codex` 与 `claude` 的无交互模式跑一轮
4. 保存原始输出、解析后 JSON、命令元数据和耗时
5. 用同一套 rubric 判断是否更好
6. 只有当新版本在开发场景和保留场景都更稳时，才保留修改

## 六、本仓库的最小 runner 落点

本仓库当前提供的最小资产是：

```text
toolchain/evals/memory-side/
  program.md
  scenarios.json
  scoring/
    context-routing-rubric.json
  schemas/
    knowledge-base-card.schema.json
    route-card.schema.json
    writeback-card.schema.json

toolchain/scripts/
  memory_side_autoresearch.py
  memory_side_autoresearch_score.py
```

用途：

- `program.md` 是可迭代的研究程序
- `scenarios.json` 是固定 benchmark 输入
- `scoring/context-routing-rubric.json` 是 `CR-1` / `CR-2` 共用的自动评分规则
- `schemas/` 约束输出结构
- `memory_side_autoresearch.py` 用本机 `codex` / `claude` 无交互模式执行场景
- `memory_side_autoresearch_score.py` 读取 run 结果并产出自动评分

运行产物默认写到：

- `.autoworkflow/memory-side-autoresearch/`

## 七、当前无交互执行方式

本机在 `2026-03-21` 验证过的命令入口是：

- `codex exec`
- `claude -p`

runner 里的默认策略是：

- `codex` 用只读沙箱和 `--output-schema`
- `claude` 用 `-p`、`--json-schema`、`--permission-mode dontAsk`
- 两边都限制在“评测只读模式”，不允许编辑文件

## 八、最小使用方式

列出场景：

```bash
python3 toolchain/scripts/memory_side_autoresearch.py list
```

做一次命令级 dry run：

```bash
python3 toolchain/scripts/memory_side_autoresearch.py run \
  --backend codex \
  --backend claude \
  --scenario CR-1 \
  --dry-run
```

真正执行一个场景：

```bash
python3 toolchain/scripts/memory_side_autoresearch.py run \
  --backend codex \
  --scenario CR-2 \
  --model gpt-5.4
```

给最新一轮 `CR-1` 自动打分：

```bash
python3 toolchain/scripts/memory_side_autoresearch_score.py \
  --latest \
  --backend codex \
  --scenario CR-1 \
  --write-score
```

## 九、当前阶段不做什么

- 不让 benchmark 直接修改 `docs/knowledge/`
- 不把 prompt 优化直接扩成复杂 agent swarm
- 不在没有固定 schema 的情况下比较输出好坏
- 不为了提分去放宽 truth boundary
- 不把整个 `Flow Side` 拉进第一阶段 benchmark

## 十、相关文档

- [Memory Side Adapter 评测基线](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/analysis/memory-side-eval-baseline.md)
- [Memory Side Skill 与 Agent 模型](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skill-agent-model.md)
- [Codex Memory Side 部署帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/codex-deployment-help.md)
- [Claude Memory Side 适配帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/claude-adaptation-help.md)
