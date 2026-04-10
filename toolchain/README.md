# Toolchain

`toolchain/` 是当前仓库第三块正式内容区。

它只负责：

- 执行动作的脚本入口
- 轻量测试与治理入口
- 后续按需准入的打包、分发或测量工具

它不负责：

- 业务源码
- 文档真相
- repo-local mount
- 运行产物

当前主线：

- `scripts/deploy/`
- `scripts/test/`
- `evals/`

AI 先读什么：

1. `toolchain/toolchain-layering.md`
2. `toolchain/scripts/README.md` 或 `toolchain/evals/README.md`
3. 需要部署时进入 `scripts/deploy/`
4. 需要做轻量治理回归时进入 `scripts/test/`
5. 只有任务明确涉及已准入测量资产时，才进入 `scripts/research/` 或 `evals/`

暂时不要先读什么：

- `product/` 下的业务源码，除非当前任务需要交叉核对实现
- `.autoworkflow/` 下的运行产物，除非当前任务明确是结果分析

二级入口：

- `scripts/README.md`
- `scripts/deploy/README.md`
- `scripts/research/README.md`
- `scripts/test/README.md`
- `evals/README.md`
- `evals/fixtures/README.md`
- `evals/memory-side/README.md`

治理说明见 `toolchain/toolchain-layering.md`。
