---
name: browser
description: Use agentwork's project browser wrapper for web navigation, interaction, capture, extraction, and local web verification. Use when a Pi task needs browser automation or visual page state.
compatibility: Requires agent-browser 0.26.0 or newer on PATH and an explicitly chosen task-scoped AGENT_BROWSER_SESSION.
---

# browser

Pi 项目级 browser 技能入口。

## 执行前必读

- 按 Pi 的 skill 相对路径规则完整读取：`../../../.shared/skills/browser/SKILL.md`
- 保持当前工作目录为仓库根，并通过 `.shared/skills/browser/scripts/browser-run.sh` 执行
- 为当前任务选择一个短且唯一的 `AGENT_BROWSER_SESSION`，并在本任务每次调用时复用；不要跨任务复用默认浏览器状态。
- 不直接调用 `agent-browser` 绕过项目产物目录、CDP 与会话隔离契约。

本入口不安装 CLI、不修改 `.pi/settings.json`，也不提供或恢复浏览器登录状态。
