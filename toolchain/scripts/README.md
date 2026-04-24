# Scripts

`toolchain/scripts/` 只放可执行动作入口。

当前分层：

- `deploy/`：部署与同步
- `git-hooks/`：本地 git hooks 入口（阻断违规 push）
- `test/`：治理检查、gate 与轻量测试入口

不要把下面这些东西放进这里：

- 业务源码
- 文档真相
- benchmark 运行产物
- 临时日志和缓存
