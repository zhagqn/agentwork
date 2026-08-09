# Bootstrap

Bootstrap 是新项目复用 agentwork 核心工作流时的启动层源。

> 所有 bootstrap 目标文件都由 `spec.json` + `render_bootstrap.py` 生成；默认不要手工改生成结果。

它负责提供：
- 轻量 `AGENTS.md`
- `.shared/` 核心工作流层
- Claude / OpenCode / Cursor / Codex 的平台入口（默认全部安装）
- Codex 项目级 `luna_worker` 执行型子代理及其受管注册块

安装入口：根目录 `install-bootstrap.py`

安装时会删除可识别为 agentwork 生成的旧平台入口；同路径的项目自定义文件和符号链接会保留并报告，不按路径直接删除。

## Bootstrap does
- 安装核心 `.shared`
- 安装不同 AI 助手的最小启动文件
- OpenCode command 只逐文件刷新受管 wrapper，不替换整个 `.opencode/commands/` 目录
- Codex agent 逐文件刷新，`.codex/config.toml` 仅更新 agentwork 受管块，不覆盖其他项目配置或 agent
- 增量补充 `.gitignore`，确保 `.tmp/` 默认不进版本控制
- 保持核心 bootstrap 输出一致；source repo 仅允许 source-only 附加入口
- 通过 block 更新 `.shared/project/index.md` 与 `.shared/session/README.md`

## Bootstrap does NOT
- 不安装可选工具
- 不自动配置 MCP
- 不自动生成 `opencode.json*` 或配置 OpenCode Provider、model、agent、skill、plugin
- 不导入 session / task state

## 示例
```bash
python3 install-bootstrap.py -p <path>
python3 install-bootstrap.py -p .
```

> `-p .` 可用于 `agentwork` 源仓库自身的原地自刷新：
> - 相同路径的核心 `.shared` 文件会直接跳过
> - 根目录适配层（`AGENTS.md`、`.claude/`、`.opencode/commands/*.md`、`.cursor/`、`.codex/skills/`、`.codex/agents/*` 与 `.codex/config.toml` 受管块）会按最新 source 重新落地
> - `.shared/project/index.md` 与 `.shared/session/README.md` 的 managed block 仍会刷新
