# Project Management

## 目标
让 `.shared/project/` 只承载长期稳定事实，而不被当次任务污染。

## 什么时候写入 Project
适合写入：
- 兼容性/运行时红线
- 长期稳定的 API / contract 约束
- 生成物策略
- 关键目录入口与 owner 边界
- 会被反复使用的命令/流程约定

不适合写入：
- 当次任务的中间推演
- 方案对比
- 临时 workaround
- 只对本轮有效的实施细节

## 与 Session 的边界
- **Session**：当前任务快照
- **Project**：长期稳定事实

简单判断：
> 下次做类似任务时，你是否希望助手“自动先读到它”？
> 如果是，倾向写入 Project；否则留在 Session。

## 推荐流程
1. 任务进行中：只写 Session
2. 任务收敛后：`/review`（或 `/session review`）
3. 识别稳定结论
4. 用户确认后，再写入 `.shared/project/*`

## 文件组织建议
- `project/index.md` 维护索引
- 每个项目或稳定子域单独一页
- 单页尽量可扫读（建议 < 200 行）

## 轻量 project 约定
目标：让助手启动时不必预读全部 project 文档，但一旦命中某个项目或目录，就能补读对应约束。

推荐做法：
1. 根入口只要求读取 `project/index.md`
2. 每个项目或稳定子域只维护一个轻量 `*.md`
3. 在 `project/index.md` 里维护“目录/主题 → 文档”的简单映射
4. 当任务明显涉及某个项目或目录时，再读取对应的 `*.md`

推荐结构：

```text
.shared/project/
├── index.md
├── app-web.md
├── api.md
└── tooling.md
```

约定：
- `index.md` 只做入口和映射，不堆大段细节
- 每个 project 文档只保留少量但重要的稳定事实
- 一个文档优先覆盖一个项目/子域，不再额外引入路由清单或目录级 `AGENTS.md`

## 读取触发规则
- 启动阶段只默认读取 `.shared/project/index.md`
- 当第一次确定将读取或修改的目标路径后，必须立即对照 `index.md` 中的读取映射
- 若命中某个映射条目，先读取对应的 `project/*.md`，再继续设计、修改或审查
- 若工作过程中目标路径扩大，必须重新对照一次 `index.md`
- 若没有命中任何条目，继续工作即可；不需要为了“可能相关”而预读全部 project 文档

## 固定收敛规则
新增或更新 `.shared/project/*.md` 时，优先按以下规则收敛，避免不同 agent 写出漂移格式：

1. **文档格式**
   - 优先遵循 `.shared/templates/project.md`
   - 一级标题顺序优先保持为：`适用范围` → `TL;DR` → `长期约束与约定` → `关键入口` → `更新记录`
   - 若某个三级小节确实无内容，可删该小节；不要新增大量临时章节

2. **索引回填**
   - 新增或更新 `.shared/project/*.md` 时，同一轮改动内同步更新 `.shared/project/index.md`
   - `index.md` 只维护“命中什么场景 → 应读哪个文档”的入口映射，不重复正文细节

3. **索引映射格式**
   - `index.md` 中每个映射条目优先使用固定三元组：`命中` / `读取` / `用途`
   - 推荐写法：

```md
- 命中：`.agentwork/`、`install-bootstrap.py`
- 读取：`.shared/project/agentwork.md`
- 用途：bootstrap / install / 自承载规则
```

4. **内容范围**
   - 只写少量但重要的长期稳定事实
   - 不写当次任务过程、方案对比、临时 workaround、最近一次执行日志
   - 若结论还未稳定，先留在 session，等 `/review` 后再提升到 project
