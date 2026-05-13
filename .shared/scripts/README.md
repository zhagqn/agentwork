# 工作流脚本

此目录仅保留 **核心工作流脚本**。

可选工具（如 figma、browser、android、godot）需要的脚本，不再默认驻留在 `.shared/scripts/`；需要时应通过项目自己的工具安装流程按需引入。

## 当前核心脚本
### agentwork-check.py
用途：检查 brain / plan / exec / review / session 工件是否满足核心 workflow 形态约束，辅助各命令在落盘后立即自检。

```bash
.shared/scripts/agentwork-check.py brain [brain-note]
.shared/scripts/agentwork-check.py plan [plan-file]
.shared/scripts/agentwork-check.py exec [plan-file]
.shared/scripts/agentwork-check.py review [review-note] [--fail-on-major]
.shared/scripts/agentwork-check.py session [session-ref] [--strict-flow]
.shared/scripts/agentwork-check.py latest brain|plan|review|session
.shared/scripts/agentwork-check.py self-test
```

### session-review.sh
用途：对照 session 的“当前批次工作集”与当前工作区实际改动，并检查“产出批次（提交锚点）”，辅助执行 `/review` 或 `/session review`

```bash
.shared/scripts/session-review.sh                # 审查最新 session
.shared/scripts/session-review.sh <session-ref> # 审查指定 session id 或文件路径
```

## Source Repo 说明
当前 source repo 可能因为已安装可选工具而额外出现脚本，例如 `arch-render.py`。

这些脚本不代表“核心 `.shared` 契约”回涨；它们的归属仍然是对应的 optional tool，应以工具安装入口和工具文档为准。

## 可选工具脚本
- 可选工具脚本不属于核心 `.shared` 层；应通过项目自己的工具安装流程按需引入
- 若某个脚本来自 optional tool，它可以物理存在于 `.shared/scripts/`，但语义上仍不属于核心工作流脚本
