# Toolchain

`toolchain/` 是当前仓库第三块正式内容区。

它只负责：

- 执行动作的脚本入口
- 评测程序、场景、schema、rubric
- 后续测试、打包、分发工具

它不负责：

- 业务源码
- 文档真相
- repo-local mount
- 运行产物

当前主线：

- `scripts/deploy/`
- `scripts/research/`
- `evals/`

治理说明见 `docs/knowledge/foundations/toolchain-layering.md`。
