# 语言与编码风格约束

## 语言使用规范

| 场景                      | 语言要求     |
| ------------------------- | ------------ |
| 代码注释                  | **简体中文** |
| 思考/推理过程             | **简体中文** |
| 解释、讨论、分析、总结    | **简体中文** |
| 代码、标识符              | **English**  |
| 提交信息 (commit message) | **简体中文** |
| Markdown 正文说明         | **简体中文** |

## 命名规范

### 文件命名

统一使用 **kebab-case**（短横线连接，全小写）：

```
✅ 正确
focus-manager.ts
user-profile.vue
api-service.ts
use-focus-zone.ts

❌ 错误
FocusManager.ts      # PascalCase
focus_manager.ts     # snake_case
focusManager.ts      # camelCase
```

### TypeScript / JavaScript

| 类型           | 命名风格         | 示例                          |
| -------------- | ---------------- | ----------------------------- |
| 变量、函数     | camelCase        | `focusManager`, `handleClick` |
| 常量           | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`             |
| 类、类型、接口 | PascalCase       | `FocusZone`, `UserProfile`    |
| 枚举           | PascalCase       | `KeyCode.Enter`               |

### Vue 组件

| 类型       | 命名风格   | 示例                            |
| ---------- | ---------- | ------------------------------- |
| 组件文件名 | kebab-case | `focus-button.vue`              |
| 组件注册名 | PascalCase | `FocusButton`                   |
| Props      | camelCase  | `isDisabled`, `tabIndex`        |
| Events     | kebab-case | `@focus-change`, `@item-select` |

## 格式化

- 默认已通过 ESLint + Prettier 格式化
- 提交前运行 `pnpm lint` 和 `pnpm format`

---

## 代码注释规范

### 核心原则

1. **语言**：全中文注释
2. **内容**：解释「Why」（业务背景/决策原因）优于「What」（代码翻译）
3. **整洁**：禁止装饰线；禁止保留注释掉的废弃代码

### 基本规则

#### 1. 使用中文

所有注释使用中文编写，保持与项目文档一致。

```typescript
// ✅ 正确
// 初始化焦点管理器，设置默认焦点区域

// ❌ 错误
// Initialize focus manager and set default focus zone
```

#### 2. 禁止无意义分隔符

不使用任何形式的装饰性分隔符。

```typescript
// ❌ 禁止
// ==========================================

// ✅ 正确
// 焦点管理模块
```

#### 3. 解释「为什么」而非「做什么」

代码展示「怎么做 (How)」，注释解释「为什么这么做 (Why)」。

```typescript
// ❌ 仅描述 What
// 设置超时时间为 500ms

// ✅ 解释 Why
// 旧款 Android TV 响应较慢，需延长超时以防断连
setTimeout(fn, 500);
```

#### 4. 同步更新注释

修改代码后，判断相关注释是否需要同步更新或删除。

#### 5. 禁止注释掉的代码

严禁提交注释掉的代码片段。版本控制（Git）用于查历史，代码库只保留生效的代码。

```typescript
// ❌ 禁止 - 废弃代码
// const oldLogic = items.filter(x => x.active);
const newLogic = items.filter((x) => x.enabled);

// ✅ 正确 - 直接删除旧代码
const newLogic = items.filter((x) => x.enabled);
```

#### 6. 格式规范

双斜杠 `//` 后必须跟一个空格，注释放在代码**上方**。

```typescript
// ✅ 正确
// 使用 Set 提升查找性能
const whiteList = new Set(config.ids);

//❌ 错误 - 缺少空格
//使用 Set 提升查找性能

// ❌ 错误 - 行尾注释（除非极短）
const whiteList = new Set(config.ids); // 转换成 Set
```

#### 7. 标记规范

禁止业务型 TODO，允许技术型标记（仅限 FIXME/HACK）。

```typescript
// ❌ 禁止 - 业务规划
// TODO: 下个版本需要支持多语言

// ✅ 允许 - 技术标记
// FIXME: 临时方案，Android 4.4 不支持 Promise.finally
```

### TypeScript 注释原则

#### 避免冗余注释

类型定义清晰时，不需要重复说明。禁止解释显而易见的逻辑。

```typescript
// ❌ 冗余
i++; // i 自增

// ❌ 冗余 - 类型已说明
/** @param a 第一个数字 */
function add(a: number, b: number): number;

// ✅ 无需注释
function add(a: number, b: number): number;
```

#### 需要 JSDoc 的场景

仅在以下情况使用完整 JSDoc：

1. **对外暴露的 API**：库或模块的公共接口
2. **参数含义模糊**：名称无法完全表达意图
3. **会抛出异常**：必须标注 `@throws`

```typescript
/**
 * 连接物理设备并初始化通信
 * @throws {DeviceNotFoundError} 无法连接到物理设备时抛出
 */
async function connectDevice(deviceId: string): Promise<Device>;
```

---

## 测试规范

对非平凡逻辑（复杂条件、状态机、异步流程、错误恢复等）的改动：

1. 优先考虑添加或更新测试
2. 说明推荐的测试用例、覆盖点
3. 说明如何运行这些测试
4. **不要声称已实际运行过测试**，只能说明预期结果和推理依据

---

## Shell 文本编辑稳定策略

用于降低命令行文本修改（尤其是 Markdown/脚本）时的转义与引用错误。

1. 优先使用结构化编辑：`apply_patch` 或 HereDoc（`cat <<'EOF'`）；避免复杂 `sed -i 's/.../.../'` 单行替换。
2. 涉及反引号、`$`、`/`、`&`、`<...>` 的文本，不放入可被 shell 解释的双引号命令串。
3. `grep` 模式一律使用 `--` 分隔参数与模式：`grep ... -- 'pattern'`。
4. 多层命令（`bash -c` + `awk/sed/perl`）前先降层：能拆成临时文件就拆，不在一条命令里嵌套三层引号。
5. 每次批量替换后必须先看 `git diff`，再执行验证命令。

---

## 速查清单

| 类别     | ✅ 正确                       | ❌ 错误                               |
| -------- | ----------------------------- | ------------------------------------- |
| 文件名   | `focus-manager.ts`            | `FocusManager.ts`, `focus_manager.ts` |
| 注释语言 | 全中文                        | 英文注释                              |
| 注释内容 | 解释「Why」                   | 翻译代码「What」                      |
| 注释格式 | `// ` 后加空格                | `//` 无空格                           |
| 注释位置 | 代码上方                      | 行尾（除非极短）                      |
| 装饰符   | 无                            | `===` `---` `***`                     |
| 废弃代码 | 直接删除                      | 注释保留                              |
| TODO     | 禁止业务规划                  | 允许 FIXME/HACK                       |
| JSDoc    | 公共 API / 复杂逻辑 / @throws | 简单类型函数                          |
| 冗余注释 | 避免                          | `i++ // i 自增`                       |
