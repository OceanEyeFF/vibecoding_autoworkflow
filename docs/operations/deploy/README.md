# Deploy / Verify / Maintenance

`docs/operations/deploy/` 是当前仓库的 deploy / verify / maintenance 路径簇入口。它只负责把同类 runbook 收在一起，不替代 `docs/knowledge/` 的主线真相。

建议阅读顺序：

1. [Deploy Runbook](../deploy-runbook.md)
2. [Skill Deployment 维护流](../skill-deployment-maintenance.md)
3. [Review / Verify 承接位](../review-verify-handbook.md)
4. [路径与文档治理检查运行说明](../path-governance-checks.md)
5. [Branch / PR 治理规则](../branch-pr-governance.md)

下钻到 partition-specific usage help：

- [Memory Side usage help](../memory-side/README.md)
- [Task Interface usage help](../task-interface/README.md)

这个簇适合放：

- deploy target 和 verify 口径
- 维护循环与 drift 清理
- 路径治理检查
- 复核与收口流程

这个簇不适合放：

- canonical skill 本体
- repo-local execution template
- 业务源码或 deploy target 本身
