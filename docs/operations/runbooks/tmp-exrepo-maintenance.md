---
title: "TMP Exrepo 维护说明"
status: active
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---
# TMP Exrepo 维护说明

> 目的：把当前仓库里 `manage_tmp_exrepos.py` 的真实 CLI 形状、运行边界和安全语义固定成 repo-local runbook，避免后续把 `/tmp` 运行时维护误写成 `autoresearch` 主流程的一部分。

## 一、适用范围

本页只覆盖当前已经存在的 TMP exrepo 维护入口：

- `toolchain/scripts/research/manage_tmp_exrepos.py`

它当前只负责：

- 读取 `toolchain/scripts/research/exrepo.txt` 或显式 `--repo-list`
- 用 `resolve_tmp_exrepos_root()` 计算稳定 TMP exrepo 根目录
- 兼容 legacy flat mode，并在子命令模式下执行 `init / reset / prepare`
- 按整个 catalog、显式 `--repo` 或 `--suite` 派生出的 repo 子集维护 TMP exrepo
- 只维护 `/tmp` 运行时 exrepo，不接管 runner 或 autoresearch authority

它当前不负责：

- 自动接入 `run_autoresearch.py`
- 物化 suite
- 维护 `autoresearch` authority 状态
- 把 `/tmp` 运行时路径提升成文档 authority
- 维护仓库内 `.exrepos/`

## 二、当前入口

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py
```

顶层 `--help` 当前暴露：

- `--repo-list`
- `--repo-root`
- `--temp-root`
- `init`
- `reset`
- `prepare`

当前默认值：

- `--repo-list` 默认指向 `toolchain/scripts/research/exrepo.txt`
- `--repo-root` 默认指向当前仓库根目录
- `--temp-root` 默认不传；此时脚本会复用共享 TMP exrepo 根解析逻辑

子命令 `init / reset / prepare` 当前共享两类附加选择器：

- `--repo <name>`：可重复传入；只能使用 catalog 中的 local repo target name
- `--suite <path>`：从 suite manifest 的 `runs[*].repo` 派生 repo 集合

注意：

- `--repo` 与 `--suite` 当前互斥
- 这些选择器只在子命令模式下存在
- 顶层不带子命令时，脚本会兼容为“整个 catalog 的 `prepare`”

## 三、repo 集合与 TMP 根来源

repo catalog 当前来自：

- `toolchain/scripts/research/exrepo.txt`
- 或显式传入的 `--repo-list`

catalog 文件约束：

- 空行和 `#` 注释会被忽略
- 每条记录必须是严格的 `owner/repo`
- local target name 取 `repo` 部分
- 若两个条目映射到同一个 local target name，会直接 fail closed

子命令模式下，repo 集合来源当前有三种：

1. 不传 `--repo` / `--suite`
   - 使用整个 catalog
2. 传 `--repo`
   - 只接受 catalog 中已有的 local target name
   - 重复值会按输入顺序去重
3. 传 `--suite`
   - suite manifest 必须定义非空 `runs` 列表
   - `runs[*].repo` 可以是 catalog 名称
   - 也可以是解析后位于 TMP exrepo 根目录直系子目录的路径
   - 若 basename 不在 catalog 中，或路径不在 TMP exrepo 根目录直系子目录，直接 fail closed

TMP exrepo 根目录当前统一由：

- `toolchain/scripts/research/exrepo_runtime.py`
- `resolve_tmp_exrepos_root(repo_root=..., temp_root=...)`

统一计算。

这意味着：

- 维护脚本与 direct runner / autoresearch 共享同一套 runtime root helper
- `/tmp` 运行时路径来自 helper 计算结果，不在文档层单独维护第二套 authority 命名

## 四、当前模式语义

### 1. `init`

- 目标目录不存在时：
  - 执行 `git clone https://github.com/<owner>/<repo>.git <target-dir>`
  - 返回 `cloned`
- 目标目录已存在且是匹配的 GitHub repo 时：
  - 不执行 fetch / reset
  - 返回 `kept`
- 目标目录已存在但不是 git repo，或 origin 不匹配时：
  - 直接失败

### 2. `reset`

- 只处理已经存在的 git repo；缺失目标会直接失败
- 执行顺序当前固定为：
  - 校验 `origin` 必须是 GitHub remote，且必须匹配 catalog 里的 `owner/repo`
  - `git fetch origin`
  - 解析 `refs/remotes/origin/HEAD`
  - 若第一次解析失败，会额外执行一次 `git remote set-head origin --auto` 后再重试
  - `git reset --hard <origin/HEAD>`
  - `git checkout -B <default-branch> <origin/HEAD>`
- 成功返回：
  - `reset`

### 3. `prepare`

- 目标目录不存在时：
  - 先 clone
  - 再执行完整 reset 路径
  - 返回 `cloned_then_reset`
- 目标目录已存在且是 git repo 时：
  - 直接执行完整 reset 路径
  - 返回 `reset`

### 4. legacy flat mode

- 不带子命令运行时：
  - 当前兼容为整个 catalog 的 `prepare`
  - 不接受 `--repo` 或 `--suite`

## 五、安全边界与 fail-closed 规则

当前已能写死的安全边界只有这些：

- destructive git 动作只会对 TMP exrepo 根下、当前条目对应的 target dir 执行
- target dir 必须在解析后仍位于 TMP exrepo 根目录内；目录逃逸或符号链接跳出会直接拒绝
- 只接受 GitHub `origin`，且 `origin` 必须与 catalog 里的 `owner/repo` 完全匹配
- 非 git 目录不会被“就地修复”，而是直接失败
- `--suite` 只能选择 catalog 名称，或解析到 TMP exrepo 根目录直系子目录的 repo path
- 脚本不会触达仓库内 `.exrepos/`
- 脚本不会改 `run_autoresearch.py`、`runtime.json`、`round.json` 或其他 authority 文件
- 脚本不会把 `/tmp` 运行时路径回写成 canonical truth

当前不要写死的内容：

- “脚本会被 autoresearch 主流程自动调用”
- “维护脚本会物化 suite 或自动准备 direct runner 输入”
- “`--suite` 可以接受 TMP exrepo 根以外的任意 repo path”

这些语义当前没有被代码证明，或已经被代码显式拒绝。

## 六、常用命令

使用默认 repo list，以 legacy flat mode 执行整个 catalog 的 `prepare`：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py
```

只初始化缺失 repo，不碰已存在的有效 repo：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py \
  init \
  --repo typer
```

按 suite 清单重置所选 repo：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py \
  reset \
  --suite /abs/path/to/suite.json
```

显式指定 repo list，并在测试或隔离环境里覆盖 TMP 根锚点：

```bash
python3 toolchain/scripts/research/manage_tmp_exrepos.py \
  prepare \
  --repo-list /abs/path/to/exrepo.txt \
  --repo-root /abs/path/to/repo \
  --temp-root /abs/path/to/os-tmp
```

## 七、输出与失败语义

当前标准输出会先打印：

- `tmp_exrepo_root: <resolved-path>`

每个 repo 成功时会打印：

- `kept: <owner/repo> -> <target-dir>`
- `cloned: <owner/repo> -> <target-dir>`
- `reset: <owner/repo> -> <target-dir>`
- `cloned_then_reset: <owner/repo> -> <target-dir>`

预检查失败时：

- 主入口会打印 `error: ...`
- 直接返回非零

典型预检查失败包括：

- repo list 缺失或为空
- catalog 条目不是 `owner/repo`
- duplicate local target
- `--repo` 指向未知 catalog 名称
- suite manifest 缺失、`runs` 非法或 `repo` 非法
- suite repo path 不在 TMP exrepo 根目录直系子目录

失败时：

- 单个 repo 失败会打印 `failed: ...`
- 其余 repo 仍会继续处理
- 若存在任意失败，主入口最终返回非零，并打印 `sync_failed: <N> repo(s)`

## 八、当前验证依据

当前脚本行为的 deterministic 依据包括：

- `toolchain/scripts/research/test_manage_tmp_exrepos.py`
  - repo list 解析
  - duplicate local target 拒绝
  - legacy flat mode -> `prepare`
  - `init / reset / prepare` 子命令语义
  - `--repo` / `--suite` 选择与 fail-closed
  - 缺失 repo clone、existing repo kept/reset、per-repo failure reporting
  - non-git target、origin mismatch、非 GitHub remote、TMP root 逃逸拒绝
  - `origin/HEAD` 解析与 `remote set-head origin --auto` 失败分支
  - 主入口 `error:` / `failed:` / `sync_failed:` 返回码
- `python3 toolchain/scripts/research/manage_tmp_exrepos.py --help`
  - 顶层 shared options
  - `init / reset / prepare` 子命令存在
- `python3 toolchain/scripts/research/manage_tmp_exrepos.py <subcommand> --help`
  - `--repo` / `--suite` 只存在于子命令
- `toolchain/scripts/research/common.py`
  - 与 direct runner 共享 repo 解析入口
- `toolchain/scripts/research/exrepo_runtime.py`
  - 共享 TMP exrepo 根目录 helper

## 九、相关文档

- [Research CLI 指令](../references/research-cli-help.md)
- [Autoresearch 最小闭环运行说明](./autoresearch-minimal-loop.md)
- [toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)
- [路径与文档治理检查运行说明](../governance/path-governance-checks.md)
