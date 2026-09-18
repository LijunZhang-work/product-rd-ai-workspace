# 确定性 Acceptance Golden 与 Test Oracle 规范

## 1. 文档目的

本项目存在大量连续人机交互。

开发模型容易出现：

```text
自己理解需求
↓
按自己的理解实现
↓
按自己的理解写 Playwright
↓
全部 PASS
↓
实际交互行为仍不符合产品定义
```

本文件用于防止“实现与测试共享同一个错误理解”。

当前阶段不引入人工确认流程。

---

## 2. Test Oracle

Test Oracle 指：

> **什么结果才算真正正确。**

Oracle 必须来自以下确定性来源之一：

```text
1. 已明确写入项目文档的交互行为契约
2. NativeSceneBundle / HitMap / 数据契约
3. 原始 JAR / Headless Native Scene 的可重复事实
4. 固定 Golden Fixture 的期望输出
5. 明确的状态机定义
6. 明确的数学/几何规则
```

禁止根据“当前实现已经是什么样”反向定义 Oracle。

---

## 3. Acceptance Golden

核心交互必须建立自动化 Golden Case。

每个 Golden Case 至少包含：

```text
case_id
feature
precondition
input_actions
expected_intermediate_states
expected_final_state
reverse_path
fixture
expected.json
```

Golden Case 一旦进入版本控制：

> 后续 Playwright 必须守住该行为，不得由开发模型为了让测试通过而随意修改 expected。

---

## 4. 第一批必须建立的 Golden

### RECT-001

矩形框选：

```text
mouseDown 点 = 固定锚点
当前 pointer = 当前对角点
mouseUp 点 = 最终对角点
```

断言：

- 起点不漂移；
- 中间状态矩形几何正确；
- 最终范围正确；
- 四方向一致。

### DOCK-001

右侧 Dock：

```text
EXPANDED
→ COLLAPSED
→ EXPANDED
```

必须完整闭环。

### DOCK-002

底部 Dock：

同上。

### VIEWPORT-001

Pan：

```text
移动 Camera
不修改 Scene World Geometry
```

### VIEWPORT-002

Zoom：

pointer 附近缩放时，目标 World Point 的屏幕位置变化必须在定义容差内。

### VIEWPORT-003

Fit：

- 简单图初始 zoom 不超过 100%；
- 复杂图允许缩小显示全貌。

### FIDELITY-ARROW-001

使用确定性 Native Scene Fixture：

```text
Original/Headless Relation
→ scene.json
→ scene.svg
→ Web
```

Arrow 的 Native ID、方向、位置必须保持一致。

---

## 5. Golden 生命周期

```text
Draft Fixture
↓
Contract Validated
↓
Automated
↓
Regression Protected
```

所谓 `Contract Validated` 指：

> Golden 的 expected 可以从明确契约、原生确定性输出或数学规则中推出。

不需要人工签字或人工确认。

---

## 6. 测试失败时禁止

禁止：

```text
测试失败
→ 直接修改 expected
```

必须先判断：

```text
实现错误
测试实现错误
Fixture版本错误
契约已正式变更
版本上下文不一致
```

如果确实修改 Golden，必须记录：

```text
why_changed
contract_reference
old_expected
new_expected
version_context
impact
```

---

## 7. Bug 如何转成自动化回归

正确流程：

```text
发现可复现Bug
↓
定义最小复现输入
↓
从行为契约/原生事实推导正确expected
↓
先写失败的Playwright/Contract回归测试
↓
再修实现
↓
测试转绿
```

禁止：

```text
先修实现
↓
再根据修后的行为写测试
```

---

## 8. Oracle 与实现隔离

推荐：

```text
tests/acceptance-golden/
```

例如：

```text
RECT-001/
├── fixture.json
├── expected.json
├── contract_ref.txt
└── notes.md
```

实现代码不得读取 Golden 来决定产品运行逻辑。

---

## 9. 自动化完成声明

核心连续交互要宣称 PASS，至少需要：

```text
Behavior Contract
Golden Fixture
Playwright / Contract Test
Screenshot / Trace / Debug State
```

当前阶段不把人工验收作为必要条件。
