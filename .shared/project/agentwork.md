# Project: agentwork

## 适用范围
- 涉及 `agentwork` source repo 自身维护时使用
- 常见命中目录/入口：`.shared/`、`.agentwork/`、`install-bootstrap.py`、`install-tool.py`

## TL;DR
- 本仓库是 `agentwork` 的 source repo，不是直接业务项目模板
- 核心职责：维护可复用工作流、默认文档输入能力和可选工具源
- source repo 自身也按目标项目结构自承载 bootstrap
- `install-bootstrap.py` 只同步核心工作流，不会把已安装的可选工具自动扩散到目标项目

## 长期约束与约定

### Build / Test
- 原地刷新核心工作流：`python3 install-bootstrap.py -p .`
- 命令内建 harness 自检：`python3 .shared/scripts/agentwork-check.py self-test`
- 真实 provider E2E 只作为人工 smoke / 兼容性调查，不作为默认回归或合并 gate
- 核心 workflow 检查优先沉淀到 `.shared/scripts/`；历史集成诊断只保留专题语境
- `.shared/scripts/verify.sh` 是 source-only 聚合门禁，不分发到目标项目；历史副本只在旧 bootstrap 收据摘要匹配时退役，用户改写保留。目标项目使用 `agentwork-check.py self-test` 与显式工件检查。
- 若修改 bootstrap 生成契约，优先同步 `.agentwork/bootstrap/*` 与命令内建 harness

### 代码与目录约定
- `.shared/`：项目可同步的核心工作流契约
- `.agentwork/bootstrap/`：迁移到其他 AI 助手的基础文件源
- `.opencode/commands/`：OpenCode 核心工作流薄 wrapper，由 bootstrap 生成并在 source repo 自承载
- `.agentwork/bootstrap/pi/prompts/`：Pi 项目 prompt 的 canonical 生成产物
- `.pi/prompts/`：Pi 核心工作流薄 wrapper，由 bootstrap 生成并在 source repo 自承载
- `.pi/skills/`：source repo 中默认或显式安装的 Pi skill 入口；anydoc 与 research 属于核心 bootstrap，其余 optional tool 仍需显式安装
- Codex 自定义子代理由项目自行管理，bootstrap 不分发 agent 文件或注册配置
- `.agentwork/tools/`：可选工具源（figma/browser/android/godot/...）
- `.tmp/`：核心 workflow 和可选工具的临时工件；核心 workflow 默认使用 `.tmp/agentwork/*`

### 兼容性 / 运行时红线
- 不默认依赖任何特定 runtime
- anydoc 与 research 的共享规则属于核心 `.shared/skills/{anydoc,research}`；其他可选工具不直接长期驻留在 `.shared`
- `.tmp/*` 默认不纳入提交，除非明确保留证据
- source repo 自身也按目标项目结构自承载 bootstrap；相同路径的核心 `.shared` 文件应跳过复制，只刷新根目录适配层与 managed block
- `install-bootstrap.py` 同步核心工作流及 anydoc、research 默认能力规则；其他已安装的可选工具文件不会随着 bootstrap 自动扩散到目标项目
- 外部项目 bootstrap 不加载 renderer，也不刷新 agentwork source checkout；只有 source repo self-host (`-p .`) 才预计算 renderer 输出和 prospective 目标计划，并将 canonical 生成与目标安装放入同一可回滚事务
- project、Case 与 `.gitignore` 的 managed block 只接受“完全不存在”或“唯一且有序”的 marker；残缺、逆序、重复 marker 与非 UTF-8 内容在首个目标写入前停止
- bootstrap 与 optional tool 安装器不新增或改写目标项目许可文件；agentwork 根 `LICENSE` 是 source repo 的许可事实源
- bootstrap 在写入前拒绝与 tool 收据重叠的认领，即使目标缺失、内容相同或 bootstrap 已有收据；不可解析的 tool 收据也阻断。旧 optional research 须先由仍支持它的旧源码正常卸载，再 bootstrap，迁移与用户改动恢复步骤见根 README。
- 退役平台入口只在内容可识别为 agentwork 生成物时自动删除；同路径的项目自定义文件和符号链接必须保留并报告
- 曾由 core bootstrap receipt 管理的退役入口以 receipt 为优先所有权证据：receipt 存在时只有路径哈希匹配才可删除，路径未记录或哈希变化必须持续保留；仅在整个历史 receipt 不存在时使用生成标记兜底
- source repo 根目录适配层产物属于正式版本基线：bootstrap 生成的 `AGENTS.md`、`.claude/`、`.opencode/commands/*`、`.cursor/`、`.codex/skills/*` 与 `.pi/prompts/*` 应与 `.agentwork/bootstrap/*` 保持一致；必要时通过命令自检或安装态人工 smoke 做诊断，可选工具安装态允许额外存在，不视为 bootstrap 漂移
- 已退役的 Codex 默认子代理只按所有权证据清理：已知未改写注册块可移除；文件优先核对旧收据摘要，仍被其他配置引用或已改写的文件保留并报告。新安装不创建 `.codex/config.toml` 或 `.codex/agents`。
- Pi 核心适配精确安装 `/brain`、`/plan`、`/exec`、`/review`、`/case` 与 `/commit` 六个项目 prompt；`/case` 映射共享 Case，Pi 内置 `/session` 和用户目录 JSONL 不作为 agentwork 跨平台状态
- Pi 结构兼容基线为 `v0.84.4`：项目 prompt 需从仓库根 cwd 启动并通过 project trust 才能发现；trust 与 headless `--approve` 都不是 sandbox 或工具级审批
- 核心 bootstrap 不安装 Pi runtime、settings、package、extension、plan-mode、subagent 或 optional tool 运行时依赖；anydoc 与 research 只提供默认 skill 规则，anydoc 的 npm 包由 agent 在项目中按需安装。默认能力一律不安装 MCP server、CLI 或二进制，不创建或修改 `.env`，不修改平台 MCP 私有配置，不向远程服务发送私有资料或凭据。Browser、CodeGraph 可由各自 manifest 显式安装 `.pi/skills/**`，但不创建 `.pi/settings.json`、安装外部 CLI 或假设 MCP 已连接；官方 plan-mode 示例占用 `/plan` 时属于用户安装的外部命令冲突，应回退共享命令或调整其一
- `pi-mcp` 是 Pi-only optional tool：tool installer 只分发项目 skill 与 setup/check 脚本；用户显式运行 setup 后，Pi 才以 project scope 安装固定顶层版本的 MCP extension 并修改目标项目 `.pi/settings.json`。MCP server、凭据和用户配置不由 agentwork 管理；卸载 runtime registration 与卸载 tool files 是两个显式步骤
- optional tool 可通过 `tool.json.env_keys` 声明项目级凭据名；安装器只在 Git ignored 的根 `.env` 中追加缺失的空占位，不覆盖、执行或回显值，卸载时保留用户原有或已填写的 assignment
- `research` 是 provider-neutral 单一研究入口，已随核心 bootstrap 默认分发（不在 registry，`install-tool.py install research` 报 `Unknown tool`）；它可主动选择最窄 provider，也可在本地或直接官方路径已足够时选择不调用远程 provider。默认分发不等于契约 stable：行为 routing contract 只有通过 `.agentwork/evals/research/` 的固定评测 gate 后才可标记为 stable
- Exa 是仅用于公开 Web 发现/批量 fetch 的受限 provisional optional provider；Octocode 仍为跨仓库证据研究的 experimental tool，快速 GitHub 查询继续优先 `gh`；Research 与 provider 的 stable 状态必须由现行评测 gate 支撑
- Exa/Octocode tool pack 仍是 registry-only optional tool，不随 `research` 提升为默认能力；它们只安装项目级 reference/wrapper，不自动修改平台 MCP 私有配置；远程 provider 不接收私有代码、内部资料或凭据

## 关键入口
- `.agentwork/bootstrap/`
- `.pi/prompts/`
- `.opencode/commands/`
- `.agentwork/tools/`
- `.shared/`
- `install-bootstrap.py`
- `install-tool.py`

## 更新记录
- 创建: 2026-04-15
- 最近更新: 2026-09-15
