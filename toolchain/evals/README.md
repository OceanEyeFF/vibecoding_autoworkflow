# Evals

`toolchain/evals/` 只保留已准入的测量资产。

当前状态：

- `prompts/`
- `fixtures/`
- `memory-side/`

说明：

- `prompts/` 当前承载最小 rubric prompt 资产
- `fixtures/` 与 `memory-side/` 仍然只保留占位入口
- 当前还没有完整的 V1 `fixtures / schemas / scoring program` 资产

这里适合放：

- 后续明确准入的测量格式
- 稳定、可复跑的最小数据面

这里不适合放：

- 业务源码
- 临时运行产物
- 本地日志
- 尚未收口的评测体系
