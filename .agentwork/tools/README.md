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
python3 install-tool.py --list
python3 install-tool.py figma -p <path>
python3 install-tool.py browser -p <path>
python3 install-tool.py android godot -p <path>
python3 install-tool.py browser figma -p <path>
```

> 默认会安装该工具当前已支持的全部助手适配层。
> 支持一次安装多个工具：可用空格或逗号分隔，例如 `python3 install-tool.py browser figma -p <path>`。
