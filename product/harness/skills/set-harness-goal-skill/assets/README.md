# Harness Init Assets

`set-harness-goal-skill/assets/` 是 `set-harness-goal-skill` 自带的 `.aw` 初始化资产包。

这里存放的是 `.aw/` 运行目录所需的模板来源，用来在 deploy 后或初始化时生成 `.aw/` 目录结构，以及少量直接属于 Harness 运行管理面的文档。它们是本技能的 canonical executable resources，不是独立的源码根，也不会替代 `docs/harness/` 的 artifact contract 真相层。

当前入口：

- [control-state.md](./control-state.md)
- [goal-charter.md](./goal-charter.md)
- [repo/README.md](./repo/README.md)
- [worktrack/README.md](./worktrack/README.md)
- [template/README.md](./template/README.md)

规则：

- 这些资产只服务 `set-harness-goal-skill` 的 `.aw` 初始化流程
- 建议通过 [../scripts/deploy_aw.py](../scripts/deploy_aw.py) 生成 `.aw/` 样例，而不是手工复制这些文件
- 用法固定为把目标 repo / worktree 根作为 `--deploy-path` 传入；脚本会在 `<deploy-path>/.aw/` 下生成文件
- 需要完整参数说明时，直接运行 `python3 scripts/deploy_aw.py generate --help`
- 资产 owner 已固定在本技能；不要再为它们建立独立的 `.aw` 模板源码根
- goal 修正文档不进入 `.aw/` 路径，只作为 Codex 对话回答流模板存在
- 不要把 doctrine、运行协议或 backend wrapper 写到这里
- 不要把这些资产误当成 `docs/` 真相层
- 运行协议与 artifact 定义以上游 `docs/harness/` 为准

示例：

```bash
python3 scripts/deploy_aw.py generate --deploy-path "$DEPLOY_PATH" --owner aw-kernel
python3 scripts/deploy_aw.py generate --deploy-path "$DEPLOY_PATH" --force --dry-run
```
