---
title: "Deploy Mapping Spec"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Deploy Mapping Spec

> 目的：定义部署流程中 `原始来源 -> 后端部署包 -> 清单 -> 目标入口 -> 校验` 这条链路的最小操作者约定。

本页属于 [Deploy Runbooks](./README.md) 系列。

阅读前请先了解以下基础文档：

- [根目录分层](../foundations/root-directory-layering.md)
- [Deploy Runbook](./deploy-runbook.md)
- [Skill 生命周期维护](./skill-lifecycle.md)

## 一、范围

本规范只定义部署相关的映射约定：

- 如何识别 skill 的原始来源
- 如何从原始来源派生出后端部署包
- 清单如何描述可分发对象
- 目标入口如何命名与落点
- 如何校验分发结果

本规范不定义：

- `adapter_deploy.py` 的实现细节
- 清单的概念体系扩展
- `.aw_template/` 的生成系统
- B1 / B2 / B3 / B4 的具体实现
- `claude` / `opencode` 等后端的后续细节

## 二、术语与链路

规范链路如下：

`原始来源 -> 后端部署包 -> 清单 -> 目标入口 -> 校验`

各环节定义：

- **原始来源（canonical source）**
  - 路径示例：`product/harness/skills/<skill>/SKILL.md` 或该 skill 的规范入口文件
  - 是 skill 的唯一权威来源，所有衍生内容都从这里产生
- **后端部署包（backend payload source）**
  - 路径示例：`product/harness/adapters/<backend>/skills/<skill>/`
  - 是面向具体后端的分发载体，由原始来源生成，不是权威来源
- **清单（manifest）**
  - 路径示例：`product/harness/manifests/<backend>/skills/<skill>.md` 或同层约定路径
  - 只描述分发与校验所需的最小信息
- **目标入口（target entry）**
  - `repo-local` 或 `global` 目标根目录下的最终落点
  - 是运行时可见的入口，只读，不回写原始来源
- **校验（verify）**
  - 检查目标入口、部署包文件以及各层之间是否一致

## 三、最小字段

### 1. 原始来源路径

- 必须能唯一定位 skill 的原始来源
- 必须能回溯到 `skill_id`
- 必须稳定，不能依赖目标根目录推导

### 2. 后端部署包路径

- 必须指向后端专属的部署包目录或等价入口
- 必须能从原始来源追踪其生成来源
- 必须体现生成关系，而非手工约定

### 3. 清单位置

- 必须唯一
- 必须与 `skill_id` 和后端保持稳定的对应关系
- 只承载分发约定，不重复存储原始来源的内容

### 4. 目标入口命名

- 在 repo-local 与 global 目标中必须保持同义
- 必须体现后端、skill 与入口角色
- 必须避免与原始来源路径冲突

### 5. repo-local / global 目标规则

- `repo-local` 目标只落在仓库内约定的运行时根目录
- `global` 目标只落在用户级的运行时根目录
- 两者共享同一命名逻辑，差异仅在根目录作用域

### 6. 必需部署文件

- 必须显式列出最小必需文件
- 缺失任一必需文件时，校验必须失败
- 必需文件只覆盖运行所需，不覆盖文档全量内容

### 7. 复制 / 软链接策略

- 必须显式声明采用复制、软链接（symlink）还是 thin-shell 载体
- 策略必须能按后端和目标作用域判定
- 校验必须能识别策略偏离

### 8. 引用分发

- 必须显式声明引用（references）是否参与分发
- 若分发，必须说明是复制、链接还是仅保留引用指针
- 若不分发，校验不能将引用缺失视为失败

### 9. 校验项

校验至少检查以下内容：

- 目标入口存在
- 目标入口类型正确
- 必需部署文件存在且可读
- 清单约束与实际部署包一致
- 复制 / 软链接策略与实际落点一致
- 各层之间是否出现不一致（drift）

## 四、不一致（drift）与错误码

### 不一致定义

出现下列任一情况，即视为不一致（drift）：

- 原始来源与后端部署包不一致
- 清单与后端部署包不一致
- 目标入口与清单不一致
- 必需部署文件缺失或类型错误
- 复制 / 软链接策略偏离约定
- 引用处理方式偏离清单声明

### 错误码

错误码只需先覆盖以下类别：

- `missing-canonical-source`：缺失原始来源
- `missing-backend-payload-source`：缺失后端部署包
- `missing-manifest`：缺失清单
- `missing-target-entry`：缺失目标入口
- `wrong-target-entry-type`：目标入口类型错误
- `missing-required-payload`：缺失必需部署文件
- `payload-policy-mismatch`：部署包策略不匹配
- `reference-policy-mismatch`：引用策略不匹配
- `manifest-payload-drift`：清单与部署包不一致
- `unknown-target-root`：未知目标根目录

代码名仅作为可读分类，不要求在此定义完整的错误枚举体系。

## 五、`.aw_template` 边界

`.aw_template/` 不参与部署包分发，也不是部署来源。

允许的提及方式：

- 作为边界说明，明确它不在 A1 的部署链路中
- 作为清单的 `template_inputs` 引用，表示某个 skill 依赖哪些模板类型

禁止的提及方式：

- 将 `.aw_template/` 直接作为权威来源复制到目标
- 将 `.aw_template/` 当作部署包的默认来源
- 将 `.aw_template/` 的生命周期细节提前写进部署约定

## 六、验收标准

后续实现至少应满足：

- 仅凭本规范和清单，即可实现 B1 / B3 / B4 的最小读取面
- 部署入口页可以直接引用本规范，无需再以"这里不定义映射"回避约定
- 校验能区分缺失、不一致、类型错误和策略偏离

## 七、保留项

以下内容留给后续任务包：

- B1：清单 schema 的正式落地
- B2：模板工具的生成约束
- B3：agents 后端部署包的具体形态
- B4：部署脚本的读取与同步行为
