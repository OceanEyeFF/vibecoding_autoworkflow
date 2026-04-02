---
title: "Autoresearch closeout cleanup and retained index"
status: active
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch closeout cleanup and retained index

> 目的：记录本轮 `G-105` 的最小真实清理结果，并为 `G-301` 提供只登记明确保留对象的 retained index。

## 1. Cleanup record

Only objects covered by the current artifact hygiene rules were changed.

| Action | Object | Reason | Recoverability | Judged by |
| --- | --- | --- | --- |
| delete | `.autoworkflow/autoresearch/manual-cr-codex-loop-3round-r000001-m000642/worktrees` | Empty scratch directory under an active retained run; hygiene rule marks `worktrees/` as delete. | Recreate by re-materializing the run or candidate worktree. | Current closeout workflow executor, under `docs/operations/autoresearch-artifact-hygiene.md` and `docs/operations/autoresearch-closeout-decision-rules.md` owned by `aw-kernel`. |
| delete | `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/worktrees` | Empty scratch directory under an active retained run; hygiene rule marks `worktrees/` as delete. | Recreate by re-materializing the run or candidate worktree. | Current closeout workflow executor, under `docs/operations/autoresearch-artifact-hygiene.md` and `docs/operations/autoresearch-closeout-decision-rules.md` owned by `aw-kernel`. |
| delete | `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/acceptance-worktrees` | Empty acceptance scratch directory; hygiene rule marks `acceptance-worktrees/` as delete. | Recreate by rerunning acceptance materialization. | Current closeout workflow executor, under `docs/operations/autoresearch-artifact-hygiene.md` and `docs/operations/autoresearch-closeout-decision-rules.md` owned by `aw-kernel`. |
| delete | `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/acceptance-runs/acceptance-run.log` | Temporary control/log file; hygiene rule marks `acceptance-run.log` as delete. | Recreate by rerunning the acceptance command. | Current closeout workflow executor, under `docs/operations/autoresearch-artifact-hygiene.md` and `docs/operations/autoresearch-closeout-decision-rules.md` owned by `aw-kernel`. |
| delete | `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/acceptance-runs/acceptance-run.pid` | Temporary control file; hygiene rule marks `acceptance-run.pid` as delete. | Recreate by rerunning the acceptance command. | Current closeout workflow executor, under `docs/operations/autoresearch-artifact-hygiene.md` and `docs/operations/autoresearch-closeout-decision-rules.md` owned by `aw-kernel`. |
| delete | `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/acceptance-runs/acceptance-run.sh` | Temporary control script; hygiene rule marks `acceptance-run.sh` as delete. | Recreate by regenerating the launcher script. | Current closeout workflow executor, under `docs/operations/autoresearch-artifact-hygiene.md` and `docs/operations/autoresearch-closeout-decision-rules.md` owned by `aw-kernel`. |

No archive batch content, manual run definition package, or non-covered object was modified.

## 2. Retained index

This index only lists objects explicitly retained for the current closeout scope.

| Object | Why it is retained |
| --- | --- |
| `.autoworkflow/autoresearch/manual-cr-codex-loop-3round-r000001-m000642/` | Representative retained run root; still used for closeout evidence and runtime residue checks. |
| `.autoworkflow/autoresearch/manual-cr-codex-loop-6-3-3-r000001-m046830/` | Representative retained run root; still used for closeout evidence and runtime residue checks. |
| `.autoworkflow/manual-runs/context-routing-codex-loop-3round/` | Definition package for a retained run lineage and rerun baseline. |
| `.autoworkflow/manual-runs/context-routing-codex-loop-6-3-3/` | Definition package for a retained run lineage and rerun baseline. |
| `.autoworkflow/manual-runs/context-routing-exrepos-codex-first-pass/` | Definition package kept as a rerun baseline for related lineage. |
| `.autoworkflow/manual-runs/context-routing-typer-claude-3round-observe/` | Definition package kept as a rerun baseline for related lineage. |
| `.autoworkflow/manual-runs/minimal-context-routing-typer-claude/` | Minimal definition package retained as a compact rerun baseline. |
| `.autoworkflow/manual-runs/.run-id-state/` | Repo-local run id allocator state required by the retained/manual run contract. |

## 3. Scope guard

- This document is intentionally narrow.
- If a future object needs retention and is not listed here, it must be justified separately and written back through the closeout workflow.
- If a future object is only a scratch file or empty directory, the default remains `delete` unless a documented exception applies.
