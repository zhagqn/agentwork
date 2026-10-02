# 工作流脚本

此目录仅保留 **核心工作流脚本**。

可选工具（如 figma、browser、android、godot）需要的脚本，不再默认驻留在 `.shared/scripts/`；需要时应通过项目自己的工具安装流程按需引入。

## 当前核心脚本
### agentwork-check.py
用途：检查 brain / spec / exec / audit / Case 工件是否满足核心 workflow 形态约束，辅助各命令在落盘后立即自检。

```bash
.shared/scripts/agentwork-check.py brain [brain-note]
.shared/scripts/agentwork-check.py spec [spec-file]
.shared/scripts/agentwork-check.py exec [spec-file]
.shared/scripts/agentwork-check.py audit [audit-note] [--fail-on-major]
.shared/scripts/agentwork-check.py case [case-ref] [--strict-flow]
.shared/scripts/agentwork-check.py latest brain|spec|audit|case
.shared/scripts/agentwork-check.py self-test
```

- `spec`：除标题与占位符外，要求 `## 决策` 下有唯一的 `D{n}` 编号决策；任务行带唯一的 `T{n}` 编号且含 `覆盖` 与 `验证` 字段，`验证` 不能是 `待定` / `TBD` / `无` / `（待确认）` 这类占位；字段分隔符与冒号接受半角或全角，任务行须单行，`[X]` 视同已完成，无法识别的 checkbox 标记报错；每个决策至少被一个任务覆盖，引用编号必须存在，依赖只接受 `无` 或逗号 / 顿号分隔的 `T{n}` 列表，占位或无法解析的值报错，不能指向自身或形成环。spec 在 `.tmp/` 下默认不提交，不把本机最新工件加入 `verify.sh`。
- 任务字段补充：所有入口拒绝重复字段（`task_duplicate_field`）；覆盖只接受逗号 / 顿号分隔的逐个 `D{n}` 编号，范围或其他混合文本报 `task_invalid_coverage`。spec/exec 可省略 `完成`，显式填写时不能空白或占位；Case 仍要求完整字段。
- `exec`：在 `spec` 规则基础上，要求至少一个任务已勾选，且已勾选任务的依赖也已勾选。只用于未写入 Case 的 spec；Case 模式下 spec 已冻结，改用 `case --strict-flow`。
- `audit`：要求 `## 结论` 下分别给出以 `通过` / `不通过` 开头的 `规格符合` 与 `质量规范` 结论（标签可加粗）；Findings 严重度分节（`###` / `####` 标题或单独一行的粗体标签，可带括号说明）或带严重度前缀列表中的每个问题都要以 `[规格]` / `[质量]` 类别开头并有有效处置，拒绝需括号内的具体理由；缩进的续行与证据子项归入上一条问题，带 `[规格]` / `[质量]` 标签的嵌套项仍按独立问题检查；`--fail-on-major` 时任一结论不通过或 Critical / Important 非空即失败。
- audit 类别标签可加粗；嵌套识别与类别校验使用相同规则，`**[规格]**` / `**[质量]**` 嵌套项必须独立提供处置，不能借用父问题的处置。
- `case --strict-flow`：所有 Case 一律校验完整任务契约（决策只取自 `### 已选方案`；覆盖、完成、验证、编号唯一、依赖无环及完成顺序），不读取被冻结的临时 spec；未编号的旧 Case 不再兼容，需手动补齐。
- 模板占位符：`TEMPLATE_PLACEHOLDERS` 与 `.shared/templates/*.md` 中的 `{...}` 保持同步，由 source repo 测试校验。
- `latest` 只认 `.tmp/agentwork/{brain,spec,audit}/` 与 `.shared/case/`；旧 `.tmp/agentwork/plan|review/` 不参与选取，也不自动迁移。

### command-preview.sh
用途：对未知或可能很大的命令输出做统一 preview，优先保护上下文体积，同时保留底层命令退出码。

默认策略：
- 合并 `stdout` / `stderr` 后落临时文件
- 输出 `exit` / `bytes` / `lines` 元信息
- 总量不超过 `4000` bytes 时返回全文
- 超过阈值时返回首尾采样，默认各 `2000` bytes

```bash
.shared/scripts/command-preview.sh -- git diff
.shared/scripts/command-preview.sh -- rg -n TODO src
.shared/scripts/command-preview.sh --max-bytes 6000 -- python3 script.py
```

当 preview 不足以定位问题时，优先：
- 收窄原命令范围
- 再次调用脚本并调整 `--max-bytes`
- 或按行号 / 偏移重新抓取定向片段

### case-audit.sh
用途：对照 Case 的“当前批次工作集”与当前工作区实际改动，并检查“产出批次（提交锚点）”。支持一条产出记录聚合多个相关提交，区分当前仓、独立仓和当前仓不可验证的历史锚点；不可验证不等于应删除，辅助执行 `/audit` 或 `/case audit`

```bash
.shared/scripts/case-audit.sh            # 审查最新 Case
.shared/scripts/case-audit.sh <case-ref> # 审查指定 Case id 或文件路径
```

“最新”按文件名时间戳选择，不使用修改时间：

- 只有符合 `YYYYMMDD-HHMM-slug.md` 的工件参与选取；命名不符的草稿（含 `README.md`）一律不被选中
- 同一 `YYYYMMDD-HHMM` 存在多个候选时不做兜底排序，直接报 `ambiguous_latest` 并要求显式指定
- `case-audit.sh` 与命令自检共用这一个入口，不存在第二套选取规则
Git 路径使用 NUL 记录解析；换行等控制字符仅在输出时转义。工作集可用目录或 glob 覆盖含换行的文件名。
已存在或在 Git status 中出现的精确路径优先按字面匹配（如 `src/[id].tsx`），其余范围才解释为 glob。

## Source Repo 说明
`verify.sh` 仅用于 source repo，聚合测试、渲染检查、workflow self-test 与 Case 检查，不随 bootstrap 分发。目标项目直接使用 `agentwork-check.py self-test` 与对应工件检查。无 Case 可跳过；latest 歧义或执行失败必须令聚合门禁失败。

当前 source repo 可能因为已安装可选工具而额外出现脚本，例如 `arch-render.py`。

这些脚本不代表“核心 `.shared` 契约”回涨；它们的归属仍然是对应的 optional tool，应以工具安装入口和工具文档为准。

## 命名约定
- 脚本名优先使用 `domain-action` 或 `domain-context-action`，例如 `agentwork-check.py`、`case-audit.sh`、`figma-desktop-mcp-check.sh`
- 当脚本只适用于某个运行环境或 fallback 路径时，在名称中写明 context，避免被误认为通用入口
- Python 适合结构化校验、文件生成、JSON / Markdown 处理和跨平台逻辑
- Shell 适合很薄的命令包装、环境探测和调用系统工具

## 可选工具脚本
- 可选工具脚本不属于核心 `.shared` 层；应通过项目自己的工具安装流程按需引入
- 若某个脚本来自 optional tool，它可以物理存在于 `.shared/scripts/`，但语义上仍不属于核心工作流脚本
