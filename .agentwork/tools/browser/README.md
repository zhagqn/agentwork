# Browser Tool Pack

## 类型
- skill
- external CLI integration (`agent-browser`)

## 内容
- shared browser skill
- browser-run.sh 统一入口脚本
- Codex / Claude / Cursor / Pi 平台入口（OpenCode 经 `.claude/skills` 兼容发现）

本工具包只分发 agentwork 自有的项目级契约、脚本与薄平台入口，不捆绑
`agent-browser` 的 CLI、源码、文档或许可证副本。

## 何时物化
- 项目需要浏览器自动化、表单交互、截图、抓取、PDF、state save 等能力
- 需要将浏览器产物统一落盘到项目 `.tmp/browser`

## 适配原则
- shared 主定义是 source of truth
- 各 AI 工具只保留入口说明，不复制主流程正文
- `agent-browser >= 0.26.0` 是完整动态 skill discovery 的兼容基线
- 建议使用最新稳定版；更旧版本仅通过 `--help` 提供 best-effort fallback
- 浏览器命令必须显式使用任务级 `AGENT_BROWSER_SESSION`；CDP 自动探测默认关闭，仅在 `BROWSER_CDP_PREFER=1` 时启用

外部 CLI 需单独安装，并继续适用其自身许可：
[agent-browser repository](https://github.com/vercel-labs/agent-browser) /
[Apache-2.0 license](https://github.com/vercel-labs/agent-browser/blob/main/LICENSE)。
