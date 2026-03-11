# docs/ - 文档中心

> 本目录采用三层架构组织项目文档，从粗到细提供不同粒度的信息。

## 三层架构

```
docs/
├── overview/       # L1 概览层 - 粗颗粒度，面向首次进入
├── modules/        # L2 模块层 - 中等颗粒度，面向模块设计
├── interfaces/     # L3 接口层 - 细颗粒度，面向接口使用
└── knowledge/      # 知识库 - 横向支撑，背景与参考
```

## 快速导航

| 目录 | 粒度 | 何时读 | 入口 |
|------|------|--------|------|
| [overview/](overview/) | 粗 | 首次进入、了解规则 | [guide.md](overview/guide.md) |
| [modules/](modules/) | 中 | 理解模块设计 | [architecture.md](modules/architecture.md) |
| [interfaces/](interfaces/) | 细 | 查阅接口用法 | [README.md](interfaces/README.md) |
| [knowledge/](knowledge/) | - | 背景知识、复盘 | [README.md](knowledge/README.md) |

## 阅读路径

### 首次进入项目
```
overview/guide.md → overview/roadmap.md → (按需) modules/
```

### 执行具体任务
```
interfaces/README.md → 选择 Agent/Skill → toolchain/
```

### 需要背景知识
```
knowledge/analysis/ 或 knowledge/guides/
```

## 层级关系图

```
overview/ (粗颗粒)
    │
    ↓ 细化
modules/ (中颗粒)
    │
    ↓ 细化
interfaces/ (细颗粒)
    │
    ↓ 引用
toolchain/ (实现)

knowledge/ ←── 横向支撑所有层级
```

---

**版本**：v2.0
**最后更新**：2026-03-11
**维护者**：浮浮酱
