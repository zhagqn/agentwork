# Bootstrap

Bootstrap 是新项目复用 agentwork 核心工作流时的启动层源。

> 所有 bootstrap 目标文件都由 `spec.json` + `render_bootstrap.py` 生成；默认不要手工改生成结果。

它负责提供：
- 轻量 `AGENTS.md`
- `.shared/` 核心工作流层
- Claude / OpenCode / Cursor / Codex / Pi 的平台入口（默认全部安装）
- anydoc 默认文档输入能力；运行时 npm 依赖按项目需要延迟安装
- research 默认调研能力；只分发 routing 契约，remote provider 仍需单独安装
- Codex 项目级 `luna_worker` 执行型子代理及其受管注册块

安装入口：根目录 `install-bootstrap.py`

安装时会删除可识别为 agentwork 生成的旧平台入口；同路径的项目自定义文件和符号链接会保留并报告，不按路径直接删除。对于曾由 core bootstrap receipt 管理的退役 wrapper，历史 receipt 存在时只有对应路径的哈希仍匹配才视为受管；路径未记录或哈希变化都会保留，生成标记只用于没有历史 receipt 的旧 core 安装。

## Bootstrap does
- 安装核心 `.shared`
- 安装不同 AI 助手的最小启动文件
- OpenCode command 只逐文件刷新受管 wrapper，不替换整个 `.opencode/commands/` 目录
- Pi prompt 只按 spec 精确安装 `.pi/prompts/{brain,plan,exec,review,case,commit}.md`，不通过目录 glob 分发残留文件，也不接管整个 `.pi/` 或 `.pi/prompts/`
- Codex agent 逐文件刷新，`.codex/config.toml` 仅更新 agentwork 受管块，不覆盖其他项目配置或 agent
- 增量补充 `.gitignore`，确保 `.tmp/` 默认不进版本控制
- 保持核心 bootstrap 输出一致；source repo 仅允许 source-only 附加入口
- 通过 block 更新 `.shared/project/index.md` 与 `.shared/case/README.md`

## Bootstrap does NOT
- 不安装可选工具包的运行时依赖；anydoc 的 npm 包仍由 agent 在项目中按需安装
- 默认能力只分发规则正文：不安装 MCP server、CLI 或二进制，不创建或修改 `.env`，不修改平台 MCP 私有配置，不向远程服务发送私有资料或凭据
- 不自动配置 MCP
- 不自动生成 `opencode.json*` 或配置 OpenCode Provider、model、agent、skill、plugin
- 不安装 Pi / Node / package / extension / plan-mode / subagent，不修改 `~/.pi`、`.pi/settings.json` 或项目 trust，也不自动为可选工具增加 Pi 入口
- 不导入平台对话或既有任务状态

## 示例
```bash
python3 install-bootstrap.py -p <path>
python3 install-bootstrap.py -p .
```

Pi 项目 prompt 的 canonical source 是 `.agentwork/bootstrap/pi/prompts/*`。使用安装后的入口时需从目标仓库根启动 Pi 并信任该项目；非交互模式是否传入 `--approve` 由调用者基于项目可信度决定，该参数不提供 sandbox 或工具级审批。

> `-p .` 可用于 `agentwork` 源仓库自身的原地自刷新：
> - 相同路径的核心 `.shared` 文件会直接跳过
> - 根目录适配层（`AGENTS.md`、`.claude/`、`.opencode/commands/*.md`、`.cursor/`、`.codex/skills/`、`.codex/agents/*`、`.codex/config.toml` 受管块与 `.pi/prompts/*.md`）会按最新 source 重新落地
> - `.shared/project/index.md` 与 `.shared/case/README.md` 的 managed block 仍会刷新
