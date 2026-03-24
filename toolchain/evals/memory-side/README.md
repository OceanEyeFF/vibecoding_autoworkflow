# Memory Side Evals

`toolchain/evals/memory-side/` 保存 `Memory Side` 主题下的稳定测量面，不保存业务源码和运行期产物。

当前主线：

- `program.md`
- `scenarios.json`
- `schemas/`
- `scoring/`

AI 先读什么：

1. `toolchain/evals/README.md`
2. `program.md`
3. `scenarios.json`
4. 需要校验输出时，再读 `schemas/` 与 `scoring/`

当前 `scoring/` 的最小覆盖面包括：

- `knowledge-base-rubric.json`
- `context-routing-rubric.json`
- `writeback-cleanup-rubric.json`

暂时不要先读什么：

- `.autoworkflow/` 里的运行结果
- `product/` 下的业务源码，除非当前任务要交叉验证评测对象

这里适合放：

- benchmark program
- scenarios
- schemas
- scoring rubrics

这里不适合放：

- 运行日志
- 临时结果
- 项目主线规则
