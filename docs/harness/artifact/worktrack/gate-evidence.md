---
title: "Gate Evidence"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# Gate Evidence

为状态转移裁决提供证据。最少应包含 review/validation/policy 三类证据面；review 下四路 SubAgent 覆盖状态（static-semantic-review、test-review、project-security-review、complexity-performance-review）；无法委派四路时的 fallback 原因；每条证据面的 freshness/缺失状态、残余风险与上游约束信号；gate intake readiness、verdict 和后续动作。
