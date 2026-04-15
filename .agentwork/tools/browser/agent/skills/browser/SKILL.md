---
name: browser
description: 浏览器自动化（轻量入口）。当需要访问网页、交互、填表、截图或提取页面信息时使用。
---

# browser

浏览器自动化技能（轻量入口）。

## 执行规则

- 先读取：`.shared/skills/browser/SKILL.md`
- 本仓库执行时统一通过：`.shared/skills/browser/scripts/browser-run.sh`
- 先 `tab list` + `get url` 确认当前页面；仅在需要跳转时执行 `open`
- 交互流程：`snapshot -i` → `@ref` 交互 → 页面变化后重抓 `snapshot -i`
- 不在本文件维护子命令清单；命令细节以上游 references 和 `agent-browser --help` 为准
