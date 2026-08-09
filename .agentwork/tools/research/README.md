# Research Tool Pack

## 类型

- skill
- provider-neutral research workflow
- provisional：结构回归通过，等待现行内容与路由 gate 验证

## 内容

- 共享研究契约
- Codex / Claude / Cursor 薄入口
- source-only 评测契约和用例（不安装到目标项目）

OpenCode 通过 `.claude/skills` 兼容发现，不维护独立正文副本。

## 单一入口

`research` 是面向用户和 agent 的唯一研究入口。Octocode、Exa 等 provider 保持独立 optional tool pack，只提供连接、凭据和受限工具面，不各自增加 skill 或命令。

- 用户不需要显式说“使用 Exa/Octocode”；research 根据任务证据类型主动选择一个最窄 provider
- 一次问题默认只升级到一个远程 provider；失败时记录原因后再选择明确 fallback，不并行调用所有 provider
- 安装 research 不自动安装 provider；目标项目按隐私、成本和任务类型单独选择 MCP
- provider 的凭据、运行时、平台 MCP 配置和卸载生命周期保持独立，避免单体 research 包扩大默认工具面
- 主动路由允许选择“不调用远程 provider”；本地资料、package metadata 或直接官方来源足够时不升级远程 provider

## 适用场景

- 调研当前系统、项目、库、工具或社区变化
- 对照官方资料、实现证据和社区反馈
- 追踪 version、release、commit、issue 或 pull request
- 在不绑定搜索 provider 的前提下形成可审查结论

## 边界

- 不安装 MCP server、CLI 或二进制
- 不创建或修改 `.env`
- 不修改平台 MCP 私有配置
- 不向远程服务发送私有资料或凭据
