---
title: "文档索引"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# 文档索引

> 用来快速定位当前 `product / docs / toolchain` 主线，并区分源码层、知识层和本地挂载层。

## 最先读什么

| 目的 | 文档 |
|------|------|
| 先建立 docs 模块边界 | `docs/README.md` |
| 先建立根目录边界 | `docs/knowledge/foundations/root-directory-layering.md` |
| 先建立 Toolchain 边界 | `docs/knowledge/foundations/toolchain-layering.md` |
| 先建立 Memory Side 边界 | `docs/knowledge/memory-side/layer-boundary.md` |
| 了解 `Memory Side` 总览 | `docs/knowledge/memory-side/overview.md` |
| 了解 Skill / Agent 关系 | `docs/knowledge/memory-side/skill-agent-model.md` |
| 处理本地或全局部署 | `toolchain/scripts/deploy/adapter_deploy.py` |
| 处理本仓库评测 | `docs/analysis/memory-side/memory-side-eval-baseline.md` |

## 目录结构

```text
.
├── product/
├── docs/
├── toolchain/
├── .agents/
├── .claude/
└── repo meta files
```

## 当前文档边界

- `product/`：业务代码唯一源码根
- `docs/knowledge/`：canonical truth 与基础治理
- `docs/operations/`：本仓库部署说明
- `docs/analysis/`：本仓库评测与研究说明
- `docs/reference/`：外部参考资料
- `toolchain/`：部署、评测、测试工具
- `.agents/` 与 `.claude/`：repo-local deploy target，不是源码层

## 不要再这样用

- 不要把 `.agents/` 或 `.claude/` 当成业务源码层
- 不要把 repo-local wrapper 当成通用 skill 合同
- 不要把本仓库的 eval baseline 当成跨仓库默认标准
- 不要跳过 `layer-boundary.md` 直接进入某个 deploy target 目录
