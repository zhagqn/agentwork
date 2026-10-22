---
name: research
description: "Evidence-led research for current systems, projects, libraries, tools, and cross-source comparisons. Use when a task needs up-to-date public research, official or implementation evidence, community signal analysis, version and change tracing, or an auditable conclusion across multiple sources."
---

# research

项目级研究技能入口，完整流程以共享定义为准。

## 路径与执行

- 根据 dsh 加载本技能时提供的资源目录（`.dsh/skills/research/`），向上三级定位本入口所在项目根；不要用当前 shell 工作目录代替。
- 读取项目根的 `AGENTS.md` 并完成其中的启动必读。共享规则中的项目相对路径均从该根解析；shell 操作以该根为工作目录，保留路径中的空格。
- 确认主定义 `.shared/skills/research/SKILL.md` 存在并完整读取；缺失时停止并报告。
- 保留当前用户消息的原始参数、子命令、引号和带空格路径，交给共享定义解释。加载技能或描述 slash 命令不构成额外执行或提交许可。
- 需要用户补充时使用当前会话实际可用的交互能力；缺少专用交互工具时，按共享定义回退为文本提问。
- 使用标准模式，保持 dsh 原生计划模式关闭；当前模式禁止写入时停止并报告，不自行调整用户配置。
- 不把搜索摘要当作证据；打开并核对原始来源后再引用。不向远程服务发送私有资料、凭据或环境变量值。
