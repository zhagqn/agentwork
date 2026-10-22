# Bootstrap

Bootstrap 是新项目复用 agentwork 核心工作流时的启动层源。

> 生成式入口由 `spec.json` + `render_bootstrap.py` 维护，不手工改生成结果。research 的平台入口是单独维护的手写薄指针；其余默认能力沿用各自的生成与分发方式。

它负责提供：
- 轻量 `AGENTS.md`
- `.shared/` 核心工作流层
- Claude / OpenCode / Cursor / Codex / Pi / dsh 的平台入口（默认全部安装）
- anydoc 默认文档输入能力；运行时 npm 依赖按项目需要延迟安装
- research 默认调研能力；只分发 routing 契约，remote provider 仍需单独安装
- Codex 项目级 skill 入口；不安装或注册自定义子代理

安装入口：根目录 `install-bootstrap.py`

安装时会删除可识别为 agentwork 生成的旧平台入口；同路径的项目自定义文件和符号链接会保留并报告，不按路径直接删除。对于曾由 core bootstrap receipt 管理的退役 wrapper，历史 receipt 存在时只有对应路径的哈希仍匹配才视为受管；路径未记录或哈希变化都会保留，生成标记只用于没有历史 receipt 的旧 core 安装。

## Bootstrap does
- 安装核心 `.shared`
- 安装不同 AI 助手的最小启动文件
- OpenCode command 只逐文件刷新受管 wrapper，不替换整个 `.opencode/commands/` 目录
- Pi prompt 只按 spec 精确安装 `.pi/prompts/{brain,spec,exec,audit,case,commit}.md`，不通过目录 glob 分发残留文件，也不接管整个 `.pi/` 或 `.pi/prompts/`
- dsh 精确安装 `.dsh/skills/{brain,spec,exec,audit,case,commit,anydoc,research}/SKILL.md` 八个薄入口，沿用文件级预检、哈希收据和回滚；不接管整个 `.dsh/`，保留用户配置、额外技能和同级资源
- 旧 Codex 子代理按所有权证据退役，仅移除已知未改写的注册块；自定义配置、改写文件与仍被引用的文件保留并报告
- 增量补充 `.gitignore`，确保 `.tmp/` 默认不进版本控制
- 保持核心 bootstrap 输出一致；source repo 仅允许 source-only 附加入口
- 通过 block 更新 `.shared/project/index.md` 与 `.shared/case/README.md`

## Bootstrap does NOT
- 不安装可选工具包的运行时依赖；anydoc 的 npm 包仍由 agent 在项目中按需安装
- 默认能力只分发规则正文：不安装 MCP server、CLI 或二进制，不创建或修改 `.env`，不修改平台 MCP 私有配置，不向远程服务发送私有资料或凭据
- 不自动配置 MCP
- 不自动生成 `opencode.json*` 或配置 OpenCode Provider、model、agent、skill、plugin
- 不安装 Pi / Node / package / extension / plan-mode / subagent，不修改 `~/.pi`、`.pi/settings.json` 或项目 trust，也不自动为可选工具增加 Pi 入口
- 不安装 dsh 或修改其 Desktop profile、模型、凭据、原生计划模式、goal、schedule、权限预设；不为可选工具自动创建 dsh MCP 接线
- 不导入平台对话或既有任务状态

## 示例
```bash
python3 install-bootstrap.py -p <path>
python3 install-bootstrap.py -p .
```

Pi 项目 prompt 的 canonical source 是 `.agentwork/bootstrap/pi/prompts/*`。使用安装后的入口时需从目标仓库根启动 Pi 并信任该项目；非交互模式是否传入 `--approve` 由调用者基于项目可信度决定，该参数不提供 sandbox 或工具级审批。

dsh 的可分发源位于 `.agentwork/bootstrap/dsh/skills/`：六命令复用 wrappers 元数据生成，anydoc 生成共享正文的薄入口，research 保持手写薄指针；不复制 `.shared/` 工作流正文。使用官方 Desktop 时打开目标项目根、新建标准模式会话并保持原生计划模式关闭；`/spec` 是 agentwork 规格入口，原生 `/plan` 不能替代它。入口按技能资源目录向上三级定位项目根，再读取 `AGENTS.md` 的启动必读和共享定义，并保留用户原始参数。

dsh 机制基线为 `@deepseek-ai/dsh@0.2.1-rc.2`，tag commit 为 `687f282e8625c6b8d11ff58211a90524be2e4317`。仓库回归、固定发布包加载检查、真实 Desktop/model 任务验收分开记录；官方 Desktop `0.2.1-rc.2` 标准模式已用公开夹具完成核心流程受控验收（2026-10-22），覆盖八入口、根规则、brain/spec、exec/audit、同夹具第二会话 Case 加载与真实提交请求/取消。权限提示、可选工具、PTC、SSH 与自动续跑未覆盖；升级后须重新验证。

> `-p .` 可用于 `agentwork` 源仓库自身的原地自刷新：
> - 相同路径的核心 `.shared` 文件会直接跳过
> - 根目录适配层（`AGENTS.md`、`.claude/`、`.opencode/commands/*.md`、`.cursor/`、`.codex/skills/`、`.pi/prompts/*.md` 与八个 `.dsh/skills/*/SKILL.md`）会按最新 source 重新落地
> - `.shared/project/index.md` 与 `.shared/case/README.md` 的 managed block 仍会刷新
