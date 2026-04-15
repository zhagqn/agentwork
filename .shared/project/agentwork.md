# Project: agentwork

## 仓库定位
- 本仓库是 `agentwork` 的源仓库，不是直接业务项目模板
- 核心职责：维护可复用工作流、基础迁移文件、可选工具源、上游参考镜像

## 目录职责
- `.shared/`：项目可同步的核心工作流契约
- `.agentwork/bootstrap/`：迁移到其他 AI 助手的基础文件源
- `.agentwork/tools/`：可选工具源（figma/browser/android/godot/...）
- `.agentwork/upstreams/`：外部工作流/方法论基座映射
- `.tmp/`：上游镜像与 standalone 临时工件

## 入口脚本
- `install-bootstrap.py`：安装核心工作流和基础 AI 适配文件
- `install-tool.py`：安装可选工具
- `python3 install-bootstrap.py -p .`：在 source repo 根目录原地刷新已安装的核心工作流层
- 外部上游的更新命令直接写在 `.agentwork/upstreams/*.md` 中

## 长期约束
- 不默认依赖任何特定 runtime
- 可选工具不直接长期驻留在 `.shared`
- `.tmp/*` 默认不纳入提交，除非明确保留证据
- source repo 自身也按目标项目结构自承载 bootstrap；相同路径的核心 `.shared` 文件应跳过复制，只刷新根目录适配层与 managed block
