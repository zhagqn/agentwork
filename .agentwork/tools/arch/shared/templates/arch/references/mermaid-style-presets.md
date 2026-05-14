# Mermaid Style Presets

本文件记录 `/arch` 默认使用的 Mermaid 基础样式，以及在不同业务语义下可复用的参考样式。

## 默认基础样式：`editorial-base`

适用场景：

- 主线架构图
- 交易链路图
- 数据流、履约流、部署分层等常规业务文档

核心约定：

- 节点分三类：`warm`、`teal`、`neutral`
- 分组底色低饱和，节点边框与文字优先保证阅读稳定
- 主链路使用棕色实线；补偿、异常和回补链路使用同色虚线

推荐片段：

```mermaid
classDef warm fill:#fff7ec,stroke:#aa6232,color:#1f2c2d,stroke-width:1.5px;
classDef teal fill:#ecf7f5,stroke:#0f766e,color:#1f2c2d,stroke-width:1.5px;
classDef neutral fill:#fffdfa,stroke:#8ea0a2,color:#1f2c2d,stroke-width:1.5px;

style domainA fill:#fbf1e4,stroke:#ddcdb8,color:#6f5d4a;
style domainB fill:#eef7f4,stroke:#ddcdb8,color:#4f6662;
style domainC fill:#f7f3eb,stroke:#ddcdb8,color:#6f5d4a;

linkStyle default stroke:#8e6746,stroke-width:1.6px;
linkStyle 7,8 stroke:#8e6746,stroke-width:1.4px,stroke-dasharray:6 4;
```

使用建议：

- `warm` 适合入口、结果、用户侧触点
- `teal` 适合控制、决策、处理中枢
- `neutral` 适合人工介入、桥接节点、二级支撑对象
- 若只有两类角色，可只用 `warm + teal`

## 参考样式：`control-plane`

适用场景：

- 平台控制面
- 发布、策略、治理、运行时编排

推荐配色：

- 节点：`fill:#eef4ff`、`stroke:#4568a8`
- 次级节点：`fill:#f6f8fc`、`stroke:#7c8aa5`
- 分组：`fill:#f3f6fb`、`stroke:#cfd8e6`
- 连线：`stroke:#516b8f`

风格特征：

- 冷色、更克制，适合控制面和治理面
- 视觉重心更偏“平台”而不是“业务触点”

## 参考样式：`ops-alert`

适用场景：

- 大促值班
- 故障定位
- 告警、降级、止损、回滚链路

推荐配色：

- 常规节点：`fill:#fff7ec`、`stroke:#b7791f`
- 告警节点：`fill:#fff1f2`、`stroke:#c53030`
- 观察节点：`fill:#ecfdf5`、`stroke:#2f855a`
- 连线：`stroke:#9c4221`

风格特征：

- 红色只用于异常、阻断、回滚等关键点，不要铺满整张图
- 正常链路仍建议保留暖色或绿色，避免整个页面进入“全告警”状态

## 参考样式：`mono-print`

适用场景：

- 需要打印
- 需要嵌入偏正式、偏黑白的设计稿
- 不适合使用明显色彩编码的审阅场景

推荐配色：

- 主节点：`fill:#f8f8f8`、`stroke:#444`
- 次节点：`fill:#ffffff`、`stroke:#777`
- 分组：`fill:#f2f2f2`、`stroke:#c8c8c8`
- 连线：`stroke:#555`

风格特征：

- 强依赖布局和分组，不依赖颜色建立语义
- 适合导出 PDF 或进入偏文档化环境

## 选择规则

- 未特别说明时，默认使用 `editorial-base`
- 用户明确要求“控制面 / 发布治理 / 平台感更强”时，优先考虑 `control-plane`
- 用户明确要求“值班 / 告警 / 风险 / 回滚”时，优先考虑 `ops-alert`
- 用户明确要求“打印 / 黑白 / 极简”时，优先考虑 `mono-print`
- 同一站点的主线版本应尽量统一一种基础风格；场景页可在同一语义下做有限变体
