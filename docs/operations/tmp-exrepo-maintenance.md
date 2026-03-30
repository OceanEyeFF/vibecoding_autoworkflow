---
title: "TMP Exrepo 维护说明"
status: active
updated: 2026-03-30
owner: aw-kernel
last_verified: 2026-03-30
---
# TMP Exrepo 维护说明

> 目的：把当前仓库里 `manage_tmp_exrepos.py` 的真实 CLI 形状、运行边界和安全语义固定成 repo-local runbook，避免后续把 `/tmp` 运行时维护误写成 `autoresearch` 主流程的一部分。

## 一、适用范围

本页只覆盖当前已经存在的 TMP exrepo 维护入口：

- `toolchain/scripts/research/manage_tmp_exrepos.py`

它当前只负责：

- 读取 `toolchain/scripts/research/exrepo.txt` 或显式 repo list
- 计算稳定 TMP exrepo 根目录
- 对每个 repo 执行 clone / pull / reset-then-pull

它当前不负责：

- 自动接入 `run_autoresearch.py`
- 物化 suite
- 维护 `autoresearch` authority 状态
- 按 suite 清单推导 repo 集合
- `init / reset / prepare` 子命令风格的更细粒度 CLI

## 二、当前入口

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py
```

当前 `--help` 形状是：

- `--repo-list`
- `--repo-root`
- `--temp-root`

当前默认值：

- `--repo-list` 默认指向 `toolchain/scripts/research/exrepo.txt`
- `--repo-root` 默认指向当前仓库根目录
- `--temp-root` 默认不传；此时脚本会复用共享 TMP exrepo 根解析逻辑

## 三、当前运行模型

脚本当前流程固定为：

1. 读取 repo list，一行一个 `owner/repo`
2. 用 `repo_root` 推导稳定 TMP exrepo 根目录
3. 对每个条目执行同步

repo list 的当前约束：

- 空行和 `#` 注释会被忽略
- 每条记录必须是严格的 `owner/repo`
- local target name 取 `repo` 部分
- 若两个条目映射到同一个 local target name，会直接 fail closed

TMP exrepo 根目录当前由：

- `toolchain/scripts/research/exrepo_runtime.py`
- `resolve_tmp_exrepos_root(repo_root=..., temp_root=...)`

统一计算。

这意味着：

- 维护脚本和 direct runner / autoresearch 主链共享同一套 TMP exrepo 根目录语义
- `/tmp` 运行时路径来自 helper 计算结果，不在文档层单独维护第二套命名规则

## 四、当前同步语义

对单个 repo，当前代码只支持两类路径：

### 1. 目标目录不存在

脚本会执行：

- `git clone https://github.com/<owner>/<repo>.git <target-dir>`

返回动作标记：

- `cloned`

### 2. 目标目录已存在且是 git repo

脚本会先执行：

- `git pull`

若 `git pull` 成功，返回动作标记：

- `pulled`

若 `git pull` 失败，脚本会执行：

- `git reset --hard`
- 再次 `git pull`

若重试成功，返回动作标记：

- `reset_then_pulled`

若目标目录存在但不是 git repo，脚本会直接失败。

## 五、安全边界

当前已能写死的安全边界只有这些：

- destructive git 动作只会对 TMP exrepo 根下、当前条目对应的 target dir 执行
- 脚本不会触达仓库内 `.exrepos/`
- 脚本不会改 `run_autoresearch.py`、`runtime.json`、`round.json` 或其他 authority 文件
- 脚本不会把 `/tmp` 运行时路径回写成 canonical truth

当前不要写死的内容：

- “脚本一定会把 repo reset 到远端默认分支最新 HEAD”
- “脚本已经支持 suite-driven repo 选择”
- “脚本已经有 `init / reset / prepare` 子命令”
- “脚本会被 autoresearch 主流程自动调用”

这些语义当前都还没有被代码证明。

## 六、常用命令

使用默认 repo list：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py
```

显式指定 repo list：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py \
  --repo-list /abs/path/to/exrepo.txt
```

在测试或隔离环境里覆盖 TMP 根锚点：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py \
  --repo-root /abs/path/to/repo \
  --temp-root /abs/path/to/os-tmp
```

## 七、输出与失败语义

当前标准输出会先打印：

- `tmp_exrepo_root: <resolved-path>`

每个 repo 成功时会打印：

- `cloned: <owner/repo> -> <target-dir>`
- `pulled: <owner/repo> -> <target-dir>`
- `reset_then_pulled: <owner/repo> -> <target-dir>`

失败时：

- 单个 repo 失败会打印 `failed: ...`
- 若存在任意失败，主入口最终返回非零，并打印 `sync_failed: <N> repo(s)`

repo list 本身若有问题，也会直接返回非零，例如：

- repo list 缺失
- repo list 为空
- 条目不是 `owner/repo`
- duplicate local target

## 八、当前验证依据

当前脚本行为的 deterministic 依据包括：

- `toolchain/scripts/research/test_manage_tmp_exrepos.py`
  - repo list 解析
  - duplicate local target 拒绝
  - 缺失 repo clone
  - 已有 repo pull
  - pull 失败后的 reset-then-pull
  - 主入口失败返回码
- `toolchain/scripts/research/common.py`
  - 与 direct runner 共享 repo 解析入口
- `toolchain/scripts/research/exrepo_runtime.py`
  - 共享 TMP exrepo 根目录 helper

## 九、相关文档

- [Research CLI 指令](./research-cli-help.md)
- [Autoresearch 最小闭环运行说明](./autoresearch-minimal-loop.md)
- [toolchain/scripts/research/README.md](../../toolchain/scripts/research/README.md)
- [路径与文档治理检查运行说明](./path-governance-checks.md)
