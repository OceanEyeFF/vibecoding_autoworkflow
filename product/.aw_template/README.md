# AW Template

`product/.aw_template/` 是 repo-local execution template layer。

这里承接可复制使用的模板文件，帮助在具体项目或具体回合中快速创建 Harness 相关正式对象；它不是 canonical truth，也不是新的源码根。

当前入口：

- [repo/README.md](./repo/README.md)
- [worktrack/README.md](./worktrack/README.md)
- [control/README.md](./control/README.md)

规则：

- 模板应直接映射 `docs/harness/artifact/` 的正式对象
- 模板可以是可填写的 markdown skeleton
- 不要把 doctrine、运行协议或 backend wrapper 写到这里
- 真正的定义以上游 `docs/harness/` 为准
