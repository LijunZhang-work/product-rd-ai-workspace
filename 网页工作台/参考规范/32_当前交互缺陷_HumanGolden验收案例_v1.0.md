> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 当前交互缺陷：Human Golden 验收案例

## 1. 文档目的

本文件把当前人工测试已经发现的问题直接转成可执行验收案例。

正确顺序：

```text
先确认正确行为
↓
写失败回归测试
↓
再修实现
```

禁止“先修完，再补一个能通过的测试”。

---

## 2. HG-RECT-001：矩形框选起点与落点

### 当前发现

人工测试发现：

> 实际框选并非严格从 mouseDown 点开始，拖动行为与预期不一致。

### 正确行为

```text
mouseDown = A
pointerMove = P
mouseUp = B
```

要求：

- A 全程固定；
- 中途矩形由 A/P 决定；
- 最终区域由 A/B 决定；
- 四方向一致；
- Zoom/Pan 后仍正确。

### 回归测试

必须先验证：

```text
anchor remains fixed
current corner follows pointer
final world bounds match A/B
```

---

## 3. HG-DOCK-001：右侧 Dock 必须可双向切换

### 当前发现

```text
能收起
但没有有效展开路径
```

### 正确状态机

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
语义清楚
```

的展开入口。

---

## 4. HG-DOCK-002：底部 Dock 同样闭环

与右侧相同。

---

## 5. HG-VIEWPORT-001：画布必须支持 Pan

### 当前发现

画布固定，无法通过拖动 Camera 查看大图不同区域。

### 正确行为

- Pan 改 Viewport；
- 不改 World Geometry；
- Pan 后点击仍命中同一 Native ID；
- Pan 后 Selection/Lasso 仍准确。

---

## 6. HG-VIEWPORT-002：画布必须支持 Zoom

### 当前发现

没有用户可控 Zoom，导致不同复杂度场景显示比例极端。

### 正确行为

至少支持：

```text
+
-
100%
Fit
滚轮/触控板 Zoom
```

---

## 7. HG-VIEWPORT-003：简单图与复杂图初始比例

推荐初次打开：

```text
initialZoom = min(1.0, fitZoom)
```

要求：

- 简单图不自动放大超过 100%；
- 复杂图可以缩小到全貌；
- 用户可随后自由 Zoom / Pan。

---

## 8. HG-VIEWPORT-004：Dock变化不得重置Camera

右侧/底部 Dock：

```text
collapse
expand
resize
```

前后必须保持：

```text
zoom
pan
selection
当前关注区域
```

---

## 9. HG-FIDELITY-001：原生 Arrow 必须保留

### 当前发现

Original BEH 中明确存在 Arrow，但当前 Web 中未看到。

### 正确排查顺序

```text
Original BEH
↓
Headless scene.json
↓
Headless scene.svg
↓
Web
```

禁止直接在 Web 中补 Arrow。

### PASS 条件

同一 Golden Relation：

```text
Native ID一致
Source/Target一致
Direction一致
Arrow Position一致
Web实际可见
```

---

## 10. 当前阶段最低人工复验

修复后至少人工重新验证：

```text
[ ] 矩形框选
[ ] 右侧收起/展开
[ ] 底部收起/展开
[ ] Pan
[ ] Zoom
[ ] 100%
[ ] Fit
[ ] 简单图初始比例
[ ] 复杂图初始比例
[ ] Arrow
```

任一关键项 FAIL：

```text
不得声明阶段完成
```
