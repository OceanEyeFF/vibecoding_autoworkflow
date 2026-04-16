# Harness Manifests

`product/harness/manifests/` 承接 Harness skill 的 machine-readable 分发元数据，但当前只保留 B1 的过渡性 canonical read surface 与首发冻结投影，不重复 canonical skill truth。

当前阶段：

- `schema/skill-manifest.v1.schema.json` 固定 B1 的最小 schema
- `agents/skills/*.json` 只包含五个 first-wave skills 的实例
- 这套 v1 manifest 不是 A1 最终 manifest 落地；required payload files、payload policy 与 reference distribution 仍留给后续 manifest revision
- `product/harness/skills/` 继续承接 canonical skill source，而 Harness doctrine 与相邻系统合同仍以 `docs/harness/` 和相关治理文档为准
- repo-local deploy/runtime state 继续留在 `.autoworkflow/`、`.agents/`、`.claude/` 与 `.opencode/`

本目录当前不承接：

- skill 正文或 workflow 正文
- adapter payload source 设计
- deploy install state、hash、checksum 或 verify 结果
- repo-local / global target root 的绝对路径

当前结构：

```text
product/harness/manifests/
├── README.md
├── schema/
│   └── skill-manifest.v1.schema.json
└── agents/
    └── skills/
        ├── dispatch-skills.json
        ├── harness-skill.json
        ├── init-worktrack-skill.json
        ├── repo-status-skill.json
        └── repo-whats-next-skill.json
```
