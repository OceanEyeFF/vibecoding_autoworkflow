# Harness Skills

`product/harness/skills/` 预留给后续的 Harness canonical executable source。

当前阶段：

- 已落地的顶层入口是 [harness-skill/](./harness-skill/)：top-level supervisor
- 已落地的 dispatch 入口是 [dispatch-skills/](./dispatch-skills/)：`WorktrackScope` 下的 bounded dispatch 与 fallback subagent
- 已落地的 `RepoScope` skill skeleton：
  - [repo-status-skill/](./repo-status-skill/)
  - [repo-whats-next-skill/](./repo-whats-next-skill/)
  - [goal-change-control-skill/](./goal-change-control-skill/)
  - [repo-refresh-skill/](./repo-refresh-skill/)
- 已落地的 `WorktrackScope` skill skeleton：
  - [init-worktrack-skill/](./init-worktrack-skill/)
  - [schedule-worktrack-skill/](./schedule-worktrack-skill/)
  - [review-evidence-skill/](./review-evidence-skill/)
  - [test-evidence-skill/](./test-evidence-skill/)
  - [rule-check-skill/](./rule-check-skill/)
  - [gate-skill/](./gate-skill/)
  - [recover-worktrack-skill/](./recover-worktrack-skill/)
  - [close-worktrack-skill/](./close-worktrack-skill/)
- 上游 skill catalog 见 [../../../docs/harness/Skills/README.md](../../../docs/harness/Skills/README.md)
- 后续新增内容应从 `docs/harness/` 的 operator / workflow / governance truth 反推
- 不应先复制局部 prompt，再反向让它生长 ontology

这里适合放：

- Harness operator realization
- Harness workflow/profile 的 canonical executable source
- 最小 references

这里不适合放：

- doctrine 长文
- backend wrapper
- repo-local 挂载结果
