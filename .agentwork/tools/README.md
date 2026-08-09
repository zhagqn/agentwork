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

## 环境变量契约

工具可在 `tool.json` 中声明可选的 `env_keys`。每项只允许以下字段：

- `name`：合法的环境变量名，且在 registry 内只能由一个工具管理
- `required`：是否在该 tool pack 的全部受支持使用路径中都必需；`false` 可表示存在 keyless、OAuth 或其他不依赖该 key 的替代路径
- `description`：不含密钥值的用途说明

该字段只描述配置契约，安装器不会因 `required` 值而读取或验证真实凭据。安装器只管理项目根 `.env` 中缺失 key 的空占位，不读取执行 shell 语法，也不覆盖或回显已有值。若 `.env` 已被 Git 跟踪则拒绝安装；未被忽略时向项目根 `.gitignore` 追加 `.env`。

卸载时，仍为空的受管占位会被移除；用户已填写的值和用户原有 key 均会保留。安装器不会删除 `.env` 或回收 `.gitignore` 规则。

安装和卸载会先完成 manifest、目标路径与凭据文件 preflight，再快照本次受影响路径；普通运行时写入异常或 `Ctrl-C` 中断会恢复 tool entries、`.env` 和 `.gitignore`。进程被强制终止、系统掉电或底层文件系统故障不承诺跨路径原子性，出现此类情况后应重新执行同一安装或卸载命令恢复 manifest 完整状态。
