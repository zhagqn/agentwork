# Case: Pi MCP 可选工具

> 创建: 2026-09-16 00:32
> 简述: 将 Pi MCP 客户端作为独立可选工具接入 agentwork，并完成实现、验证和审查。

## 任务列表（按优先级）
- [x] 新增 pi-mcp 工具包及 Pi 项目 skill
- [x] 增加 setup/check 使用入口与安全边界
- [x] 更新测试并运行回归
- [x] 完成 Case review
- [x] 验证 Pi 扩展实际发现并调用 MCP 工具
- [x] 补齐目标项目安装、检查与双阶段卸载说明
- [x] 运行 source repo 完整门禁并收敛最终审查

## 已确认结论（工作快照）
### 目标
- 仅 Pi 项目显式安装 MCP 能力，其他 agent 和核心 bootstrap 无影响。
### 边界
- In Scope: `.agentwork/tools/pi-mcp/**`、registry、相关测试，以及 README / Project 稳定边界说明。
- Out of Scope: Pi runtime、其他 agent MCP、自动 server、OAuth、真实凭据。
### 约束
- 复用现有 install-tool.py；不修改 staged 区或全局 Pi 配置，不写真实 secret。显式 setup 会修改项目 .pi/settings.json。
### 已选方案
- 工具包分发项目级 skill/setup/check，由 setup 调用 Pi 原生项目安装。
### 关键决策 / 取舍
- MCP 扩展是 Pi 专属 optional tool；MCP server 配置由项目用户显式维护。

## 计划摘要
### 关键文件 / 边界
- `.agentwork/tools/registry.json`、`.agentwork/tools/pi-mcp/**`、`.agentwork/tests/test_pi_optional_tools.py`、`README.md`、`.shared/project/agentwork.md`。
### 执行批次 / 优先级
- 文件分发、安装回归与 Pi 扩展 MCP 工具桥接验证已完成。
### 验证策略
- agentwork-check self-test、安装器和 Pi optional tool 单测。
### 完成标准
- pi-mcp 文件可安装/卸载；runtime setup/remove 使用 project scope，不覆盖 MCP 配置；核心 bootstrap 无变化；真实 STDIO MCP 工具可被 Pi 发现和调用。

## 关联工件
- `.tmp/agentwork/brain/20260916-0021-pi-mcp.md`
- `.tmp/agentwork/plan/20260916-0030-pi-mcp.md`

## 当前批次工作集（可选）
- 范围: `.agentwork/tools/pi-mcp/**` | 主题: Pi MCP optional tool
- 范围: `.agentwork/tools/registry.json` | 主题: 工具注册
- 范围: `.agentwork/tests/test_pi_optional_tools.py` | 主题: 安装与边界回归
- 范围: `README.md` | 主题: Pi optional tool 平台边界
- 范围: `.shared/project/agentwork.md` | 主题: source repo 稳定安装与所有权约定
- 范围: `.shared/case/pi-mcp.md` | 主题: 当前快照与验证边界

## 产出批次（提交锚点）
- 提交: `4a4359a feat(pi-mcp): 添加项目级 MCP 可选工具` | 范围: `.agentwork/tools/pi-mcp/**`, `.agentwork/tools/registry.json`, `.agentwork/tests/test_pi_optional_tools.py`, `README.md`, `.shared/project/agentwork.md` | 验证: 文件安装/卸载、项目包安装、Pi MCP 公开会话桥接调用及 source repo 完整门禁通过
- 提交: `-` | 范围: `.shared/case/pi-mcp.md` | 验证: Case 快照与最终审查事实同步

## 风险 / 阻塞
- 当前无阻塞问题。已验证基线为 Pi 0.85.1、`pi-mcp-extension@1.5.0` 和 STDIO filesystem MCP；HTTP、SSE、OAuth 不在本轮兼容承诺内。
- setup 会联网并修改目标项目 `.pi/settings.json`；`--approve` 仅为该命令信任项目资源，不提供 sandbox。扩展会合并全局 server，项目配置不构成隔离。
- 顶层扩展版本固定，但 fresh install 的传递依赖未完全锁定。tool files 与 runtime registration 分属不同所有权，卸载需要两个显式步骤；用户 MCP 配置始终保留。

## 审查记录
### 2026-09-16 13:18
- 变更：复核全部工作区改动，补齐 `INSTALL.md` 和根 README / Project 稳定边界；修正 manifest 描述，明确文件分发与 runtime 安装、卸载是两个生命周期。
- 验证：脚本语法、JSON、执行权限和 Pi remove 契约通过；install-tool 40 项、Pi optional tool 6 项、tool catalog 8 项通过；source repo 完整门禁 158 项通过（1 项按预期跳过），self-test、bootstrap render 与 Case strict-flow 全部通过；staged 区为空。
- 风险/待办：未发现阻止初步引入项目的破坏性问题；保留 transport 范围、全局 server 继承和传递依赖三个已公开限制。

### 2026-09-16 01:15
- 变更：修正 smoke 中 `tools: []` 造成的空 allowlist；改为正常 Pi 会话并仅经公开 session API 检查、调用扩展工具。
- 验证：`mcp_filesystem_read_text_file` 同时出现在 `getAllTools()` 与 `getActiveToolNames()`，经 `getToolDefinition()` 调用返回 `pi-extension-bridge-ok`，session shutdown 完成。
- 风险/待办：顶层扩展版本固定但传递依赖未完全锁定；未验证 OAuth/HTTP server，不影响本轮 STDIO 接入结论。

### 历史审查摘要（2026-09-16 00:50-01:00）
- 安装定位与检查语义完成收敛，文件安装/卸载、项目 package 安装和测试均通过；当时未完成的桥接验证已由 01:15 公开 session API smoke 闭环。
