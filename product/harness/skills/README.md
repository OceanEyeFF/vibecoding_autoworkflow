# 调度器技能

`product/harness/skills/` 目录存放 `Harness` 调度器的标准可执行源文件。

当前阶段：

- 已落地的顶层入口是 [harness-skill/](./harness-skill/)：顶层监督入口
- 已落地的分派入口是 [dispatch-skills/](./dispatch-skills/)：`WorktrackScope` 下的限定范围分派与后备执行载体
- 已落地的通用执行载体：
  - [generic-worker-skill/](./generic-worker-skill/) — 接收限定范围 Prompt 的通用执行 worker
  - [doc-catch-up-worker-skill/](./doc-catch-up-worker-skill/) — 将已验证实现事实追平到正确文档层
- 已落地的 `RepoScope` 技能骨架：
  - [repo-status-skill/](./repo-status-skill/) — 代码仓库状态观察
  - [repo-whats-next-skill/](./repo-whats-next-skill/) — 代码仓库下一步判断
  - [repo-append-request-skill/](./repo-append-request-skill/) — 追加请求分类与路由
  - [repo-change-goal-skill/](./repo-change-goal-skill/) — 修改 Repo 目标
  - [repo-refresh-skill/](./repo-refresh-skill/) — 代码仓库刷新
- [init-milestone-skill/](./init-milestone-skill/) — Milestone 初始化/注册到 Pipeline
- [milestone-status-skill/](./milestone-status-skill/) — Milestone 状态观测/验收分析器
- 已落地的 `WorktrackScope` 技能骨架：
  - [init-worktrack-skill/](./init-worktrack-skill/) — 初始化工作追踪
  - [schedule-worktrack-skill/](./schedule-worktrack-skill/) — 调度工作追踪
  - [review-evidence-skill/](./review-evidence-skill/) — 审查证据
  - [test-evidence-skill/](./test-evidence-skill/) — 测试证据
  - [rule-check-skill/](./rule-check-skill/) — 规则检查
  - [gate-skill/](./gate-skill/) — 关卡判定
  - [recover-worktrack-skill/](./recover-worktrack-skill/) — 恢复工作追踪
  - [close-worktrack-skill/](./close-worktrack-skill/) — 关闭工作追踪
- 上游技能目录见 [../../../docs/harness/catalog/README.md](../../../docs/harness/catalog/README.md)
- 后续新增内容应从 `docs/harness/` 的操作员定义、工作流程与治理规则推导而来
- 不应先复制局部提示词，再反向让它生长出本体论

这里适合放：

- `Harness` 的操作员落地实现
- `Harness` 工作流程/配置的标准可执行源文件
- 最小必要的参考资料

## 技能目录布局

每个技能目录必须有 `SKILL.md`。下列子目录是当前允许的可选结构，只有在能被该技能稳定消费时才保留：

- `templates/`：技能执行时会复制、渲染或要求使用的模板
- `references/`：技能本体需要随包分发的短参考材料
- `scripts/`：技能私有辅助脚本；共享部署、测试或治理逻辑仍应放在 `toolchain/`
- `assets/`：技能私有静态资产

没有对应资产的技能应保持仅 `SKILL.md`，不需要补空目录。新增子目录类型前，先更新本页并补对应治理检查。

这里不适合放：

- 教义长文正文
- 后端包装器
- 代码仓库本地挂载结果
