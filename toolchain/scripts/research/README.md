# Research Scripts

本目录放最小研究动作入口，不承载研究产物本身。

当前入口：

- `run_claude_skill_eval.py`：对 `.exrepos/` 里的目标仓库运行 Claude 非交互 skill prompt 评估
- `tasks/`：研究用 prompt 模板

最小约束：

- 默认不落盘，避免把临时研究产物写进脚本目录
- 如需保存结果，显式传 `--save-dir`
- 输出目录应放在脚本目录之外
- 如需连带 rubric 评分，显式传 `--with-eval`

示例：

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task context-routing
```

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo zustand \
  --task all \
  --save-dir /tmp/claude-skill-evals
```

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task context-routing \
  --with-eval \
  --save-dir /tmp/claude-skill-evals
```

落盘内容：

- `*.prompt.txt`：被测 skill 或 eval rubric 的最终 prompt
- `*.response.md`：Claude 输出
- `*.stderr.txt`：有 stderr 时才写
- `*.meta.json`：单次运行元数据
- `run-summary.json`：整轮汇总
