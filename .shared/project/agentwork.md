# Project: agentwork

## 适用范围
- 涉及 `agentwork` source repo 自身维护时使用
- 常见命中目录/入口：`.shared/`、`.agentwork/`、`install-bootstrap.py`、`install-tool.py`

## TL;DR
- 本仓库是 `agentwork` 的 source repo，不是直接业务项目模板
- 核心职责：维护可复用工作流、基础迁移文件和可选工具源
- source repo 自身也按目标项目结构自承载 bootstrap
- `install-bootstrap.py` 只同步核心工作流，不会把已安装的可选工具自动扩散到目标项目

## 长期约束与约定

### Build / Test
- 原地刷新核心工作流：`python3 install-bootstrap.py -p .`
- 命令内建 harness 自检：`python3 .shared/scripts/agentwork-check.py self-test`
- 真实 provider E2E 只作为人工 smoke / 兼容性调查，不作为默认回归或合并 gate
- 核心 workflow 检查优先沉淀到 `.shared/scripts/`；历史集成诊断只保留专题语境
- 若修改 bootstrap 生成契约，优先同步 `.agentwork/bootstrap/*` 与命令内建 harness

### 代码与目录约定
- `.shared/`：项目可同步的核心工作流契约
- `.agentwork/bootstrap/`：迁移到其他 AI 助手的基础文件源
- `.opencode/commands/`：OpenCode 核心工作流薄 wrapper，由 bootstrap 生成并在 source repo 自承载
- `.agentwork/bootstrap/pi/prompts/`：Pi 项目 prompt 的 canonical 生成产物
- `.pi/prompts/`：Pi 核心工作流薄 wrapper，由 bootstrap 生成并在 source repo 自承载
- `.pi/skills/`：source repo 中显式安装的 optional tool Pi 入口；不属于核心 bootstrap
- `.codex/agents/`：Codex 项目级执行子代理，由 bootstrap 生成、显式注册并在 source repo 自承载
- `.agentwork/tools/`：可选工具源（figma/browser/android/godot/...）
- `.tmp/`：核心 workflow 和可选工具的临时工件；核心 workflow 默认使用 `.tmp/agentwork/*`

### 兼容性 / 运行时红线
- 不默认依赖任何特定 runtime
- 可选工具不直接长期驻留在 `.shared`
- `.tmp/*` 默认不纳入提交，除非明确保留证据
- source repo 自身也按目标项目结构自承载 bootstrap；相同路径的核心 `.shared` 文件应跳过复制，只刷新根目录适配层与 managed block
- `install-bootstrap.py` 只同步核心工作流；已安装的可选工具文件不会随着 bootstrap 自动扩散到目标项目
- 外部项目 bootstrap 不加载 renderer，也不刷新 agentwork source checkout；只有 source repo self-host (`-p .`) 才预计算 renderer 输出和 prospective 目标计划，并将 canonical 生成与目标安装放入同一可回滚事务
- project/session/`.gitignore` managed block 只接受“完全不存在”或“唯一且有序”的 marker；残缺、逆序、重复 marker 与非 UTF-8 内容在首个目标写入前停止
- bootstrap 与 optional tool 安装器不新增或改写目标项目许可文件；agentwork 根 `LICENSE` 是 source repo 的许可事实源
- 退役平台入口只在内容可识别为 agentwork 生成物时自动删除；同路径的项目自定义文件和符号链接必须保留并报告
- source repo 根目录适配层产物属于正式版本基线：bootstrap 生成的 `AGENTS.md`、`.claude/`、`.opencode/commands/*`、`.cursor/`、`.codex/skills/*`、`.codex/agents/*`、`.codex/config.toml` 受管块与 `.pi/prompts/*` 应与 `.agentwork/bootstrap/*` 保持一致；必要时通过命令自检或安装态人工 smoke 做诊断，可选工具安装态允许额外存在，不视为 bootstrap 漂移
- bootstrap 默认安装并注册 `luna_worker` Codex 执行子代理；安装器只维护 agentwork 受管配置块和受管 agent 文件，遇到同名项目自定义定义时停止，不静默覆盖
- Pi 核心适配精确安装 `/brain`、`/plan`、`/exec`、`/review`、`/commit` 与 `/aw-session` 六个项目 prompt；只有 `/aw-session` 映射共享 `/session`，Pi 内置 `/session` 和用户目录 JSONL 不作为 agentwork 跨平台状态
- Pi 结构兼容基线为 `v0.84.4`：项目 prompt 需从仓库根 cwd 启动并通过 project trust 才能发现；trust 与 headless `--approve` 都不是 sandbox 或工具级审批
- 核心 bootstrap 不安装 Pi runtime、settings、package、extension、plan-mode、subagent 或 optional tool；Browser、Research、CodeGraph 可由各自 manifest 显式安装 `.pi/skills/**`，但不创建 `.pi/settings.json`、安装外部 CLI 或假设 MCP 已连接；官方 plan-mode 示例占用 `/plan` 时属于用户安装的外部命令冲突，应回退共享命令或调整其一
- optional tool 可通过 `tool.json.env_keys` 声明项目级凭据名；安装器只在 Git ignored 的根 `.env` 中追加缺失的空占位，不覆盖、执行或回显值，卸载时保留用户原有或已填写的 assignment
- `research` 是 provider-neutral 单一研究入口；它可主动选择最窄 provider，也可在本地或直接官方路径已足够时选择不调用远程 provider；行为 routing contract 只有通过固定评测 gate 后才可标记为 stable
- Exa 是仅用于公开 Web 发现/批量 fetch 的受限 provisional optional provider；Octocode 仍为跨仓库证据研究的 experimental tool，快速 GitHub 查询继续优先 `gh`；Research 与 provider 的 stable 状态必须由现行评测 gate 支撑
- Exa/Octocode tool pack 只安装项目级 reference/wrapper，不自动修改平台 MCP 私有配置，也不随 `research` 自动全量安装；远程 provider 不接收私有代码、内部资料或凭据

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
- 最近更新: 2026-09-02
