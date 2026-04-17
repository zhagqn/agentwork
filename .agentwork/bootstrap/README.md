# Bootstrap

Bootstrap 是新项目复用 agentwork 核心工作流时的启动层源。

> 所有 bootstrap 目标文件都由 `spec.json` + `render_bootstrap.py` 生成；默认不要手工改生成结果。

它负责提供：
- 轻量 `AGENTS.md`
- `.shared/` 核心工作流层
- Claude / Antigravity / Cursor / Codex / VS Code Copilot 的薄封装入口（默认全部安装）

安装入口：根目录 `install-bootstrap.py`

## Bootstrap does
- 安装核心 `.shared`
- 安装不同 AI 助手的最小启动文件
- 增量补充 `.gitignore`，确保 `.tmp/` 默认不进版本控制
- 保持 source repo 与目标项目输出一致
- 通过 block 更新 `.shared/project/index.md` 与 `.shared/session/README.md`

## Bootstrap does NOT
- 不安装可选工具
- 不自动配置 MCP
- 不导入 session / task state

## 示例
```bash
python3 install-bootstrap.py -p <path>
python3 install-bootstrap.py -p .
```

> `-p .` 可用于 `agentwork` 源仓库自身的原地自刷新：
> - 相同路径的核心 `.shared` 文件会直接跳过
> - 根目录适配层（`AGENTS.md`、`.claude/`、`.agent/`、`.cursor/`、`.github/`）会按最新 source 重新落地
> - `.shared/project/index.md` 与 `.shared/session/README.md` 的 managed block 仍会刷新
