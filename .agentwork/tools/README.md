# Tools

可选工具能力统一放在 `.agentwork/tools/<tool>/`。

每个工具目录负责维护：
- 原始 source 文件
- `tool.json`（安装清单）
- `INSTALL.md`（安装流程）

## 工具清单

`.agentwork/tools/registry.json` 是可选工具清单的唯一事实源。查看可安装工具时使用安装入口读取 registry，不在说明文档中维护重复列表。

## 安装入口
```bash
python3 install-tool.py list
python3 install-tool.py -l
python3 install-tool.py install <tool-name> -p <path>
python3 install-tool.py -i <tool-name> -p <path>
python3 install-tool.py install <tool-a> <tool-b> -p <path>
python3 install-tool.py -i <tool-a>,<tool-b> -p <path>
python3 install-tool.py uninstall <tool-name> -p <path>
python3 install-tool.py -u <tool-a>,<tool-b> -p <path>
```

> 默认安装该工具在 `tool.json` 中声明的全部助手适配层。
> 支持一次安装多个工具：可用空格或逗号分隔，例如 `python3 install-tool.py install <tool-a> <tool-b> -p <path>`。
> 动作长命令使用裸词：`install`、`uninstall`、`list`；简写使用 `-i`、`-u`、`-l`。
> `install-bootstrap.py` 只同步核心工作流，不会自动把已安装的可选工具扩散到目标项目。
