# Harness Scope

`docs/harness/scope/` 固定 Harness 的两层控制对象与它们之间的状态闭环。

## RepoScope

`RepoScope` 是 Harness 的**慢变量控制层**，负责长期基线——repo goal、架构与模块地图、主分支现状、活跃分支及用途、治理状况、系统不变量、已知风险。其核心职责不是推进单个任务，而是判断是否需要新建/恢复/刷新 worktrack、当前 baseline 是否仍可信、以及目标是否需要进入 change control。

权威定义见 [Harness指导思想.md](../foundations/Harness指导思想.md)。

## WorktrackScope

`WorktrackScope` 是 Harness 的**快变量控制层**，负责局部状态转移——当前任务目标、范围与非目标、验收条件、branch 与 baseline 差异、子任务序列、回滚/拆分/恢复路径。它依赖的最小正式对象包括 Worktrack Contract、Plan/Task Queue、Gate Evidence 和 Control State。WorktrackScope 不应吸收 repo 级长期真相；它消费 RepoScope 给出的 baseline，局部闭环完成后回传结果给 RepoScope。

权威定义见 [Harness运行协议.md](../foundations/Harness运行协议.md)。

## 当前入口

- [state-loop.md](./state-loop.md)：两层 Scope 之间的完整状态转移矩阵
