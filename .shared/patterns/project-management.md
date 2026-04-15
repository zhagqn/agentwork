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
- 每个子域单独一页
- 单页尽量可扫读（建议 < 200 行）
