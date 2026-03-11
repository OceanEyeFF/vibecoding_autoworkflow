# 文档路由中心

> **本文档是项目的「路由器」**，帮助您快速找到所需文档和资源。

## 当前开发方向（小需求更稳）

- 范围与非目标：以 `docs/overview/guide.md` 为准；大任务必须先拆分后再进入流程。

---

## 🎯 快速导航

### 按角色快速进入

| 角色 | 入口 | 说明 |
|------|------|------|
| **首次进入** | [docs/overview/](docs/overview/) | 了解协作规则和项目方向 |
| **执行任务** | [docs/interfaces/](docs/interfaces/) | 查阅 Agent/Skill 接口 |
| **需要背景** | [docs/knowledge/](docs/knowledge/) | 分析洞察、参考资料 |

### 按任务类型快速定位

| 任务类型 | 首选工具 |
|---------|---------|
| **新功能开发** | [autodev Skill](toolchain/skills/aw-kernel/autodev/SKILL.md) |
| **代码分析** | [review Agent](toolchain/agents/aw-kernel/review.md) |
| **日志分析** | [logs Agent](toolchain/agents/aw-kernel/logs.md) |
| **清理重构** | [clean Agent](toolchain/agents/aw-kernel/clean.md) |
| **需求澄清** | [clarify Agent](toolchain/agents/aw-kernel/clarify.md) |
| **资料研究** | [knowledge-researcher Agent](toolchain/agents/aw-kernel/knowledge-researcher.md) |

---

## 📁 目录结构

```
AutoWorkflow/
├── 📄 README.md                    # 项目介绍与快速开始
├── 📄 INDEX.md                     # 文档路由中心（本文件）
│
├── 📁 docs/                        # 【文档中心】三层架构
│   ├── overview/                   # L1 概览层（粗颗粒）
│   │   ├── guide.md               # 项目宪法
│   │   └── roadmap.md             # 路线图
│   ├── modules/                    # L2 模块层（中颗粒）
│   ├── interfaces/                 # L3 接口层（细颗粒）
│   └── knowledge/                  # 知识库（横向支撑）
│       ├── analysis/              # 分析精华
│       ├── guides/                # 用户指南
│       └── reference/             # 参考资料
│
├── 📁 toolchain/                   # 【实现层】Agent/Skill 资源
│   ├── agents/aw-kernel/          # 6 个 Agents
│   ├── skills/aw-kernel/          # 2 个 Skills
│   └── scripts/                   # 安装脚本
│
├── 📁 planning/                    # 任务管理区
├── 📁 ideas/                       # 研究 Idea 区
└── 📁 archive/                     # 归档区
    ├── design/                    # 设计基线（已归档）
    └── modules-spec/              # 模块规格（已归档）
```

---

## ⚡ 安装

```bash
# Linux/macOS/WSL
bash toolchain/scripts/install-global.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File toolchain\scripts\install-global.ps1
```

详细选项：[toolchain/scripts/README.md](toolchain/scripts/README.md)

---

## 📖 阅读路径

**首次进入** → `docs/overview/guide.md` → `docs/overview/roadmap.md`

**执行任务** → `docs/interfaces/README.md` → 选择 Agent/Skill

**需要背景** → `docs/knowledge/analysis/` 或 `docs/knowledge/guides/`

---

**版本**：v2.0
**最后更新**：2026-03-11
**维护者**：浮浮酱
