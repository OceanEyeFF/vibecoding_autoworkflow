---
title: "Deploy Mapping Spec"
status: active
updated: 2026-04-23
owner: aw-kernel
last_verified: 2026-04-23
---
# Deploy Mapping Spec

> 目的：定义 destructive reinstall model 下 `原始来源 -> 后端部署包 -> 目标入口 -> 校验` 这条链路的最小操作者约定。

本页属于 [Deploy Runbooks](./README.md) 系列。

阅读前请先了解以下基础文档：

- [根目录分层](../foundations/root-directory-layering.md)
- [Deploy Runbook](./deploy-runbook.md)
- [Skill 生命周期维护](./skill-lifecycle.md)

## 一、范围

本规范只定义部署相关的映射约定：

- 如何识别 skill 的原始来源
- 如何从原始来源派生出后端部署包
- payload descriptor 如何描述可分发对象
- 目标入口如何命名与落点
- 如何校验 live install 结果

本规范不定义：

- `adapter_deploy.py` 的实现细节
- archive / history 策略
- 旧 `local/global` deploy mode
- `.aw_template/` 生成 `.aw/` 目录结构与管理文档的实现细节
- payload contract / template tooling / deploy 阶段的具体实现
- `claude` / `opencode` 等后端的后续细节

## 二、术语与链路

规范链路如下：

`原始来源 -> 后端部署包 -> 目标入口 -> 校验`

各环节定义：

- **原始来源（canonical source）**
  - 路径示例：`product/harness/skills/<skill>/SKILL.md` 或该 skill 的规范入口文件
  - 是 skill 的唯一权威来源，所有衍生内容都从这里产生
- **后端部署包（backend payload source）**
  - 路径示例：`product/harness/adapters/<backend>/skills/<skill>/`
  - 是面向具体后端的分发载体，由原始来源生成，不是权威来源
- **payload descriptor**
  - 路径示例：`product/harness/adapters/<backend>/skills/<skill>/payload.json`
  - 只描述分发与校验所需的最小信息
- **目标入口（target entry）**
  - backend target root 下的最终落点
  - 是运行时可见的 live install 入口，只读，不回写原始来源
- **校验（verify）**
  - 检查目标入口、部署包文件以及各层之间是否一致

## 三、最小字段

### 1. 原始来源路径

- 必须能唯一定位 skill 的原始来源
- 必须能回溯到 `skill_id`
- 必须稳定，不能依赖目标根目录推导
- `canonical_dir` 必须保持为相对 repo root 的安全路径，不能使用绝对路径，也不能包含 `.` / `..` 路径段跳出仓库

### 2. 后端部署包路径

- 必须指向后端专属的部署包目录或等价入口
- 必须能从原始来源追踪其生成来源
- 必须体现生成关系，而非手工约定

### 3. payload descriptor 位置

- 必须唯一
- 必须与 `skill_id` 和后端保持稳定的对应关系
- 只承载分发约定，不重复存储原始来源的内容

### 4. 目标入口命名

- 必须体现后端、skill 与入口角色
- 必须避免与原始来源路径冲突
- `target_dir`、`target_entry_name` 与 `required_payload_files` 必须保持为相对 target root 的安全路径，不能使用绝对路径，也不能包含 `.` / `..` 路径段跳出目标根
- 当前 live bindings 内，`target_dir` 必须唯一；这是一条运行时硬断言，不是测试侧建议

### 5. backend target root 规则

- target root 由 backend 自己解析
- operator-facing 主流程不再区分 `local/global` deploy mode
- install 只面向“当前 backend 的 resolved target root”

### 5.1 当前 `agents` target contract

- 当前 `agents` live install 仍按单个 skill 目录落在 backend target root 下
- 当前 `agents` skills 使用 `aw-{skill_id}` 作为 `payload.target_dir`，并通过 `legacy_target_dirs` 声明旧目录名用于升级清理
- 若未来要支持 nested target layout，必须先升级 deploy contract，再同步更新 runbook、verify 口径与测试矩阵

### 6. 必需部署文件

- 必须显式列出最小必需文件
- 对当前 `agents` payload，live install 至少应包含 target entry、顶层 `payload.json` 与 runtime-generated `aw.marker`
- 当前实现中，`aw.marker` 只表达 deploy 指纹：`marker_version / backend / skill_id / payload_version / payload_fingerprint`
- 缺失任一必需文件时，校验必须失败
- 必需文件只覆盖运行所需，不覆盖文档全量内容

### 7. 复制 / 软链接策略

- 必须显式声明采用复制、软链接（symlink）还是 canonical-copy 载体
- 策略必须能按后端判定
- 校验必须能识别策略偏离

### 8. 引用分发

- 必须显式声明引用（references）是否参与分发
- 若分发，必须说明是复制、链接还是只保留 metadata 指针
- 若不分发，校验不能将引用缺失视为失败

### 9. 校验项

校验至少检查以下内容：

- source 本身是否合法，例如 live bindings 是否出现重复 `target_dir`
- target root 是否存在、是否是目录、是否是坏链路
- 目标入口存在
- 目标入口类型正确
- 必需部署文件存在且可读
- `canonical_dir`、`canonical_paths` 与 `target_dir` 都留在各自声明的相对根目录内
- payload descriptor 的固定身份字段与当前 binding 一致，例如 `payload_version`、`backend`、`skill_id`
- payload descriptor 自身字段与实际部署包一致
- 复制 / 软链接策略与实际落点一致
- target root 下的 live install 是否与当前 source 对齐
- 是否存在 conflict / unrecognized 目录
- 各层之间是否出现不一致（drift）

## 四、不一致（drift）与错误码

### 不一致定义

出现下列任一情况，即视为不一致（drift）：

- 原始来源与后端部署包不一致
- payload descriptor 与后端部署包不一致
- 目标入口与 payload descriptor 不一致
- 必需部署文件缺失或类型错误
- 复制 / 软链接策略偏离约定
- 引用处理方式偏离 payload descriptor 声明

### 错误码

错误码只需先覆盖以下类别：

- `missing-canonical-source`：缺失原始来源
- `missing-backend-payload-source`：缺失后端部署包
- `missing-target-entry`：缺失目标入口
- `wrong-target-entry-type`：目标入口类型错误
- `missing-required-payload`：缺失必需部署文件
- `payload-policy-mismatch`：部署包策略不匹配
- `reference-policy-mismatch`：引用策略不匹配
- `payload-contract-invalid`：payload descriptor 字段、路径或目标约束不一致
- `unrecognized-target-directory`：目标目录存在，但没有可识别或可安全匹配的 runtime marker
- `target-payload-drift`：target payload 与当前 source 不一致
- `unexpected-managed-directory`：target root 下残留了带可识别 marker、但已不在当前 source live bindings 里的受管目录
- `unknown-target-root`：未知目标根目录

代码名仅作为可读分类，不要求在此定义完整的错误枚举体系。

## 五、install / prune 约束

- `prune --all` 只删除带可识别、且属于当前 backend 的受管 `aw.marker` 目录
- `check_paths_exist` 必须基于当前 source 声明的 live bindings 全量列出冲突路径；命令失败时不允许有业务写入
- `install` 只写当前 source 声明的 live payload
- `install` 不承接 archive/history、旧版本保活、增量修复，或“确认新目录可用再删旧目录”

## 六、`.aw_template` 边界

`.aw_template/` 不参与部署包分发，也不是 skill deploy source。

允许的提及方式：

- 作为边界说明，明确它不在 A1 的 skill deploy 链路中
- 作为 `.aw/` 目录结构与管理文档模板来源的说明对象，描述 deploy 后如何初始化 `.aw/`

禁止的提及方式：

- 将 `.aw_template/` 直接作为权威来源复制到目标
- 将 `.aw_template/` 当作部署包的默认来源
- 将 `.aw_template/` 当前目录中的模板文件位置，直接当作 skill owner 结论写进部署约定

## 七、验收标准

后续实现至少应满足：

- 仅凭本规范和 payload descriptor，即可实现当前最小 deploy 读取面
- 部署入口页可以直接引用本规范，无需再以"这里不定义映射"回避约定
- 校验能区分缺失、不一致、类型错误、source 非法和冲突目录
- destructive reinstall 流程不会把 foreign / unrecognized 目录当作可自动接管对象

## 八、保留项

以下内容留给后续任务包：

- payload contract：payload descriptor 的进一步收敛
- 模板工具：模板工具的生成约束
- `agents` payload：后端部署包的具体形态
- deploy：部署脚本的读取与同步行为
