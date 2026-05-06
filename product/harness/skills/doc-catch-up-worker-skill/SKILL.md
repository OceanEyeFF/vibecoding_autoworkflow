---
name: doc-catch-up-worker-skill
description: 当工作追踪需要把已验证实现事实追平到正确文档层，减少后续开发引用过期上下文时，使用这个技能。
---

# 文档追平 Worker 技能

## 概览

本技能是 Harness 执行平面的文档追平 worker。它负责在每个 worktrack 的实现或验证事实稳定后，把事实同步到正确的长期文档层，减少后续开发因为引用旧文档、旧计数、旧路径或旧操作流程导致的错误。

本技能只追平已经验证的事实，不把推测、计划或未通过验证的中间结论写进 `docs/`。它不替代设计、review、gate 或 repo-goal 变更；它只做文档基线对齐。

它也负责 `version fact sync`：当 package 版本、approval lock、CLI 版本输出、npm dist-tag、registry artifact 或 GitHub Release 事实发生变化时，把已验证版本事实同步到 release/channel/testing/usage 文档，并明确哪些入口不需要更新。

## 何时使用

当满足以下任一条件时使用：

- 当前 worktrack 已改变 operator-facing 行为、部署流程、验证命令、skill set、目录结构或治理规则
- 当前 worktrack 改变 package version、release approval lock、publish workflow、dist-tag、registry artifact、CLI `--version` 输出或 GitHub Release 事实
- publish workflow 成功后，需要把 npm registry 的 `latest` / `next` / `canary`、published version、`gitHead` 和 tarball 事实写回治理文档
- 实现已通过匹配验证，但长期文档仍引用旧路径、旧数量、旧命令或旧边界
- closeout 前需要确认文档是否与已验证事实一致
- 一个任务完成后需要为后续 worktrack 拉平上下文基线

不适用于：

- 写未验证的设计愿景
- 把研究草稿直接升格为长期真相
- 大范围改写 docs 叙事结构
- 替 `repo-change-goal-skill` 修改 Repo 级目标
- 替 `gate-skill` 做最终放行判断

## 输入约定

调用本技能时，任务 Prompt 至少应包含：

- `已验证事实`
- `触及实现或配置`
- `可能过期的文档范围`
- `应同步的 truth layer`
- `不应同步的内容`
- `验证证据`
- `完成信号`

如果任务是 `version fact sync`，Prompt 还应包含：

- `source version facts`：root/package `package.json`、approval lock、CLI `--version`、release tag
- `vcs tracking facts`：git branch、commit SHA、tag、remote ref；若目标仓库使用 SVN，则记录 SVN URL、revision、branch/tag 路径和工作副本状态
- `published version facts`：`npm view aw-installer dist-tags --json`，以及相关 `npm view aw-installer@<tag-or-version> version gitHead dist.tarball --json`
- `release evidence`：GitHub Release、publish workflow run、npx/package smoke 结果
- `doc update decision`：哪些根入口、governance、testing、usage-help 文档需要更新，哪些不需要更新及理由

默认 truth layer：

- 项目维护规则、governance、deploy、usage-help 写入 `docs/project-maintenance/`
- Harness doctrine、workflow family、artifact 与 adjacent-system 合同写入 `docs/harness/`
- 可执行合同写入 `product/` 或 `toolchain/`
- 不把长期事实写入 `.agents/`、`.claude/`、`.nav/`

## 工作流

1. 读取任务 Prompt、当前 diff 和验证证据，提取已验证事实。
2. 定位最小文档范围，优先更新承接层正文和最近入口页。
3. 查找旧路径、旧数量、旧命令、旧行为描述和旧准入条件。
4. 只写入已验证事实；对未验证事项保留为待办或不写入长期文档。
5. 如果涉及版本事实，先区分 `source version`、`published version` 和 `docs freshness`，再更新对应文档；不得把本地 candidate 写成 registry artifact，也不得把 registry fact 写进未复核页面。
6. 更新文档 frontmatter 的 `updated` / `last_verified`，仅限本轮实际复核过的文档。
7. 运行与文档和治理面匹配的检查。
8. 返回文档追平报告，不输出 gate 判定。

## Version Fact Sync

版本事实同步是本技能的专用模式，触发时机固定在这些节点：

- `harness entry observation`：`harness-skill` 启动一轮控制回路时，如发现 package/release/VCS 文档事实与当前代码或 registry 证据可能不一致，先记录 freshness risk，并在不阻塞主流程的前提下排入文档追平任务。
- `pre-publish readiness`：approval lock 或 package version 变更后，publish 前确认 root README、release channel、pre-publish、testing/usage docs 没有指向旧 selector 或旧行为。
- `post-publish verification`：publish workflow 成功并完成 registry 查询后，更新 registry fact、dist-tag、published version、`gitHead`、tarball URL 和后续 immutable version 约束。
- `post-smoke closeout`：registry npx / local `.tgz` smoke 通过后，必要时更新 testing docs 的 selector、命令矩阵或 pass criteria。
- `harness closeout`：`harness-skill` 命中 handback/closeout 前，若本轮触碰 release、deploy、adapter、package、VCS baseline 或 operator-facing docs，必须调用本技能确认文档版本事实已追平。
- `release rollback / failed publish`：只记录已验证失败事实和恢复边界，不把未发布 candidate 写成 published fact。

推荐证据命令：

```bash
git status --short --branch
git rev-parse HEAD
git describe --tags --always --dirty
svn info
npm view aw-installer dist-tags --json
npm view aw-installer@latest version gitHead dist.tarball --json
npm view aw-installer@next version gitHead dist.tarball --json
node toolchain/scripts/deploy/bin/aw-installer.js --version
```

同步目标通常包括：

- `docs/project-maintenance/governance/aw-installer-release-channel-governance.md`
- `docs/project-maintenance/governance/aw-installer-pre-publish-governance.md`
- `docs/project-maintenance/governance/aw-installer-release-standard-flow.md`
- `docs/project-maintenance/testing/npx-command-test-execution.md`
- `docs/project-maintenance/usage-help/codex.md`
- `docs/project-maintenance/usage-help/claude.md`
- root `README.md`，仅当根入口 selector、试用路径或成熟度口径确实变化

## 硬约束

- 不要把未验证计划写成长期真相。
- 不要把 docs 当成临时 scratchpad。
- 不要在 `.agents/`、`.claude/` 或 `.nav/` 写长期事实。
- 不要为了同步一个事实而重写整篇文档。
- 不要改变实现以配合文档，除非任务 Prompt 明确要求并且仍在当前范围内。
- 不要更新未实际复核过的 `last_verified`。
- 不要把 npm registry 查询之外的推断写成 published version fact。
- 不要把 `latest`、`next` 或 `canary` 的 dist-tag 变更写进 release docs，除非附带 registry 查询证据。
- 不要把 git commit、tag、branch 或 SVN revision 当成 package publish 事实；它们只提供可追踪性。
- 如果当前仓库不是 SVN 工作副本，不要臆造 SVN revision；记录 `svn: not applicable` 即可。
- 不要引入双份主线；新增或接管文档作用域时必须同步最近入口页并清理旧入口。

## 预期输出

使用本技能时，返回一份 `文档追平报告`，至少包含：

- `已验证事实`
- `文档同步范围`
- `已更新文档`
- `未同步内容`
- `验证结果`
- `返回 Harness`

字段至少包括：

- `truth layer`
- `引用的验证证据`
- `旧上下文清理`
- `version fact sync`（如适用：source version、published version、VCS tracking facts、docs freshness、未更新文档及理由）
- `剩余文档风险`
- `建议下一动作`

## 资源

使用当前 worktrack 的实现 diff、验证命令输出、`AGENTS.md`、`docs/README.md`、`docs/project-maintenance/README.md`、`docs/harness/README.md` 和相关承接层文档作为输入。
