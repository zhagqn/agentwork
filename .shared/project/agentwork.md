# Project: agentwork

## 适用范围
- 涉及 `agentwork` source repo 自身维护时使用
- 常见命中目录/入口：`.agentwork/`、`install-bootstrap.py`、`install-tool.py`、`test/`

## TL;DR
- 本仓库是 `agentwork` 的 source repo，不是直接业务项目模板
- 核心职责：维护可复用工作流、基础迁移文件、可选工具源、上游参考镜像
- source repo 自身也按目标项目结构自承载 bootstrap
- `install-bootstrap.py` 只同步核心工作流，不会把已安装的可选工具自动扩散到目标项目

## 长期约束与约定

### Build / Test
- 原地刷新核心工作流：`python3 install-bootstrap.py -p .`
- 集成诊断入口（人工触发）：`python3 test/run.py`
- 若修改 bootstrap 生成契约，优先同步 `.agentwork/bootstrap/*` 与 integrated harness

### 代码与目录约定
- `.shared/`：项目可同步的核心工作流契约
- `.agentwork/bootstrap/`：迁移到其他 AI 助手的基础文件源
- `.agentwork/tools/`：可选工具源（figma/browser/android/godot/...）
- `.agentwork/upstreams/`：外部工作流/方法论基座映射
- `.tmp/`：上游镜像与 standalone 临时工件
- 外部上游的更新命令直接写在 `.agentwork/upstreams/*.md` 中

### 兼容性 / 运行时红线
- 不默认依赖任何特定 runtime
- 可选工具不直接长期驻留在 `.shared`
- `.tmp/*` 默认不纳入提交，除非明确保留证据
- source repo 自身也按目标项目结构自承载 bootstrap；相同路径的核心 `.shared` 文件应跳过复制，只刷新根目录适配层与 managed block
- `install-bootstrap.py` 只同步核心工作流；已安装的可选工具文件不会随着 bootstrap 自动扩散到目标项目
- source repo 根目录适配层产物属于正式版本基线：`AGENTS.md`、`.claude/`、`.agent/`、`.cursor/`、`.github/`、`.codex/skills/*` 应与 `.agentwork/bootstrap/*` 保持一致，并通过 integrated harness 回归

## 关键入口
- `.agentwork/bootstrap/`
- `.agentwork/tools/`
- `install-bootstrap.py`
- `install-tool.py`
- `test/`

## 更新记录
- 创建: 2026-04-15
- 最近更新: 2026-05-04
