# Repo Governance Evaluation Bindings

## Required

- `${GOVERNANCE_EVAL_CMDS}`：宿主仓库的治理评分命令列表。
- `${GOVERNANCE_DIMENSIONS}`：宿主仓库治理收口维度列表。

## Optional

- `${HARNESS_CONTRACT_FILE}`：如果宿主仓库需要把评分结果回链到 harness contract，可注入当前 contract 路径。

## Runtime Placeholders

- `${TASK_SOURCE_REF}`：当前治理评估的对象或上下文来源。
