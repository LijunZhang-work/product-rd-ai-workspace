> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Web 画布交互行为契约

## 1. 文档目的

本文件定义 Web Workbench 画布交互的真实用户行为。

它不是功能清单，也不是视觉精修说明。

任何开发模型、前端实现和 Playwright 测试在实现以下功能前，必须先遵守本文件：

- Pan；
- Zoom；
- Fit；
- 100%；
- 矩形框选；
- 椭圆框选；
- Lasso；
- 自由笔；
- Dock 折叠/展开；
- Dock Resize；
- 点击与 Hit Test；
- 画布坐标转换。

核心原则：

> **不能只证明“按钮存在”或“最终有结果”，必须证明用户从开始动作到结束动作的整个交互轨迹正确。**

---

## 2. 画布坐标体系

必须明确区分：

```text
Screen Coordinate
↓
Canvas Local Coordinate
↓
BEH World Coordinate
```

### 2.1 Screen Coordinate

浏览器窗口中的 pointer 坐标。

### 2.2 Canvas Local Coordinate

相对于画布容器左上角的坐标。

必须考虑：

- 左侧导航宽度；
- 顶部栏高度；
- 右侧 Dock；
- 底部 Dock；
- 页面滚动；
- 浏览器 viewport。

### 2.3 BEH World Coordinate

与 NativeSceneBundle 的 `BEH_WORLD` 一致。

所有正式 Selection、Annotation、Intent、Hit Test 结果必须最终保存为 BEH World Coordinate。

禁止将屏幕像素直接保存为正式选择数据。

---

## 3. Viewport / Camera 模型

Native Scene 几何与用户视口必须完全分离。

Native Scene 中的：

```text
Node / Port / Relation / Label Geometry
```

必须始终保持原始 BEH World 坐标。

用户视口单独维护：

```text
panX
panY
zoom
viewportWidth
viewportHeight
```

禁止因为浏览器大小、Dock 展开/折叠或用户 Zoom 改写正式世界坐标。

---

## 4. Pan 行为契约

Pan 是移动 Camera，不是移动图元。

### 4.1 基本路径

```text
浏览模式
↓
在空白画布 mouseDown
↓
保持按住并拖动
↓
Viewport 平移
↓
mouseUp
```

建议同时支持：

```text
Space + 左键拖动
鼠标中键拖动
```

### 4.2 必须满足

- 图元彼此相对位置不变；
- Node / Port / Relation 世界坐标不变；
- zoom 不变；
- Selection 世界坐标不变；
- Annotation 世界坐标不变；
- Pan 后点击同一图元仍得到同一 Native ID；
- Pan 后框选/Lasso 仍能正确命中；
- Pan 操作本身不得生成 Selection；
- 圈选/手绘模式下，`Space + drag` 可以临时 Pan 时，不得污染当前手势轨迹。

---

## 5. Zoom 行为契约

### 5.1 最低支持

```text
鼠标滚轮 / 触控板
工具栏 +
工具栏 -
100%
Fit
```

### 5.2 鼠标中心缩放

用户在 pointer 所在位置 P 缩放时，缩放前后 P 指向的 World Point 应尽可能保持在同一屏幕位置。

禁止每次缩放都只围绕画布中心，导致正在观察的对象被明显甩离。

### 5.3 Zoom 不得改变

- Native Scene World Geometry；
- Selection World Geometry；
- Annotation World Geometry；
- Relation 语义；
- Hit Map 语义。

---

## 6. 100% 行为契约

点击 `100%`：

```text
zoom = 1.0
```

默认不应强制执行 Fit。

应尽量保持用户当前观察区域附近内容。

---

## 7. Fit 行为契约

Fit 只负责：

> 在当前 viewport 中尽可能完整显示当前 Scene。

推荐初次打开策略：

```text
initialZoom = min(1.0, fitZoom)
```

含义：

- 简单图即使 Fit 可放到 200% 或 300%，初次也不自动放大超过 100%；
- 复杂图可以缩小以先看到全貌；
- 用户之后可以自由 Pan / Zoom。

Fit 是明确的 Camera 操作，不得在以下动作后偷偷自动触发：

- Dock 折叠；
- Dock 展开；
- Dock Resize；
- Selection 变化；
- Analysis Result 加载；
- Annotation 更新。

---

## 8. Viewport Continuity

以下操作必须保持 Camera 连续：

- 右侧 Dock 折叠/展开；
- 底部 Dock 折叠/展开；
- Dock Resize；
- 分析结果加载；
- Selection 变化；
- Annotation 变化；
- 代码面板打开/关闭。

必须尽量保持：

```text
zoom
pan
当前关注区域
selection
```

只有用户明确执行：

```text
Fit
100%
Reset View
```

才允许主动改变 Camera 策略。

---

## 9. 矩形框选行为契约

### 9.1 正式定义

用户：

```text
mouseDown = A
pointerMove current = P
mouseUp = B
```

必须满足：

```text
A = 整个拖动过程中的固定锚点
P = 当前对角点
B = 最终对角点
```

拖动过程中的可见矩形始终由 A 与 P 确定。

最终 Selection Geometry 由 A 与 B 确定。

### 9.2 内部归一化

可以使用：

```text
x = min(A.x, B.x)
y = min(A.y, B.y)
width = abs(B.x - A.x)
height = abs(B.y - A.y)
```

但不得导致用户看到的初始锚点在拖动过程中漂移。

### 9.3 必须覆盖四个方向

```text
左上 → 右下
右下 → 左上
左下 → 右上
右上 → 左下
```

---

## 10. 椭圆框选行为契约

椭圆使用和矩形一致的：

```text
mouseDown anchor
current pointer
mouseUp final point
```

其外接矩形由起点和当前点确定。

禁止默认实现成“从中心向外扩张”，除非未来产品明确增加独立的中心椭圆模式。

---

## 11. Lasso 行为契约

```text
mouseDown
↓
持续采样 world points
↓
mouseUp
↓
闭合 polygon
↓
执行 Selection
```

要求：

- 点序列保存为 BEH World Coordinate；
- Zoom / Pan 后重新显示不漂移；
- mouseUp 前不提交最终 Selection；
- 极短轨迹应按阈值取消；
- 使用 Space 临时 Pan 时，Pan 轨迹不得写入 Lasso 点集。

---

## 12. Freehand 行为契约

自由笔保存：

```text
stroke_id
world_points
tool
order
```

自由笔本身只代表原始用户笔迹。

不得自动生成：

```text
正式 Relation
正式 Node
确定业务语义
```

没有用户文字或其他可靠证据时，语义允许为 `UNKNOWN`。

---

## 13. Dock 折叠/展开行为契约

每个 Dock 必须是完整双向状态机：

```text
EXPANDED
⇄
COLLAPSED
```

禁止只实现：

```text
EXPANDED → COLLAPSED
```

### 13.1 收起后必须保留

- 明确可见的展开入口；
- 可点击；
- 不被 Canvas / Overlay 覆盖；
- 有明确可发现的交互含义；
- 支持键盘访问；
- ARIA 状态正确。

### 13.2 展开后必须恢复

- Panel 主体；
- 收起入口；
- 上一次宽度/高度；
- 上一次 Tab；
- Camera 不重置；
- Selection 不丢失。

---

## 14. Dock Resize 行为契约

Resize 必须：

- 有稳定拖拽区域；
- 有合理 min/max；
- 不能把画布压成 0；
- 不改 Scene World Geometry；
- 不自动 Fit；
- 可记忆上一次尺寸。

---

## 15. 核心完成定义

任何上述功能不能仅凭：

```text
按钮存在
DOM存在
最终结果非空
Playwright显示PASS
```

宣称完成。

必须至少验证：

```text
起始状态
用户动作
中途状态
最终状态
反向恢复
坐标正确性
真实页面视觉结果
```
