# ideas/ - 研究 Idea 区

> 本目录管理项目的创新想法、技术探索和研究方向。

## 目录结构

```
ideas/
├── README.md          # 本文件（Idea 管理指南）
├── active/            # 活跃研究中的 Idea（当前投入资源）
├── incubating/        # 孵化中的 Idea（待验证/探索）
└── archived/          # 已归档的 Idea（已实现/已放弃）
```

## Idea 生命周期

```
[灵感] → incubating/ → [验证可行] → active/ → [实现完成] → archived/
                            ↓
                      [验证不可行] → archived/（标记放弃）
```

## Idea 文档模板

```markdown
# IDEA-XXX: 标题

## 状态
- **当前阶段**：incubating / active / archived
- **创建日期**：YYYY-MM-DD
- **最后更新**：YYYY-MM-DD
- **负责人**：（可选）

## 问题陈述
描述要解决的问题或探索的方向。

## 核心思路
描述解决方案的核心思路。

## 可行性评估
- **技术可行性**：
- **收益预估**：
- **风险评估**：

## 验证计划
如何验证这个 Idea 是否可行？

## 实施路径（active 阶段填写）
如果进入实施，具体的步骤是什么？

## 归档原因（archived 阶段填写）
- 已实现：链接到实现的代码/文档
- 已放弃：放弃的原因
```

---

## 当前 Idea 清单

### active/（活跃研究中）

| Idea | 标题 | 状态 | 关联 |
|------|------|------|------|
| IDEA-006 | 强制数据访问 | 实施中 | design/01_DesignBaseLines/IDEA-006-implementation/ |

### incubating/（孵化中）

*（当前无孵化中的 Idea）*

### archived/（已归档）

| Idea | 标题 | 归档原因 |
|------|------|----------|
| IDEA-001 | 子 Agent 调用机制 | 已实现 |
| IDEA-002 | Agent 边界定义 | 已实现 |
| IDEA-003 | 权限守护 Agent | 部分实现 |
| IDEA-004 | 结构化交互协议 | 已实现 |
| IDEA-005 | 本地化指令缓存 | 待评估 |

---

## 与其他文档的关系

| 来源 | 流向 | 说明 |
|------|------|------|
| 日常开发中的灵感 | → `ideas/incubating/` | 记录待验证的想法 |
| 验证可行的 Idea | → `ideas/active/` | 开始投入资源研究 |
| 研究完成的 Idea | → `design/` + `planning/` | 进入设计和任务排期 |
| 放弃的 Idea | → `ideas/archived/` | 保留历史记录 |

---

**版本**：v1.0
**创建日期**：2026-03-11
