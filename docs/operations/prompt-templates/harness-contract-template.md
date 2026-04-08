---
title: "Harness Contract 模板"
status: active
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Harness Contract 模板

> 说明：本文已降级为 compatibility shim。canonical source 已迁到 [harness-contract-shape](../../../product/harness-operations/skills/harness-contract-shape/references/prompt.md)。本页只保留旧路径兼容入口，不再定义主线语义。

## Canonical Source

- [harness-contract-shape/SKILL.md](../../../product/harness-operations/skills/harness-contract-shape/SKILL.md)
- [harness-contract-shape/references/prompt.md](../../../product/harness-operations/skills/harness-contract-shape/references/prompt.md)
- [harness-contract-shape/references/entrypoints.md](../../../product/harness-operations/skills/harness-contract-shape/references/entrypoints.md)
- [docs/knowledge/README.md](../../knowledge/README.md)

> 目的：为 repo-local harness state 和 contract 文件提供一个最小 JSON 结构样例。

## JSON 示例

```json
{
  "workflow_id": "${WORKFLOW_ID}",
  "workflow_type": "review-loop | task-list-workflow",
  "task_ref": "${TASK_SOURCE_REF}",
  "scope": {
    "in_scope": [
      "${SCOPE_INCLUDE}"
    ],
    "out_of_scope": [
      "${SCOPE_EXCLUDE}"
    ]
  },
  "gates": {
    "scope_gate": "pending",
    "spec_gate": "pending",
    "static_gate": "pending",
    "test_gate": "pending",
    "smoke_gate": "pending"
  },
  "risk_triage": {
    "blocking_risks": [],
    "rework_risks": []
  },
  "governance": {
    "rule": "pending",
    "folders": "pending",
    "document": "pending",
    "code": "pending",
    "overall": "pending",
    "improvement_suggestions": []
  },
  "status": "planning",
  "last_updated": "2026-04-03T00:00:00Z"
}
```

## 使用约束

- 本文档只提供与 canonical source 对齐的结构样例，不直接承接运行态文件
- 真实 state 和 contract 产物应落在 `.autoworkflow/`
- host-repo 的路径、gate 顺序和治理维度应通过 bindings 注入，而不是在 shim 中重新写死

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [Docs 文档治理基线](../../knowledge/foundations/docs-governance.md)
- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
