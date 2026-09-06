# 工作流脚本

此目录仅保留 **核心工作流脚本**。

可选工具（如 figma、browser、android、godot）需要的脚本，不再默认驻留在 `.shared/scripts/`；需要时应通过项目自己的工具安装流程按需引入。

## 当前核心脚本
### agentwork-check.py
用途：检查 brain / plan / exec / review / Case 工件是否满足核心 workflow 形态约束，辅助各命令在落盘后立即自检。

```bash
.shared/scripts/agentwork-check.py brain [brain-note]
.shared/scripts/agentwork-check.py plan [plan-file]
.shared/scripts/agentwork-check.py exec [plan-file]
.shared/scripts/agentwork-check.py review [review-note] [--fail-on-major]
.shared/scripts/agentwork-check.py case [case-ref] [--strict-flow]
.shared/scripts/agentwork-check.py latest brain|plan|review|case
.shared/scripts/agentwork-check.py self-test
```

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

### case-review.sh
用途：对照 Case 的“当前批次工作集”与当前工作区实际改动，并检查“产出批次（提交锚点）”。支持一条产出记录聚合多个相关提交，区分当前仓、独立仓和当前仓不可验证的历史锚点；不可验证不等于应删除，辅助执行 `/review` 或 `/case review`

```bash
.shared/scripts/case-review.sh            # 审查最新 Case
.shared/scripts/case-review.sh <case-ref> # 审查指定 Case id 或文件路径
```

“最新”按修改时间选择（同时间按路径排序），排除 `README.md`，与命令自检一致。
Git 路径使用 NUL 记录解析；换行等控制字符仅在输出时转义。工作集可用目录或 glob 覆盖含换行的文件名。
已存在或在 Git status 中出现的精确路径优先按字面匹配（如 `src/[id].tsx`），其余范围才解释为 glob。

## Source Repo 说明
当前 source repo 可能因为已安装可选工具而额外出现脚本，例如 `arch-render.py`。

这些脚本不代表“核心 `.shared` 契约”回涨；它们的归属仍然是对应的 optional tool，应以工具安装入口和工具文档为准。

## 命名约定
- 脚本名优先使用 `domain-action` 或 `domain-context-action`，例如 `agentwork-check.py`、`case-review.sh`、`figma-desktop-mcp-check.sh`
- 当脚本只适用于某个运行环境或 fallback 路径时，在名称中写明 context，避免被误认为通用入口
- Python 适合结构化校验、文件生成、JSON / Markdown 处理和跨平台逻辑
- Shell 适合很薄的命令包装、环境探测和调用系统工具

## 可选工具脚本
- 可选工具脚本不属于核心 `.shared` 层；应通过项目自己的工具安装流程按需引入
- 若某个脚本来自 optional tool，它可以物理存在于 `.shared/scripts/`，但语义上仍不属于核心工作流脚本
