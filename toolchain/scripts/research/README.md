# Research Scripts

本目录放最小研究动作入口，不承载研究产物本身。

当前入口：

- `run_claude_skill_eval.py`：对 `.exrepos/` 里的目标仓库运行 Claude 非交互 skill prompt 评估
- `tasks/`：研究用 prompt 模板

最小约束：

- 默认不落盘，避免把临时研究产物写进脚本目录
- 如需保存结果，显式传 `--save-dir`
- 输出目录应放在脚本目录之外

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
