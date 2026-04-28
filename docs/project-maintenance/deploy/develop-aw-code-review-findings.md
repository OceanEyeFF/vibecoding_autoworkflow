---
title: "develop-aw Code Review Findings"
status: superseded
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# develop-aw → develop-main Code Review 问题清单

> 审查日期: 2026-04-28
> 审查范围: 74 files, +4407/-285 lines, 26 commits
> 验证方式: 四通道并行审查（安全/架构/质量/性能）+ 逐项 double-check
> 说明: 本文档仅列出经 double-check 确认真实存在的问题，不包含解决方案。

Resolution status: superseded by the follow-up review-fix worktrack on `2026-04-28`; retained as audit evidence.

---

## 问题列表

### 1. AW_HARNESS_REPO_ROOT 缺少路径白名单验证

- **文件**: `toolchain/scripts/deploy/adapter_deploy.py`
- **行号**: 87-89 vs 96-101
- **分类**: 安全
- **严重度**: 中

`resolve_repo_root()` 中 `AW_HARNESS_REPO_ROOT` 环境变量的值被直接用作源根路径（`Path(override).expanduser().resolve()`），没有经过任何路径白名单验证。而 `resolve_target_repo_root()` 对 `AW_HARNESS_TARGET_REPO_ROOT` 使用了 `validate_target_repo_root` 进行了完整的三级白名单验证（精确敏感路径黑名单 + 递归敏感路径黑名单 + 允许列表）。两者形成不对称防护。

如果攻击者能控制 `AW_HARNESS_REPO_ROOT` 环境变量，可引导适配器从任意文件系统路径读取文件。

**当前代码** (`resolve_repo_root`, 第87-89行):
```python
override = os.environ.get("AW_HARNESS_REPO_ROOT")
if override:
    return Path(override).expanduser().resolve()  # 无验证
```

**对比** (`resolve_target_repo_root`, 第96-98行):
```python
target_override = os.environ.get("AW_HARNESS_TARGET_REPO_ROOT")
if target_override:
    return validate_target_repo_root(Path(target_override), source_root)  # 有验证
```

---

### 2. writeGithubEnv 非原子写入且无错误处理

- **文件**: `toolchain/scripts/deploy/bin/resolve-release-metadata.js`
- **行号**: 60-63
- **分类**: 安全/质量
- **严重度**: 中

`writeGithubEnv` 函数对同一文件连续三次调用 `appendFileSync`，每次对应一个环境变量。三次调用均无 try-catch。如果第一次或第二次写入成功但后续写入失败，`GITHUB_ENV` 文件将处于不完整状态——下游步骤可能读取到部分环境变量（如 `AW_INSTALLER_RELEASE_GIT_TAG` 已设置但 `AW_INSTALLER_RELEASE_CHANNEL` 缺失），导致行为异常。

**当前代码**:
```javascript
function writeGithubEnv(githubEnvPath, metadata) {
  appendFileSync(githubEnvPath, `AW_INSTALLER_RELEASE_GIT_TAG=${metadata.releaseTag}\n`);
  appendFileSync(githubEnvPath, `AW_INSTALLER_RELEASE_CHANNEL=${metadata.releaseChannel}\n`);
  appendFileSync(githubEnvPath, `NPM_CONFIG_TAG=${metadata.npmConfigTag}\n`);
}
```

---

### 3. publish.yml 缺少并发控制

- **文件**: `.github/workflows/publish.yml`
- **行号**: 1-12 (workflow 级别)
- **分类**: 安全
- **严重度**: 中

workflow 文件中没有 `concurrency` 组定义。如果两个 GitHub Release 几乎同时被创建（例如通过 API 批量操作），两个 workflow 实例可能并行运行，存在竞态发布风险。同时也没有 `timeout-minutes` 设置，job 可能无限挂起。

**当前代码** (workflow 头部):
```yaml
name: Publish aw-installer

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm
```

---

### 4. semverPattern 正则表达式在两个 JS 文件中重复定义

- **文件**: `toolchain/scripts/deploy/bin/check-root-publish.js:7-8`, `toolchain/scripts/deploy/bin/resolve-release-metadata.js:9-10`
- **分类**: 质量/架构
- **严重度**: 中

完全相同的复杂 semver 正则表达式（约 120 字符）在两个文件中独立定义和维护。如果 semver 校验逻辑需要更新，必须同时修改两处，存在不一致风险。`resolve-release-metadata.js` 已经 `require("./check-root-publish.js")` 导入了 `deriveReleaseChannelFromTag`，可以同样导入 `semverPattern`，但没有这样做。

**当前代码** (两处相同):
```javascript
const semverPattern =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/;
```

---

### 5. normalize_relative_* 薄包装函数通过字符串替换修改错误消息

- **文件**: `toolchain/scripts/deploy/adapter_deploy.py`
- **行号**: 461-474
- **分类**: 质量
- **严重度**: 中

`normalize_relative_canonical_path` 和 `normalize_relative_repo_path` 两个函数仅是对 `normalize_relative_target_path` 的薄包装，通过 `str(exc).replace("backend target root", "...")` 来修改异常消息中的上下文名词。如果 `normalize_relative_target_path` 的错误消息格式发生变化，替换逻辑会静默失效，导致用户看到包含 "backend target root" 字样的误导性错误消息。

**当前代码**:
```python
def normalize_relative_canonical_path(value, *, field_name, skill_id):
    try:
        return normalize_relative_target_path(value, field_name=field_name, skill_id=skill_id)
    except DeployError as exc:
        detail = str(exc).replace("backend target root", "canonical skill directory")
        raise DeployError(detail) from exc

def normalize_relative_repo_path(value, *, field_name, skill_id):
    try:
        return normalize_relative_target_path(value, field_name=field_name, skill_id=skill_id)
    except DeployError as exc:
        detail = str(exc).replace("backend target root", "repository root")
        raise DeployError(detail) from exc
```

---

### 6. main() 使用冗长 if-elif 链分派子命令

- **文件**: `toolchain/scripts/deploy/adapter_deploy.py`
- **行号**: 1883-1931
- **分类**: 质量
- **严重度**: 低

`main()` 函数约 60 行，通过 `args.mode` 的 if-elif 链分派 6 种不同的子命令（verify, diagnose, prune, check_paths_exist, install, update）。新增子命令需要修改 `main()` 自身，违反开闭原则。`verify` 和 `diagnose` 两个分支有重复的 `verify_backend` 调用模式。

**当前代码** (部分结构):
```python
if args.mode == "verify":
    ...
if args.mode == "diagnose":
    ...
if args.mode == "prune":
    ...
if args.mode == "check_paths_exist":
    ...
if args.mode == "install":
    ...
if args.mode == "update":
    ...
```

---

### 7. fail() 函数直接调用 process.exit(1) 导致不可测试

- **文件**: `toolchain/scripts/deploy/bin/check-root-publish.js`
- **行号**: 26-36
- **分类**: 质量
- **严重度**: 中

`fail()` 函数直接调用 `process.exit(1)` 终止进程。`runChecks` 函数依赖 `fail()`，因此任何包含 `runChecks` 调用的函数都无法被单元测试验证——测试进程会被直接终止而无法捕获断言结果。

**当前代码**:
```javascript
function fail(message) {
  console.error(message);
  process.exit(1);
}

function runChecks(checks) {
  for (const check of checks) {
    if (!check.test()) {
      fail(check.message());
    }
  }
}
```

---

### 8. parseBoolean 命名误导

- **文件**: `toolchain/scripts/deploy/bin/resolve-release-metadata.js`
- **行号**: 12-14
- **分类**: 质量
- **严重度**: 低

函数名为 `parseBoolean` 暗示能解析多种布尔表示形式，但实际只做了 `value === true || value === "true"` 的简单比较，不处理 `"1"`、`"yes"`、`"false"` 等常见表示形式。名称与实际行为不匹配，可能导致调用者误用。

**当前代码**:
```javascript
function parseBoolean(value) {
  return value === true || value === "true";
}
```

---

### 9. case.pop("expected") 在迭代中修改测试数据

- **文件**: `toolchain/scripts/test/test_publish_workflow_contract.py`
- **行号**: 112
- **分类**: 质量
- **严重度**: 低

`test_release_metadata_resolver_accepts_rc_stable_and_canary_shapes` 在 `for case in cases` 循环内调用 `case.pop("expected")` 修改了测试数据字典。虽然当前测试中字典仅迭代一次不会导致问题，但这种可变性模式在添加更多测试逻辑时可能引入微妙的 bug。

**当前代码**:
```python
for case in cases:
    expected = str(case.pop("expected"))  # 修改了原始数据
    completed = run_release_metadata_case(case)
```

---

### 10. BYTECODE_FREE_COMMAND_EXCLUDED_PATHS 硬编码日期文件名

- **文件**: `toolchain/scripts/test/governance_semantic_check.py`
- **行号**: 207
- **分类**: 质量
- **严重度**: 低

排除路径包含硬编码日期 `2026-04-23`。如果未来产生类似格式的历史日志文件（如 `codex-harness-manual-run-continuous-2026-05-01.md`），这个排除列表需要持续手动维护，容易遗漏。

**当前代码**:
```python
BYTECODE_FREE_COMMAND_EXCLUDED_PATHS = {
    "docs/project-maintenance/deploy/codex-harness-manual-run-continuous-2026-04-23.md",
}
```

---

### 11. publish-dry-run.js 进程被信号终止时无错误上下文

- **文件**: `toolchain/scripts/deploy/bin/publish-dry-run.js`
- **行号**: 24
- **分类**: 质量
- **严重度**: 低

当 `spawnSync` 返回 `completed.status === null`（进程被信号终止）时，仅返回退出码 1，但没有输出信号名称、stderr 内容等任何诊断信息，故障排查时缺少关键上下文。

**当前代码**:
```javascript
if (completed.error) {
    console.error(completed.error.message);
    return 1;
}
return completed.status === null ? 1 : completed.status;
```

---

### 12. setUp 每测试方法调用 _seed_fake_repo 导致大量冗余 I/O

- **文件**: `toolchain/scripts/deploy/test_adapter_deploy.py`
- **行号**: 26-56, 64-72
- **分类**: 性能
- **严重度**: 中

`setUp` 方法在每个测试方法（共 100 个）执行时都调用 `_seed_fake_repo()`，该方法使用 `shutil.copytree` 全量复制 `product/harness/adapters` 和 `product/harness/skills` 两个目录（约 414KB, 61 个文件）。100 个测试方法累计产生约 40MB 的冗余文件复制。没有使用 `setUpClass` 来共享只读的 fake repo 数据。

**当前代码**:
```python
class AdapterDeployTest(unittest.TestCase):
    def setUp(self) -> None:          # 每个测试方法都执行
        ...
        self._seed_fake_repo()       # 每次复制 ~414KB
        ...

    def _seed_fake_repo(self) -> None:
        shutil.copytree(
            self.source_repo_root / "product" / "harness" / "adapters",
            self.fake_repo_root / "product" / "harness" / "adapters",
        )
        shutil.copytree(
            self.source_repo_root / "product" / "harness" / "skills",
            self.fake_repo_root / "product" / "harness" / "skills",
        )
```

---

### 13. CI 中 deploy 回归测试被重复执行

- **文件**: `.github/workflows/publish.yml`
- **行号**: 59, 62
- **分类**: 性能
- **严重度**: 中

"Governance tests" 步骤运行 `pytest toolchain/scripts/test` 会收集所有 `test_*.py` 文件，包括 `toolchain/scripts/deploy/test_adapter_deploy.py`（unittest.TestCase 兼容）。随后的 "Deploy regression tests" 步骤运行 `unittest discover -s toolchain/scripts/deploy -p 'test_*.py'` 再次执行同一套测试（100 个测试方法）。同一套测试被执行了两次。

**当前代码**:
```yaml
- name: Governance tests
  run: PYTHONDONTWRITEBYTECODE=1 python -m pytest toolchain/scripts/test

- name: Deploy regression tests
  run: PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

---

### 14. publish.yml 无 CI 缓存策略

- **文件**: `.github/workflows/publish.yml`
- **分类**: 性能
- **严重度**: 低

workflow 文件中没有任何 `actions/cache` 配置。每次 CI 运行都从零开始：
- 下载并安装 pip 依赖（pytest, jsonschema）
- 下载并全局安装 `npm@11.5.1`

这些依赖在多次运行之间不会变化，每次重新下载浪费网络带宽和 CI 时间。

---

### 15. governance_semantic_check.py 同一文件被多次读取

- **文件**: `toolchain/scripts/test/governance_semantic_check.py`
- **行号**: 121, 152
- **分类**: 性能
- **严重度**: 低

`docs/harness/catalog/worktrack.md` 同时出现在 `SUBAGENT_DEFAULT_CONTRACT_PATHS`（第121行）和 `REVIEW_EVIDENCE_FOUR_LANE_CONTRACT_PATHS`（第152行）两个列表中。`check_subagent_dispatch_default_contract` 和 `check_review_evidence_four_lane_contract` 两个串行执行的函数各自独立读取并解析该文件。在 16 个串行 check 函数中，该文件被读取 2 次。

---

### 16. npm pack --dry-run 与 publish:dry-run 功能重叠

- **文件**: `.github/workflows/publish.yml`
- **行号**: 68, 71
- **分类**: 性能
- **严重度**: 低

`npm pack --dry-run --json` 和 `npm run publish:dry-run`（内部执行 `npm publish --dry-run`）存在功能重叠。`npm publish --dry-run` 内部已执行与 `npm pack --dry-run` 相同的打包验证，再加上发布权限检查。两个步骤存在冗余计算。

**当前代码**:
```yaml
- name: Root aw-installer package pack dry-run
  run: npm pack --dry-run --json

- name: Root aw-installer publish dry-run
  run: npm run publish:dry-run --silent
```

---

### 17. CI workflow 中硬编码工具版本号

- **文件**: `.github/workflows/publish.yml`
- **行号**: 29, 34, 39, 44
- **分类**: 质量
- **严重度**: 低

Python 版本 (`3.13`)、Node 版本 (`24`)、npm 版本 (`11.5.1`) 以及 pip upgrade 均硬编码在 workflow 中。版本升级时需要手动修改多处，没有集中管理的版本配置文件。

**当前代码**:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.13"
- uses: actions/setup-node@v4
  with:
    node-version: "24"
- run: npm install -g npm@11.5.1
- run: python -m pip install --upgrade pip pytest jsonschema
```

---

### 18. adapter_deploy.py 单文件过长

- **文件**: `toolchain/scripts/deploy/adapter_deploy.py`
- **行号**: 1-1940
- **分类**: 架构/质量
- **严重度**: 低

单个文件 1940 行，承载了 CLI 参数解析、路径验证、安装、验证、诊断、修剪、更新等全部职责。虽然函数拆分良好（每个函数职责单一），但文件作为单模块过于庞大，不利于快速定位和并行维护。

涉及的职责域：CLI 定义 (parse_args, add_backend_args), 上下文构建 (build_deploy_context), 路径验证 (validate_target_repo_root, normalize_*), 安装 (install_backend_payloads), 验证 (verify_backend, verify_deployed_skill), 诊断 (diagnostic_summary), 修剪 (prune_all_managed_target_dirs), 更新 (run_update_backend), 指纹计算 (compute_payload_fingerprint), Runtime Marker 管理。

---

### 19. generic-worker-skill 与 doc-catch-up-worker-skill 结构同源但无共享模板

- **文件**: `product/harness/skills/generic-worker-skill/SKILL.md`, `product/harness/skills/doc-catch-up-worker-skill/SKILL.md`
- **分类**: 架构
- **严重度**: 低

两个 Worker Skill 共享相同的章节模板（`概览` → `何时使用` → `输入约定` → `工作流` → `硬约束` → `预期输出` → `资源`），且部分硬约束文字高度相似。但两者之间没有任何共享模板引用或基类声明。如果添加第三个 worker skill，同样的结构会再次被复制。

相似硬约束示例：
- 两者都有"不要扩大任务范围" / "不要把未验证计划写成长期真相"
- 两者都有"不要修改 .aw/ 控制面" / "不要在 .agents/ 等目录写长期事实"
- 两者都有"不要替 Harness 选择下一步工作" / "不要替 gate-skill 做放行判断"

---

### 20. ensure_install_target_root 存在理论 TOCTOU 竞争窗口

- **文件**: `toolchain/scripts/deploy/adapter_deploy.py`
- **行号**: 335-348
- **分类**: 质量
- **严重度**: 低（理论风险，实际利用可能性极低）

`path.exists()` 检查和 `path.mkdir()` 操作之间存在时间窗口。如果另一个进程在检查后、创建前在目标路径创建了符号链接（而非目录），`path.mkdir(parents=True, exist_ok=True)` 将失败（`exist_ok=True` 仅忽略目录已存在的情况，不处理非目录文件/符号链接的情况）。实际利用场景极其有限。

**当前代码**:
```python
def ensure_install_target_root(path: Path) -> None:
    if path.is_symlink():       # 检查1: 时间 T1
        ...
    if path.exists():            # 检查2: 时间 T2
        ...
        return
    path.mkdir(parents=True, exist_ok=True)  # 操作: 时间 T3
```

---

### 21. GITHUB_REF_NAME 回退可能导致不明确的错误消息（信息性）

- **文件**: `toolchain/scripts/deploy/bin/resolve-release-metadata.js`
- **行号**: 71
- **分类**: 质量
- **严重度**: 信息性

`releaseTag` 的取值链为 `GITHUB_RELEASE_TAG || GITHUB_REF_NAME || ""`。当 `GITHUB_RELEASE_TAG` 未设置时回退使用 `GITHUB_REF_NAME`（可能是分支名如 `develop-aw`）。虽然后续 semver 验证会拒绝这类值，但错误消息不够明确——用户会看到 "must match package version" 而非 "缺少 GITHUB_RELEASE_TAG 环境变量"。

**当前缓解**: CI workflow 显式传入了 `GITHUB_RELEASE_TAG: ${{ github.event.release.tag_name }}`，正常发布流程中始终有值。回退逻辑仅在脚本独立运行时激活。实际风险极低。

---

### 22. publish-dry-run.js 在 Windows 平台启用 shell 模式（信息性）

- **文件**: `toolchain/scripts/deploy/bin/publish-dry-run.js`
- **行号**: 14
- **分类**: 安全
- **严重度**: 信息性

`shell: process.platform === "win32"` 在 Windows 平台通过 shell 执行 npm 命令，理论上面临更大的命令注入攻击面。但 CI workflow 运行在 `ubuntu-latest`，不会触发 Windows 路径。仅在本地 Windows 开发环境中可能生效。

---

## 统计摘要

| 严重度 | 数量 | 问题编号 |
|--------|------|---------|
| 中 | 8 | #1, #2, #3, #4, #5, #7, #12, #13 |
| 低 | 12 | #6, #8, #9, #10, #11, #14, #15, #16, #17, #18, #19, #20 |
| 信息性 | 2 | #21, #22 |

| 分类 | 数量 |
|------|------|
| 安全 | 3 (#1, #2, #3) |
| 质量 | 12 (#2, #4, #5, #6, #7, #8, #9, #10, #11, #17, #18, #20) |
| 性能 | 5 (#12, #13, #14, #15, #16) |
| 架构 | 3 (#4, #18, #19) |

> 注: #2 同时属于安全和质量分类, #4 同时属于质量和架构分类, #18 同时属于架构和质量分类。

---

## Double-check 验证记录

以下为上一轮审查中报告、但在 double-check 后被排除或降级的项目：

| 原始发现 | 验证结果 |
|---------|---------|
| gate-evidence.md 被两个 check 函数重复读取 | **不成立** — 该文件仅出现在 REVIEW_EVIDENCE_FOUR_LANE_CONTRACT_PATHS 一个列表中 |
| Scaffold package.json 版本从 0.0.0-local 变更为 0.4.0-rc.2 有问题 | **不成立** — 与根 package.json 版本一致是有意为之，用于 check-root-publish.js 版本校验 |
| DeployContext 有 God Object 倾向 | **保留为架构观察** — 当前仅 4 个字段，暂不构成实质问题 |
| worktrack.md 被 3 个 check 函数重复读取 | **部分成立** — 实际在 2 个列表中（非 3 个），已在 #15 中修正 |
