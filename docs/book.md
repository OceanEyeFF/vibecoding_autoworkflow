---
title: "Docs Book Spine"
status: active
updated: 2026-05-14
owner: aw-kernel
last_verified: 2026-05-14
---
# Docs Book Spine

`docs/book.md` 是 `docs/` 的 canonical book-style spine：它定义当前版本中实际存在的完整阅读顺序、章节边界、文档分组关系和路径维护规则。`docs/README.md` 只做入口导航；具体规则正文仍以对应章节内的承接文档为准。

Owner：`aw-kernel`。边界：只覆盖当前 `docs/` 文档分层与阅读路线，不替代 `AGENTS.md` 的 agent boot 规则，不承接 `product/` 源码合同或 `toolchain/` 脚本合同，不把未来迁移计划或后续 Worktrack seed 写成 docs truth。

## How To Read

1. 先读 [docs/README.md](./README.md) 确认 `docs/` 的入口定位。
2. 回到本页，按 [Full Reading Order](#full-reading-order) 从上到下阅读。每个链接都是当前书目中的一个节点。
3. 需要执行任务时，停在最近章节入口，不要继续扩读不相关章节。
4. 新增、移动、删除或重命名文档时，先按 [Docs Path Maintenance](#docs-path-maintenance) 同步本页、最近章节入口和旧路径引用。

## Full Reading Order

### 0. Orientation

1. [docs/README.md](./README.md)

### 1. Project Maintenance

1. [project-maintenance/README.md](./project-maintenance/README.md)
2. [project-maintenance/foundations/README.md](./project-maintenance/foundations/README.md)
3. [project-maintenance/foundations/root-directory-layering.md](./project-maintenance/foundations/root-directory-layering.md)
4. [project-maintenance/governance/README.md](./project-maintenance/governance/README.md)
5. [project-maintenance/governance/review-verify-handbook.md](./project-maintenance/governance/review-verify-handbook.md)
6. [project-maintenance/governance/path-governance-checks.md](./project-maintenance/governance/path-governance-checks.md)
7. [project-maintenance/governance/global-language-style.md](./project-maintenance/governance/global-language-style.md)
8. [project-maintenance/governance/branch-pr-governance.md](./project-maintenance/governance/branch-pr-governance.md)
9. [project-maintenance/governance/aw-installer-release-operation-model.md](./project-maintenance/governance/aw-installer-release-operation-model.md)
10. [project-maintenance/governance/aw-installer-release-channel-governance.md](./project-maintenance/governance/aw-installer-release-channel-governance.md)
11. [project-maintenance/governance/aw-installer-release-standard-flow.md](./project-maintenance/governance/aw-installer-release-standard-flow.md)
12. [project-maintenance/governance/aw-installer-pre-publish-governance.md](./project-maintenance/governance/aw-installer-pre-publish-governance.md)
13. [project-maintenance/governance/aw-installer-external-trial-governance.md](./project-maintenance/governance/aw-installer-external-trial-governance.md)
14. [project-maintenance/deploy/README.md](./project-maintenance/deploy/README.md)
15. [project-maintenance/deploy/distribution-entrypoint-contract.md](./project-maintenance/deploy/distribution-entrypoint-contract.md)
16. [project-maintenance/deploy/deploy-mapping-spec.md](./project-maintenance/deploy/deploy-mapping-spec.md)
17. [project-maintenance/deploy/deploy-runbook.md](./project-maintenance/deploy/deploy-runbook.md)
18. [project-maintenance/deploy/skill-deployment-maintenance.md](./project-maintenance/deploy/skill-deployment-maintenance.md)
19. [project-maintenance/deploy/payload-provenance-trust-boundary.md](./project-maintenance/deploy/payload-provenance-trust-boundary.md)
20. [project-maintenance/deploy/existing-code-adoption.md](./project-maintenance/deploy/existing-code-adoption.md)
21. [project-maintenance/testing/README.md](./project-maintenance/testing/README.md)
22. [project-maintenance/testing/python-script-test-execution.md](./project-maintenance/testing/python-script-test-execution.md)
23. [project-maintenance/testing/npx-command-test-execution.md](./project-maintenance/testing/npx-command-test-execution.md)
24. [project-maintenance/testing/codex-post-deploy-behavior-tests.md](./project-maintenance/testing/codex-post-deploy-behavior-tests.md)
25. [project-maintenance/testing/claude-post-deploy-behavior-tests.md](./project-maintenance/testing/claude-post-deploy-behavior-tests.md)
26. [project-maintenance/usage-help/README.md](./project-maintenance/usage-help/README.md)
27. [project-maintenance/usage-help/recommended-usage.md](./project-maintenance/usage-help/recommended-usage.md)
28. [project-maintenance/usage-help/init-greenfield.md](./project-maintenance/usage-help/init-greenfield.md)
29. [project-maintenance/usage-help/init-with-code.md](./project-maintenance/usage-help/init-with-code.md)
30. [project-maintenance/usage-help/goal-change-guide.md](./project-maintenance/usage-help/goal-change-guide.md)
31. [project-maintenance/usage-help/codex.md](./project-maintenance/usage-help/codex.md)
32. [project-maintenance/usage-help/claude.md](./project-maintenance/usage-help/claude.md)
33. [project-maintenance/repo-onboarding.md](./project-maintenance/repo-onboarding.md)

### 2. Harness

1. [harness/README.md](./harness/README.md)
2. [harness/foundations/README.md](./harness/foundations/README.md)
3. [harness/foundations/Harness指导思想.md](./harness/foundations/Harness指导思想.md)
4. [harness/foundations/Harness运行协议.md](./harness/foundations/Harness运行协议.md)
5. [harness/foundations/runtime-protocol-chapter-plan.md](./harness/foundations/runtime-protocol-chapter-plan.md)
6. [harness/foundations/dispatch-decision-policy.md](./harness/foundations/dispatch-decision-policy.md)
7. [harness/foundations/skill-common-constraints.md](./harness/foundations/skill-common-constraints.md)
8. [harness/scope/README.md](./harness/scope/README.md)
9. [harness/scope/state-loop.md](./harness/scope/state-loop.md)
10. [harness/artifact/README.md](./harness/artifact/README.md)
11. [harness/artifact/standard-fields.md](./harness/artifact/standard-fields.md)
12. [harness/artifact/repo/README.md](./harness/artifact/repo/README.md)
13. [harness/artifact/repo/discovery-input.md](./harness/artifact/repo/discovery-input.md)
14. [harness/artifact/repo/goal-charter.md](./harness/artifact/repo/goal-charter.md)
15. [harness/artifact/repo/repo-analysis.md](./harness/artifact/repo/repo-analysis.md)
16. [harness/artifact/repo/snapshot-status.md](./harness/artifact/repo/snapshot-status.md)
17. [harness/artifact/repo/worktrack-backlog.md](./harness/artifact/repo/worktrack-backlog.md)
18. [harness/artifact/repo/milestone-backlog.md](./harness/artifact/repo/milestone-backlog.md)
19. [harness/artifact/repo/decision-log.md](./harness/artifact/repo/decision-log.md)
20. [harness/artifact/worktrack/README.md](./harness/artifact/worktrack/README.md)
21. [harness/artifact/worktrack/contract.md](./harness/artifact/worktrack/contract.md)
22. [harness/artifact/worktrack/plan-task-queue.md](./harness/artifact/worktrack/plan-task-queue.md)
23. [harness/artifact/worktrack/dispatch-packet.md](./harness/artifact/worktrack/dispatch-packet.md)
24. [harness/artifact/worktrack/gate-evidence.md](./harness/artifact/worktrack/gate-evidence.md)
25. [harness/artifact/worktrack/debug-evidence.md](./harness/artifact/worktrack/debug-evidence.md)
26. [harness/artifact/control/README.md](./harness/artifact/control/README.md)
27. [harness/artifact/control/control-state.md](./harness/artifact/control/control-state.md)
28. [harness/artifact/control/milestone.md](./harness/artifact/control/milestone.md)
29. [harness/artifact/control/append-request.md](./harness/artifact/control/append-request.md)
30. [harness/artifact/control/goal-change-request.md](./harness/artifact/control/goal-change-request.md)
31. [harness/artifact/control/node-type-registry.md](./harness/artifact/control/node-type-registry.md)
32. [harness/catalog/README.md](./harness/catalog/README.md)
33. [harness/catalog/supervisor.md](./harness/catalog/supervisor.md)
34. [harness/catalog/repo.md](./harness/catalog/repo.md)
35. [harness/catalog/worktrack.md](./harness/catalog/worktrack.md)
36. [harness/catalog/init-milestone-skill.md](./harness/catalog/init-milestone-skill.md)
37. [harness/catalog/milestone-status-skill.md](./harness/catalog/milestone-status-skill.md)
38. [harness/catalog/skill-impact-matrix.md](./harness/catalog/skill-impact-matrix.md)
39. [harness/workflow-families/README.md](./harness/workflow-families/README.md)
40. [harness/workflow-families/repo-evolution/README.md](./harness/workflow-families/repo-evolution/README.md)
41. [harness/workflow-families/repo-evolution/standard-worktrack.md](./harness/workflow-families/repo-evolution/standard-worktrack.md)
42. [harness/workflow-families/repo-evolution/append-request-routing.md](./harness/workflow-families/repo-evolution/append-request-routing.md)
43. [harness/workflow-families/repo-evolution/policy-profiles.md](./harness/workflow-families/repo-evolution/policy-profiles.md)
44. [harness/design/skills-handback-improvements.md](./harness/design/skills-handback-improvements.md)

## Chapter Boundaries

### 1. Project Maintenance

`docs/project-maintenance/` 承接 operator-facing 项目维护：根目录分层、review/verify/gate 治理、部署 runbook、测试入口、backend usage help 和 repo onboarding。

新文档属于这里，当它回答的是“这个仓库如何维护、验证、部署、接入或使用”。涉及长期治理规则时，优先进入 `project-maintenance/governance/`；涉及目录边界时，优先进入 `project-maintenance/foundations/`；涉及命令运行或 smoke 时，优先进入 `project-maintenance/testing/`。

### 2. Harness

`docs/harness/` 承接 Harness-first 主线：doctrine、runtime protocol、scope、artifact contract、skill catalog、workflow families 和设计分析。

Harness 子章节放置规则：

- `harness/foundations/`：Harness 指导思想、运行协议、跨 skill 公共约束和执行载体选择策略。
- `harness/scope/`：`RepoScope`、`WorktrackScope` 与状态闭环。
- `harness/artifact/`：Harness 正式对象合同，包括 repo/worktrack/control artifact 与标准字段。
- `harness/catalog/`：Codex 语境下的 skill catalog、控制层级映射和 skill 影响矩阵；可执行源仍归 `product/harness/skills/`。
- `harness/workflow-families/`：可复用流程族、policy profile 和标准 worktrack 路线。
- `harness/design/`：尚未升格为 doctrine、artifact contract 或 workflow family 的 Harness 设计方案与变更分析。

新文档属于这里，当它回答的是“Harness 如何思考、调度、记录证据、判定、交接或沉淀 workflow”。已验证并需要长期承接的设计，应升格到对应 foundations、artifact 或 workflow family 章节。

## Grouping And Relationships

- `README.md` 是局部章节入口，只解释该目录的定位和最近路线；不要在 README 中复制完整规则正文。
- `docs/book.md` 是当前版本的全量书目和阅读顺序，必须直接链接 `docs/` 下除自身外的每个当前 markdown 文件。
- 承接文档保存规则正文；book 只写章节边界、顺序、分组关系和维护规则。
- docs truth surface 只描述当前已经存在的文档拓扑、owner 和维护规则；未来迁移计划、后续 Worktrack seed 或尚未落地的重构切片不得作为长期 docs 正文保留。
- 一个主题只能有一个稳定主线 owner。若两个章节都需要引用同一主题，非 owner 章节只链接到 owner，不复制正文。
- 跨章节依赖要在相关文档中用相对链接表达，不能只依靠文件路径相邻或读者搜索。

## Placement Checklist

新增或移动文档前，按顺序判断：

1. 它是维护/治理/部署/测试/usage 吗？放 `project-maintenance/`。
2. 它是 Harness doctrine、runtime、artifact、catalog、workflow 或设计吗？放 `harness/` 的最近子章节。
3. 如果它无法归入当前存在的两个章节，不要把它写入 `docs/`；先明确当前 owner 和实际承接路径，再同步最近入口和本页。

新增正文文档后，同步更新最近的 `README.md` 入口和本页的 Full Reading Order；若接管了新的稳定边界，也要清理旧入口，避免双份主线。

## Docs Path Maintenance

当 `docs/` 下的 markdown 文件新增、移动、重命名、删除或改 owner 时，维护顺序如下：

1. 先确定 owner 章节和最近 `README.md`，避免把新正文直接散落在目录里。
2. 更新最近章节 `README.md` 的局部入口或迁移说明。
3. 更新本页的 Full Reading Order，确保除 `docs/book.md` 自身外的每个当前 docs markdown 文件都有直接有序链接。
4. 修复旧路径引用；若旧入口仍有读者价值，写清迁移目标。
5. 运行 `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py`，确认 book reachability 和 explicit reading-order coverage 均通过。
6. 若变更影响 review/verify、路径治理或 closeout 规则，同步更新 `docs/project-maintenance/governance/` 的对应文档。

删除或重命名文档时，不只删除文件；必须同步删除或替换本页、最近 README、相关正文和治理文档中的旧链接。
