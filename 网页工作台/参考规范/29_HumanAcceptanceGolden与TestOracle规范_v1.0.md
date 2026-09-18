> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Human Acceptance Golden 与 Test Oracle 规范

## 1. 文档目的

本项目存在大量连续人机交互。

开发模型可能出现：

```text
自己理解需求
↓
按自己的理解实现
↓
按自己的理解写 Playwright
↓
全部 PASS
↓
真实用户操作发现行为并不正确
```

本文件用于防止“实现与测试共享同一个错误理解”。

---

## 2. Test Oracle

Test Oracle 指：

> **什么结果才算真正正确。**

Oracle 应来自：

- 明确的人类交互契约；
- 原生 BEH 可重复事实；
- Human Acceptance Golden；
- 稳定数据契约；
- 已确认的产品行为。

禁止根据“当前实现已经是什么样”反向定义 Oracle。

---

## 3. Human Acceptance Golden

对于关键连续交互，第一次正式实现时必须由人确认至少一个 Golden Case。

Golden Case 应包含：

```text
case_id
功能
前置状态
用户动作
期望中间状态
期望最终状态
反向恢复路径
截图/轨迹证据
确认结论
```

一旦成为 Human Confirmed：

> 后续 Playwright 应守住该行为，不得由开发模型自行修改 expected 来迁就实现。

---

## 4. 第一批必须建立的 Human Acceptance Golden

### RECT-001

矩形框选：

```text
mouseDown 点 = 固定锚点
当前 pointer = 当前对角点
mouseUp 点 = 最终对角点
```

人工确认：

- 起点不漂移；
- 中途矩形正确；
- 最终范围正确。

### DOCK-001

右侧 Dock：

```text
展开 → 收起 → 展开
```

完整闭环。

### DOCK-002

底部 Dock：

同上。

### VIEWPORT-001

Pan：

```text
移动 Camera
不移动图元 World Geometry
```

### VIEWPORT-002

Zoom：

pointer 附近缩放时，关注点不能明显被甩离。

### VIEWPORT-003

Fit：

- 简单图初始不自动放大超过 100%；
- 复杂图允许先缩小显示全貌。

### FIDELITY-ARROW-001

原生 BEH 明确存在箭头的 Golden Relation：

```text
Original BEH
→ Headless Scene
→ Web
```

方向和位置必须一致。

---

## 5. Golden 生命周期

```text
Draft
↓
Human Confirmed
↓
Automated
↓
Regression Protected
```

只有 Human Confirmed 后，才能作为稳定 Oracle。

---

## 6. 测试失败时禁止

禁止：

```text
测试失败
→ 直接修改 expected
```

必须判断：

```text
实现错误
测试错误
Golden过期
需求真实变更
```

如果确实要修改 Golden，必须记录：

```text
why_changed
old_behavior
new_behavior
impact
human_confirmation
```

---

## 7. 手动缺陷如何转成自动化

正确流程：

```text
用户发现真实Bug
↓
记录最小复现
↓
定义正确行为
↓
形成Human Acceptance Case
↓
先写会失败的Playwright回归测试
↓
再修实现
↓
测试转绿
```

禁止：

```text
先修实现
↓
再写一个能通过的测试
```

---

## 8. Oracle 与实现隔离

推荐维护：

```text
tests/human-golden/
```

例如：

```text
RECT-001/
├── case.yaml
├── expected.json
├── reference.png
└── notes.md
```

实现代码不得读取 Golden 来决定产品运行逻辑。

---

## 9. 首次完成声明

对于核心连续交互：

```text
Playwright PASS
```

不能单独代表完成。

首次进入阶段门禁前至少同时需要：

```text
Behavior Contract
Human Golden
Playwright
Screenshot / Trace
```
