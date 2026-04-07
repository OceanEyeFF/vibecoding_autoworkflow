---
title: "Harness Contract 模板"
status: active
updated: 2026-04-07
owner: aw-kernel
last_verified: 2026-04-07
---
# Harness Contract 模板

> 目的：为 repo-local harness state 和 contract 文件提供一个最小 JSON 结构样例。

## JSON 示例

```json
{
  "workflow_id": "wf-2026-xxxx",
  "workflow_type": "review-loop | task-list-workflow",
  "task_ref": "<commit|pr|task-file>",
  "scope": {
    "in_scope": [
      "product/**",
      "docs/operations/prompt-templates/**",
      "toolchain/scripts/test/**"
    ],
    "out_of_scope": [
      ".autoworkflow/",
      ".spec-workflow/",
      ".serena/",
      ".nav/",
      ".agents/",
      ".claude/",
      ".opencode/"
    ]
  },
  "gates": {
    "scope": "pending",
    "static": "pending",
    "semantic": "pending",
    "white_box": "pending",
    "smoke": "pending"
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

- 本文档只提供结构样例，不直接承接运行态文件
- 真实 state 和 contract 产物应落在 `.autoworkflow/`

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [Docs 文档治理基线](../../knowledge/foundations/docs-governance.md)
- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
