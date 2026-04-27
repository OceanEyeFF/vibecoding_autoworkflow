# Worktrack Contract

> 这是 `.aw/worktrack/contract.md` 的模板来源，用来填写单个 worktrack 的局部状态转移合同。最终内容应与 `docs/harness/artifact/worktrack/contract.md` 的定义一致。

## Metadata

- worktrack_id:
- branch:
- baseline_branch:
- baseline_ref:
- owner:
- updated:
- contract_status:

## Node Type

> 从 Goal Charter 的 Engineering Node Map 绑定，决定本 worktrack 的基线策略与判定标准。

- type:
- source_from_goal_charter:
- baseline_form:
- merge_required:
- gate_criteria:
- if_interrupted_strategy:

## Execution Policy

> 控制本 worktrack 的执行载体选择。`auto` 默认优先委派 SubAgent；`delegated` 强制要求真实委派；`current-carrier` 明确选择当前载体执行。默认 scaffold 中 `.aw/control-state.md` 的 `subagent_dispatch_mode_override_scope: worktrack-contract-primary` 会让本字段优先生效；只有 control-state 显式改为 `global-override` 时，`subagent_dispatch_mode` 才作为上层覆盖。若因权限边界、运行时缺口或 `dispatch package unsafe` 不能委派，必须记录 `runtime fallback`。

- runtime_dispatch_mode: auto
- dispatch_mode_source: worktrack-contract
- allowed_values: auto / delegated / current-carrier
- fallback_reason_required: yes

## Task Goal

- 

## Scope

- 

## Non-Goals

- 

## Impacted Modules

- 

## Planned Next State

- 

## Acceptance Criteria

- 

## Constraints

- 

## Verification Requirements

- 

## Rollback Conditions

- 

## Notes

- 
