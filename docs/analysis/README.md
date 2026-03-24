# Analysis

`docs/analysis/` 只保存 benchmark、评测基线和研究闭环，不作为当前项目真相的默认执行入口。

当前主线：

- `eval-method-evolution.md`
- `eval-fixture-design.md`
- `memory-side/memory-side-eval-baseline.md`
- `memory-side/memory-side-auto-research-loop.md`
- `task-interface/task-interface-eval-baseline.md`

AI 先读什么：

1. `docs/knowledge/foundations/root-directory-layering.md`
2. `docs/knowledge/foundations/toolchain-layering.md`
3. 需要评测或研究时，再进入目标主题目录

暂时不要先读什么：

- `docs/reference/`
- `docs/archive/`
- 业务源码目录，除非当前任务需要交叉核对实现

这里适合放：

- repo-local eval baseline
- 研究流程说明
- benchmark 约束和观察

这里不适合放：

- 当前主线规则
- 业务源码真相
- 运行期临时结果
