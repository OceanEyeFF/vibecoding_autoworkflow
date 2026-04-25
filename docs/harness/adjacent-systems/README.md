# Adjacent Systems

`docs/harness/adjacent-systems/` 固定那些与 Harness 强相关、但不属于 Harness 本体的相邻系统。

当前入口：

- [task-interface/README.md](./task-interface/README.md)
- [memory-side/README.md](./memory-side/README.md)

当前边界：

- `Task Interface` 负责把讨论收束成正式执行基线
- `Memory Side` 负责长期记忆、路由与写回清理
- Harness 可以消费这两个系统的正式对象，但不应把它们改写成自己的本体定义
