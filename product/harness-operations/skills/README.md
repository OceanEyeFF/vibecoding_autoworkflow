# Harness Operations Skills

`product/harness-operations/skills/` 当前是 Harness 的 legacy canonical skill 源码入口，不是 deploy target。

新的 Harness-first 源码叙事入口：

- [../../harness/README.md](../../harness/README.md)

当前主线：

- `execution-contract-template/`
- `harness-contract-shape/`
- `repo-governance-evaluation/`
- `review-loop-workflow/`
- `simple-workflow/`
- `strict-workflow/`
- `task-list-workflow/`
- `task-planning-contract/`

当前分类：

| legacy skill | 分类 | 目标去向 |
|---|---|---|
| `execution-contract-template` | `split` | `product/harness/core/contracts/` |
| `harness-contract-shape` | `split` | `product/harness/core/contracts/` + `product/harness/core/governance/` |
| `task-planning-contract` | `split` | `product/harness/core/contracts/` + `product/harness/workflows/repo-evolution/` |
| `repo-governance-evaluation` | `downgrade` | `product/harness/core/governance/` 子能力 |
| `review-loop-workflow` | `deprecate` | `product/harness/workflows/repo-evolution/review-repair.loop.md` |
| `simple-workflow` | `deprecate` | `product/harness/profiles/simple.profile.md` |
| `strict-workflow` | `deprecate` | `product/harness/profiles/strict.profile.md` |
| `task-list-workflow` | `downgrade` | `product/harness/workflows/repo-evolution/` + `product/harness/profiles/task-list.variant.md` |

路由权威以 `AGENTS.md` 为准。
当 authority 已确认进入 canonical skill source layer 时，本目录只建议继续读取：

1. `product/harness-operations/README.md`
2. 对应 skill 的 `SKILL.md`
3. 对应 skill 的 `prompt.md`
4. 对应 skill 的 `references/entrypoints.md`
5. `product/harness-operations/skills/harness-standard.md`

这里适合放：

- Harness Operations canonical skill 源码
- backend-agnostic `prompt.md`
- shared `harness-standard.md`
- skill 的最小 references（`entrypoints.md` 与 `bindings.md`）

这里不适合放：

- repo-local 挂载结果
- 后端专属 interface metadata
- 运行期状态
- 新的 Harness ontology 命名
