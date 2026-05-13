# Harness Artifact / Worktrack

`docs/harness/artifact/worktrack/` 承接 `WorktrackScope` 的局部状态转移对象。

当前入口：

- [contract.md](./contract.md)
- [plan-task-queue.md](./plan-task-queue.md)
- [gate-evidence.md](./gate-evidence.md)
- [dispatch-packet.md](./dispatch-packet.md)
- [debug-evidence.md](./debug-evidence.md)

## Closeout Record Policy

Worktrack `closeout_record` 不单独新增长期 artifact。它折叠在 `close-worktrack-skill` 的 `关闭工作追踪报告` 与 `代码仓库刷新交接` 中，并由 `repo-refresh-skill` 写入 repo 级 backlog / snapshot。

该结构至少覆盖：`worktrack_id`、`branch`、`base_ref`、`head_ref`、`merge_commit`、`pr`、`files_changed`、`acceptance_result`、`gate_verdict`、`evidence_refs`、`decision_refs`、`docs_updated`、`snapshot_refreshed`、`backlog_updated`、`cleanup_done`、`remaining_risks`、`next_repo_scope_action`。
