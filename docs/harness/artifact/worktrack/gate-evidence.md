---
title: "Gate Evidence"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# Gate Evidence

为状态转移裁决提供证据，而不是只记录口头结论。

最少应包含：

- review / validation / policy 三类证据面
- review 证据面下的四路 SubAgent 覆盖状态：`static-semantic-review`（静态语义解释）、`test-review`（测试 review）、`project-security-review`（security review）、`complexity-performance-review`（代码复杂度和性能 review）
- 无法真实并行委派四路 review SubAgent 时的 fallback 原因
- 每条证据面的 freshness 或缺失状态
- 每条证据面的残余风险与上游约束信号
- gate intake readiness
- gate verdict
- 后续动作
