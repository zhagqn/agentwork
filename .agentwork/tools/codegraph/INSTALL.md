# Install CodeGraph Tool

## What gets installed
- `.shared/mcp/codegraph.md`：共享优先导航约定和官方接入参考。
- `.agents/skills/codegraph/SKILL.md`：Codex / OpenCode / Pi 共用的项目技能，描述明确覆盖理解、定位与修改代码前的优先查询。Pi 原生从 `.agents/skills/` 发现项目技能，不再单独安装 `.pi/skills/codegraph/`。
- `.claude/rules/codegraph.md`：Claude Code 项目规则。
- `.cursor/rules/codegraph.mdc`：Cursor alwaysApply 项目规则。

所有入口只由本工具显式安装和卸载，不写入核心 bootstrap、根 AGENTS.md 或用户级全局约束。不安装 CLI、不建索引、不修改任何平台 MCP、权限或自动许可配置。

## Install
```bash
python3 install-tool.py install codegraph -p <path>
python3 install-tool.py -i codegraph -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall codegraph -p <path>
python3 install-tool.py -u codegraph -p <path>
```

## After install
- 安装新入口后，在目标项目重新加载技能或开启新会话；平台需要项目信任时按平台提示处理。已有安装可重复运行同一 install 命令升级，未被用户改写的旧文件按收据更新；冲突时停止并保留用户内容。
- 旧版安装的 `.pi/skills/codegraph/SKILL.md` 会在重新 install 时退役：与收据摘要一致则删除；被改写则保留为项目文件、移出收据并输出 `keep-modified`。保留的改写版与共享技能同名，Pi 会报名称冲突且只加载其一，需人工合并到 `.agents/skills/codegraph/` 后删除。
- 没有 tool 收据的历史文件不会被自动接管；需先人工核对来源并迁移，不能仅凭当前 manifest 覆盖。source repo 中已追踪且与旧模板一致的自承载文件可按 Git 基线同步，不伪造安装收据。
- 已有 `.codegraph/` 且 CLI 或 MCP 可用时，理解、定位和准备修改代码应优先调用 CodeGraph；索引或工具缺失则回退。技能匹配依赖模型与平台，规则是优先调用指令而非机械强制，需从实际调用记录确认使用。
- CLI、项目索引和 MCP 是独立能力；按 `.shared/mcp/codegraph.md` 完成所需设置。仅使用 CLI 无需接线 MCP，工具安装也不创建 `.pi/settings.json`。
- 索引过期或监听停止时读取受影响文件，必要时运行 `codegraph sync`；安装入口不会替用户刷新索引。
- 遥测默认开启，可 `codegraph telemetry off` 关闭
- 收益边界：上游基准不代表本项目结果；按任务质量、耗时和成本评估，小任务可能直接读取更轻量
- 常驻文件监听进程有持续资源开销，不用的项目及时 `codegraph uninit`
- `.codegraph/` 默认不纳入提交
- 上游为高速迭代项目；命令若失效，以官方仓库 README 为准

## Uninstall behavior
- 卸载会按 tool 收据移除未被用户改写的上述入口，保留相邻的项目自定义规则、技能和配置。
- 用户改写的受管文件会触发所有权冲突，不被覆盖或静默删除。CLI、MCP 配置及 `.codegraph/` 不在本工具的卸载范围内。
