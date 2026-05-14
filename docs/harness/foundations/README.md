# Harness Foundations

`docs/harness/foundations/` 承接 Harness 的指导思想、运行协议和跨 skill 的基础控制策略。

当前入口：

- [Harness指导思想.md](./Harness指导思想.md)：当前唯一的指导思想主文档
- [Harness运行协议.md](./Harness运行协议.md)：用于补上思路层与实践层差距的运行协议主草稿
- [runtime-protocol-chapter-plan.md](./runtime-protocol-chapter-plan.md)：`Harness运行协议.md` 的拆章计划，迁移完成前不替代当前协议入口
- [skill-common-constraints.md](./skill-common-constraints.md)：所有 Harness Skills 的公共约束定义（C-1 至 C-7），各 Skill 通过引用消费
- [dispatch-decision-policy.md](./dispatch-decision-policy.md)：`dispatch_mode: auto` 的执行载体选择策略

## Owner Boundaries

| 主题 | 权威入口 |
| --- | --- |
| Doctrine / 指导思想 | [Harness指导思想.md](./Harness指导思想.md) |
| Runtime protocol / 运行协议 | [Harness运行协议.md](./Harness运行协议.md) |
| Runtime protocol split plan | [runtime-protocol-chapter-plan.md](./runtime-protocol-chapter-plan.md) |
| Artifact contracts / 正式对象字段 | [../artifact/README.md](../artifact/README.md) |
| Catalog inventory / skill 清单 | [../catalog/README.md](../catalog/README.md) |
| Workflow policy / workflow family | [../workflow-families/README.md](../workflow-families/README.md) |
| Design analysis / 未升格方案分析 | [../design/](../design/) |
| Executable skill surfaces / 可执行技能源 | [../../../product/harness/skills/README.md](../../../product/harness/skills/README.md) |
