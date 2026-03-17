---
title: "modules/ - 功能模块区"
status: archived
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# modules/ - 功能模块区

> 本目录按功能模块组织设计规格、实现文档和测试用例。

## 目录结构

```
modules/
├── README.md              # 本文件（模块索引）
├── gate/                  # 门禁模块
│   ├── README.md          # 模块概述
│   ├── spec/              # 规格文档
│   ├── impl/              # 实现文档
│   └── test/              # 测试用例
├── workflow/              # 工作流模块
├── verification/          # 验证模块
└── knowledge/             # 知识管理模块
```

## 模块定义

### 🚪 gate/ - 门禁模块

**职责**：任务入口筛选、阶段放行控制

| 组件 | 说明 | 关联 ROADMAP |
|------|------|--------------|
| Intake Gate (G0) | 入口规模评估，SizeScore 判定 | P0-1 |
| Spec Gate (G1) | 需求契约放行 | P0-3 |
| Evidence Gate (G3) | 证据验证放行 | P0-4 |
| Delivery Gate (G4) | 交付完整性检查 | P0-6 |

### 🔄 workflow/ - 工作流模块

**职责**：任务编排、阶段流转、回路控制

| 组件 | 说明 | 关联 ROADMAP |
|------|------|--------------|
| Level 0 Loop | 最多 3 次修复回路 | P0-5 |
| Goal Tracker | 目标列表持续更新 | P0-7 |
| 2-3-1 Orchestration | 需求-实现-交付编排 | - |

### ✅ verification/ - 验证模块

**职责**：证据收集、合规检查、诚实度保障

| 组件 | 说明 | 关联 ROADMAP |
|------|------|--------------|
| Evidence Collector | 最小证据三件套收集 | P0-4 |
| Compliance Checker | 约束符合度对照 | - |
| Honesty Guard | 诚实度门禁（无证据不宣称） | - |

### 📚 knowledge/ - 知识管理模块

**职责**：知识沉淀、检索增强、长期记忆

| 组件 | 说明 | 关联 ROADMAP |
|------|------|--------------|
| Knowledge Gate | 提交前知识更新门禁 | P0-8 |
| Doc Indexer | 文档元数据标准化 | P2-3 |
| BM25 Search | 本地全文检索 | P2-4 |

---

## 模块文档模板

每个模块目录应包含：

```markdown
# [模块名] - 模块概述

## 职责边界
模块负责什么，不负责什么。

## 核心组件
| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|

## 接口定义
与其他模块的交互接口。

## 实现状态
| 组件 | 状态 | 进度 | 关联文档 |
|------|------|------|----------|
```

---

## 与 toolchain/ 目录的关系

| 目录 | 职责 | 关系 |
|------|------|------|
| `toolchain/agents/` | Agent 定义（Prompt） | 实现层 |
| `toolchain/skills/` | Skill 编排（工作流） | 实现层 |
| `modules/` | 功能模块设计（规格） | 设计层 |

**设计 → 实现**：modules/ 中的规格文档指导 toolchain/ 中的 Agent/Skill 实现。

---

**版本**：v1.0
**创建日期**：2026-03-11
