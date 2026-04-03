# Scripts

`toolchain/scripts/` 只放可执行动作入口。

当前分层：

- `deploy/`：部署与同步
- `research/`：已准入的研究 runner、实验 orchestration 与 live acceptance 入口
- `test/`：治理检查、gate 与轻量测试入口

不要把下面这些东西放进这里：

- 业务源码
- 文档真相
- benchmark 运行产物
- 临时日志和缓存
