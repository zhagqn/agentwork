# 电商业务架构站

本目录使用 `/arch` 维护一套区域仓配电商系统的架构文档，按“主线 / 场景”拆分长期结构与值班视图。

## 文档范围

- `主线`：系统总览、订单主链路、支付异常、履约分拨、售后逆向、数据通路和部署分层
- `场景`：围绕大促值班、故障处置或专项治理的聚焦视图

## 当前条目

- `主线 / 电商总览`
- `主线 / 订单旅程`
- `主线 / 跨域订单长链路`
- `主线 / 支付异常回路`
- `主线 / 履约分拨编排`
- `主线 / 售后逆向闭环`
- `主线 / 数据织网`
- `主线 / 部署分层`
- `场景 / 双 11 值班视图`

## 生成方式

```bash
python3 .shared/scripts/arch-export-mermaid.py docs/architecture
python3 .shared/scripts/arch-render.py docs/architecture --check
python3 .shared/scripts/arch-render.py docs/architecture
```
