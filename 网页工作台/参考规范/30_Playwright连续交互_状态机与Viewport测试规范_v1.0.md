> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Playwright 连续交互、状态机与 Viewport 测试规范

## 1. 文档目的

普通 E2E 容易只验证：

```text
点过
出现过
隐藏了
有结果
```

本文件要求对连续交互验证：

```text
开始
→ 中途
→ 结束
→ 反向恢复
```

---

## 2. Pointer Trace 测试

重要拖动功能必须有可复现轨迹：

```text
pointerDown
pointerMove 1
pointerMove 2
pointerMove 3
pointerUp
```

关键节点要检查真实页面状态。

---

## 3. Rect Selection

### RECT-PW-001 固定锚点

```text
down A
move P1
assert anchor == A

move P2
assert anchor == A

move P3
assert anchor == A
```

### RECT-PW-002 中途尺寸

例如：

```text
A=(100,100)
P=(300,250)
```

归一化结果应为：

```text
x=100
y=100
width=200
height=150
```

### RECT-PW-003 最终落点

```text
down(100,100)
up(500,400)
```

最终 Selection World Geometry 必须与转换后的 A/B 一致。

### RECT-PW-004 四方向

四个拖动方向全部测试。

---

## 4. Viewport 测试矩阵

至少覆盖：

| 条件 | 必须 |
|---|---|
| Zoom 100% | 是 |
| Zoom 50% | 是 |
| Zoom 200% | 是 |
| Pan 后点击 | 是 |
| Pan 后框选 | 是 |
| 右 Dock 展开 | 是 |
| 右 Dock 折叠 | 是 |
| 底部 Dock 展开 | 是 |
| 底部 Dock 折叠 | 是 |
| 纯画布模式 | 是 |

---

## 5. Pan

### PAN-PW-001

空白画布拖动：

- Viewport Transform 改变；
- Node World Geometry 不变；
- Selection World Geometry 不变。

### PAN-PW-002

Pan 后点击同一 Node：

```text
native_id 保持一致
```

### PAN-PW-003

Pan 后矩形 / Lasso 命中仍正确。

---

## 6. Zoom

### ZOOM-PW-001

工具栏 +/- 必须产生真实 zoom 变化。

### ZOOM-PW-002

滚轮 / 触控板 Zoom 后：

```text
zoom改变
world geometry不变
```

### ZOOM-PW-003

以 pointer 附近 World Point 为中心缩放，前后 screen 位置偏差必须在定义容差内。

### ZOOM-PW-004

`100%`：

```text
zoom == 1.0
```

### ZOOM-PW-005

Fit：

- 简单场景 `zoom <= 1.0`；
- 复杂场景可缩小；
- Fit 后用户仍可继续 Pan/Zoom。

---

## 7. Dock 状态机

### RIGHT-DOCK-PW-001

```text
EXPANDED
→ collapse
→ COLLAPSED
→ expand control visible
→ expand
→ EXPANDED
```

### RIGHT-DOCK-PW-002

```text
collapse / expand × 5
```

不能失效。

### BOTTOM-DOCK-PW-001

同样测试。

### DOCK-PW-003

折叠/展开前后：

```text
zoom不变
pan不变
selection不变
active tab恢复
```

---

## 8. Lasso

必须验证：

- world points；
- polygon闭合；
- CONTAIN / INTERSECT；
- Zoom后不漂移；
- Pan后仍能正确命中；
- Space+Pan 不污染 Lasso Points。

---

## 9. Freehand

测试目标是：

```text
笔迹保存
坐标正确
Zoom/Pan后不漂移
```

不是测试“AI是否理解语义”。

必须断言：

```text
Freehand Stroke
≠
正式 Relation
```

---

## 10. Interaction Debug State

开发/测试模式建议暴露只读状态：

```json
{
  "pointer": {
    "screen": [0,0],
    "canvas": [0,0],
    "world": [0,0]
  },
  "viewport": {
    "panX": 0,
    "panY": 0,
    "zoom": 1
  },
  "gesture": {
    "type": "RECT_SELECTION",
    "anchorWorld": [0,0],
    "currentWorld": [0,0]
  }
}
```

Playwright 可读取此状态验证坐标链。

生产模式可关闭该接口。

---

## 11. 不允许的“PASS”

以下情况不能标记整个功能 PASS：

- 只测最终 DOM 存在；
- 只测按钮可点击；
- 只测 Panel hidden；
- 只测 Selection 非空；
- 没测中途状态；
- 没测反向恢复；
- 没测 Zoom/Pan 下坐标一致性。

---

## 12. 失败证据

连续交互失败至少保存：

```text
trace.zip
before screenshot
mid screenshot
after screenshot
console
viewport state
interaction debug state
```
