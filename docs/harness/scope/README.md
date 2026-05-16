# Harness Scope

`docs/harness/scope/` 固定 Harness 的两层控制对象与它们之间的状态闭环。

本目录不复制 doctrine 或 runtime protocol 正文。`RepoScope` / `WorktrackScope` 的概念定义见 [Harness指导思想.md](../foundations/Harness指导思想.md)，运行时合法算子与连续推进规则见 [Harness运行协议.md](../foundations/Harness运行协议.md) 和 [runtime-control-loop.md](../foundations/runtime-control-loop.md)。

当前入口：

- [state-loop.md](./state-loop.md)：两层 Scope 之间的完整状态转移矩阵、异常路径和治理约束
