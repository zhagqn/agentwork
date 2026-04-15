# 工作流脚本

此目录仅保留 **核心工作流脚本**。

可选工具（如 figma、browser、android、godot）需要的脚本，不再默认驻留在 `.shared/scripts/`；需要时应通过项目自己的工具安装流程按需引入。

## 当前核心脚本
### session-review.sh
用途：对照 session 的“当前批次工作集”与当前工作区实际改动，并检查“产出批次（提交锚点）”，辅助执行 `/review` 或 `/session review`

```bash
.shared/scripts/session-review.sh                # 审查最新 session
.shared/scripts/session-review.sh <session-id>  # 审查指定 session（不含 .md）
.shared/scripts/session-review.sh <path/to.md>  # 审查指定文件路径
```

## 可选工具脚本
可选工具脚本不属于核心 `.shared` 层；应通过项目自己的工具安装流程按需引入。
