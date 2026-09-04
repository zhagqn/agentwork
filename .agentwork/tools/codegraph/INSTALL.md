# Install CodeGraph Tool

## What gets installed
- `.shared/mcp/codegraph.md`（引用型参考文档，不含上游源码或二进制）
- `.pi/skills/codegraph/SKILL.md`（只使用已存在 CLI/索引的 Pi 项目入口，不假设 MCP 已连接）

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
- 本 tool pack 只物化参考文档；codegraph 本体按 `.shared/mcp/codegraph.md` 的三步流程接入：装 CLI → `codegraph install` 接线 agent → 每项目 `codegraph init` 建索引
- Pi skill 不创建 `.pi/settings.json`；CLI 或 `.codegraph/` 缺失时回退本地读取/搜索能力
- 遥测默认开启，可 `codegraph telemetry off` 关闭
- 收益边界：大/复杂仓库高频场景收益确定；小仓库/小任务可能不降反升，按需评估
- 常驻文件监听进程有持续资源开销，不用的项目及时 `codegraph uninit`
- `.codegraph/` 默认不纳入提交
- 上游为高速迭代项目；命令若失效，以官方仓库 README 为准
