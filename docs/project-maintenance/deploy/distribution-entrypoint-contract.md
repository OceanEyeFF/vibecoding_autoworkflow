---
title: "Distribution Entrypoint Contract"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
---
# Distribution Entrypoint Contract

> 目的：为后续 reusable install/update/verify/diagnose 分发入口固定最小合同。本文只定义未来包装层必须保持的语义，不表示 npm/npx、Python package 或 release channel 已经实现。

本页属于 [Deploy Runbooks](./README.md) 系列。当前可执行入口仍是仓库内脚本：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py
```

当前还提供一个本地薄包装入口，供后续 package runner 复用同一命令面：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py
```

当前 `toolchain/scripts/deploy/package.json` 和 `bin/aw-harness-deploy.js` 只提供本地 npm-style scaffold；它们调用同一个 Python wrapper，不代表 package 已发布。

package packlist 检查应在 `toolchain/scripts/deploy/` package root 内执行 `npm pack --dry-run --json`。不要从仓库根用 `--prefix` 运行 `pack`，因为该命令会寻找当前工作目录的 `package.json`。

CI 必须显式设置 Node 后运行本地 package smoke、package-root pack dry-run，以及从临时 `.tgz` 执行 `aw-harness-deploy --help` 和带 `AW_HARNESS_REPO_ROOT=<repo-root>` 的只读 `diagnose` tarball smoke；这些只验证 `aw-harness-deploy` scaffold 的分发面，不表示 npm/npx 发布渠道已经开启。

`AW_HARNESS_REPO_ROOT` 是当前 packaged wrapper 的 source checkout bridge。包装层可以改变启动位置，但所有 deploy source / target / payload 合同仍必须以该 source checkout 为准，不能从 package 解压目录或 deploy target 反推业务真相。

## 一、范围

本文定义未来分发入口的外层合同：

- 分发包装层可以改变 operator 如何启动命令，但不能改变 deploy 语义。
- 当前 `agents` backend 的 source / target / payload / marker 合同仍以 [Deploy Mapping Spec](./deploy-mapping-spec.md) 为准。
- 当前 destructive reinstall 主流程仍以 [Deploy Runbook](./deploy-runbook.md) 为准。

本文不定义：

- npm/npx 包名、Python 包名、发布 registry 或版本策略。
- 新的 deploy backend。
- `adapter_deploy.py` 内部实现。
- one-shot mutating install/update 行为。

## 二、当前与未来入口

当前已验证入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py <mode> --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py <mode> --backend agents
```

未来可复用包装层可以提供更短的启动形式，例如 package runner、project-local bin 或 thin wrapper，但必须投影到同一组 mode：

| mode | 当前语义 | 未来包装层约束 |
|---|---|---|
| `diagnose` | 只读状态投影；`--json` 输出机器可读摘要；发现 issue 时仍可 0 退出 | 保持只读、非严格失败信号，不替代 `verify` |
| `verify` | 只读严格复验；发现 source、target、payload、marker、drift 或 conflict 问题时失败 | 保持只读、严格失败信号 |
| `prune --all` | 删除当前 backend 可识别且属于我方的受管安装目录 | 仍必须显式触发，不能静默并入只读命令 |
| `check_paths_exist` | 写入前全量冲突扫描；发现冲突时失败且不写业务文件 | 保持零业务写入边界 |
| `install` | 只写当前 source 声明的 live payload | 不接管 archive/history、增量修复或旧版本保活 |
| `update` | 当前未实现 | 后续实现前必须先定义和验证它与三步 destructive reinstall 的关系 |

## 三、必须保持的不变量

- `diagnose` 和 `verify` 都是只读入口。
- `diagnose` 是状态观察，不是安装成功证明；需要严格失败信号时使用 `verify`。
- mutating install 仍由 `prune --all -> check_paths_exist -> install` 三步表达。
- `check_paths_exist` 失败时不得写入业务文件。
- `install` 不得跳过 source contract 校验、target path 冲突校验或 payload identity 校验。
- deploy target 不是 source of truth；包装层不得从 `.agents/`、`.claude/` 或 `.opencode/` 反向生成 canonical source。
- backend 支持列表必须来自实际实现；包装层不得把 `claude` 或 `opencode` 写成已支持 deploy backend。

## 四、`update` 的准入条件

后续若要添加 `update`，必须先完成一轮独立 worktrack，并至少回答：

- `update` 是否只是三步 destructive reinstall 的命名包装。
- `update` 如何暴露将要删除和写入的 target paths。
- `update` 在 unrecognized / foreign / conflict 目录存在时是否必须停止。
- `update` 是否复用 `diagnose` 的状态摘要和 `verify` 的严格失败信号。
- `update` 的回滚或恢复文档如何落在 [Skill Deployment 维护流](./skill-deployment-maintenance.md)。

在这些问题被验证前，operator-facing 文档不得把 `update` 写成可用命令。

## 五、包装层验收标准

未来任一分发包装 worktrack 至少应验证：

- wrapper help 或 README 不声称未实现 backend 可用。
- wrapper 的 `diagnose`、`verify` 与 repo-local 脚本在同一 fixture 上给出等价状态。
- wrapper 的 mutating command 不绕过 `check_paths_exist` 的零业务写入边界。
- wrapper 保留 backend target root override 入口，或明确声明当前不支持 override。
- wrapper 文档清楚区分当前已实现命令和未来保留命令。

## 六、当前停止线

当前仓库只承诺 repo-local deploy scripts、本地 npm-style scaffold 和 `agents` backend。`harness_deploy.py` 与 `bin/aw-harness-deploy.js` 都是本地薄包装入口，不是已发布 package。下一轮如果要进入 packaging，应以本文为合同输入，先建立包装层最小验证，再讨论发布渠道。
