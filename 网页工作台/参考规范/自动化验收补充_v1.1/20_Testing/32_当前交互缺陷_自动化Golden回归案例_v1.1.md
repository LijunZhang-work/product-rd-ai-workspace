# 当前交互缺陷：自动化 Golden 回归案例

## 1. 文档目的

本文件把当前已经复现的问题转成确定性的自动化回归案例。

当前阶段不依赖人工验收。

统一处理顺序：

```text
复现问题
↓
依据行为契约/原生事实确定expected
↓
先写失败回归测试
↓
再修实现
↓
测试转绿
```

---

## 2. GOLDEN-RECT-001：矩形框选起点与落点

### 已复现问题

当前矩形框选并非严格满足：

```text
mouseDown起点固定
当前pointer作为另一角
mouseUp作为最终另一角
```

### 正确 Oracle

依据：

```text
40_UI/28_Web画布交互行为契约
```

正式定义：

```text
mouseDown = A
pointerMove = P
mouseUp = B
```

要求：

- A 全程固定；
- 中途矩形由 A/P 唯一确定；
- 最终区域由 A/B 唯一确定；
- 四方向一致；
- Zoom/Pan 后仍正确。

### 回归测试

```text
anchor remains fixed
current corner follows pointer
final world bounds match A/B
```

---

## 3. GOLDEN-DOCK-001：右侧 Dock 双向状态机

### 已复现问题

```text
可以收起
但没有有效展开路径
```

### 正确 Oracle

```text
EXPANDED
→ COLLAPSED
→ EXPANDED
```

收起后必须保留：

```text
可见
可点击
不被遮挡
语义明确
```

的展开入口。

---

## 4. GOLDEN-DOCK-002：底部 Dock 双向状态机

与右侧 Dock 相同。

---

## 5. GOLDEN-VIEWPORT-001：Pan

### 已复现问题

画布固定，无法通过拖动 Camera 查看大图局部。

### 正确 Oracle

- Pan 改变 Viewport Transform；
- Scene World Geometry 不变；
- Pan 后点击同一对象仍返回同一 Native ID；
- Pan 后 Selection / Lasso 命中不变。

---

## 6. GOLDEN-VIEWPORT-002：Zoom

### 已复现问题

缺少用户可控 Zoom，导致不同复杂度场景显示比例极端。

### 正确 Oracle

至少支持：

```text
+
-
100%
Fit
wheel/trackpad zoom
```

Zoom 只改变 Camera，不改变 World Geometry。

---

## 7. GOLDEN-VIEWPORT-003：初始 Fit 策略

正确 Oracle：

```text
initialZoom = min(1.0, fitZoom)
```

要求：

- 简单图不自动放大超过 100%；
- 复杂图允许缩小到全貌；
- 用户之后仍可自由 Pan / Zoom。

---

## 8. GOLDEN-VIEWPORT-004：Dock变化保持Camera

右/底 Dock：

```text
collapse
expand
resize
```

前后：

```text
zoom保持
pan保持
selection保持
当前关注区域保持
```

不得偷偷自动 Fit。

---

## 9. GOLDEN-FIDELITY-001：Arrow 保真

### 已复现问题

原始 BEH / Headless 原生链中存在 Arrow，但当前 Web 中未显示。

### 排查顺序

```text
Original JAR / Native Runtime
↓
Headless scene.json
↓
Headless scene.svg
↓
Web
```

### 禁止

不得直接在 Web 中自行推导或补画 Arrow。

### PASS 条件

同一固定 Relation Fixture：

```text
Native ID一致
Source/Target一致
Direction一致
Arrow Position一致
scene.svg可见
Web实际可见
```

---

## 10. 自动化阶段门禁

以下全部必须自动化 PASS：

```text
[ ] RECT-001
[ ] RIGHT-DOCK-001
[ ] BOTTOM-DOCK-001
[ ] PAN
[ ] ZOOM
[ ] 100%
[ ] FIT
[ ] SIMPLE-SCENE initial zoom
[ ] LARGE-SCENE initial zoom
[ ] ARROW fidelity
```

任一关键项 FAIL：

```text
不得声明阶段完成
```
