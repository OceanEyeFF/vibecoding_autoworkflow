---
title: "Research 评测观测与输出规范"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Research 评测观测与输出规范

> 目的：固定 Research/Eval 的输出边界、运行记录口径与评分结果规范，确保多 backend 下的评测可复用、可对比、可汇总。

## 一、输出边界与落盘规则

当前已验证的合理做法是：

- 显式传 `--save-dir`
- 把结果写到外部目录，例如 `/tmp/...`

后续如果要沉淀到 repo-local state，也应落到状态层，而不是 `toolchain/` 本体。

## 二、原始输出与最终回答必须分离

这轮研究已经验证出一个必要约束：

- runner 必须显式区分 `raw stdout/stderr` 与 `final message`

原因：

- Claude 输出可能混入 chatter
- Codex 更适合走 `stdin prompt + output file final message`
- 若不拆开原始输出与最终回答，后续多 backend 汇总会变脆

## 三、计时与运行记录口径

现有实现需要尽快固定的基础约束：

- `elapsed_seconds` 不应继续用 wall-clock 差值
- 后续应改为基于 `time.perf_counter()` 计算

## 四、评分结果的结构化规范

当前自然语言抓分只适合研究期，后续准入方向应是结构化 JSON：

- judge 输出受 schema 约束的 JSON
- `toolchain/evals/fixtures/schemas/` 提供 schema
- runner 直接汇总结构化结果

示例：

```json
{
  "skill": "context-routing",
  "repo": "typer",
  "backend": "codex",
  "judge_backend": "claude",
  "scores": {
    "path_contraction": 3,
    "entry_point_identification": 2,
    "avoidance_of_over_scanning": 3,
    "execution_usability": 2
  },
  "total_score": 10,
  "max_score": 12,
  "overall": "Okay",
  "key_issues": ["..."],
  "key_strengths": ["..."]
}
```

## 五、评分提取与回退策略

建议的准入路径：

- Claude judge 优先输出受 schema 约束的 JSON
- Codex judge 可优先走 `--output-schema`
- OpenCode 若暂时不支持 schema，再退回 text + parser

## 六、相关文档

- [Research 评测契约与边界](./research-eval-contracts.md)
- [Research CLI 指令](../operations/research-cli-help.md)
- [toolchain/evals/README.md](../../toolchain/evals/README.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
