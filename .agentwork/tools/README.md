# Tools

可选工具能力统一放在 `.agentwork/tools/<tool>/`。

每个工具目录负责维护：
- 原始 source 文件
- `tool.json`（安装清单）
- `INSTALL.md`（安装流程）

## 当前工具
- `figma`
- `browser`
- `android`
- `godot`

## 安装入口
```bash
python3 install-tool.py list
python3 install-tool.py -l
python3 install-tool.py install figma -p <path>
python3 install-tool.py -i browser -p <path>
python3 install-tool.py install android godot -p <path>
python3 install-tool.py -i browser,figma -p <path>
python3 install-tool.py uninstall figma -p <path>
python3 install-tool.py -u browser,figma -p <path>
```

> 默认会安装该工具当前已支持的全部助手适配层。
> 支持一次安装多个工具：可用空格或逗号分隔，例如 `python3 install-tool.py install browser figma -p <path>`。
> 动作长命令使用裸词：`install`、`uninstall`、`list`；简写使用 `-i`、`-u`、`-l`。
> `install-bootstrap.py` 只同步核心工作流，不会自动把已安装的可选工具扩散到目标项目。
