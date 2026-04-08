# Harness Contract Template

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
