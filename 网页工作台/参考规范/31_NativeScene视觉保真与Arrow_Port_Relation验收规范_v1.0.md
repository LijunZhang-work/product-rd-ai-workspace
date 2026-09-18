> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Native Scene 视觉保真与 Arrow / Port / Relation 验收规范

## 1. 文档目的

正式 Web 原生视图不得重新发明 BEH 图形语义。

必须证明：

> 原生 BEH 已确认存在的视觉与结构事实，在 Headless Scene 和 Web 中没有丢失。

重点：

```text
Node
Port
Relation
Arrow
Label
Display Text
Geometry
```

---

## 2. 三段式保真链

任何视觉缺失先定位：

```text
A. Original BEH / Original JAR
↓
B. Headless Native Scene
↓
C. Web Workbench
```

禁止看到 Web 缺 Arrow 后，直接在 Web 手工补 marker。

---

## 3. Arrow 排查

### Case A：Headless scene.svg 也没有 Arrow

问题属于：

```text
Native Scene Exporter / Headless Renderer
```

Web 不允许自行修补。

应追：

- 原生 Arrow Geometry；
- 原生 Arrow Renderer；
- Relation Style；
- SVG Exporter；
- diagnostics。

### Case B：scene.json 有 Arrow，scene.svg 没有

属于：

```text
NativeScene结构与视觉不一致
```

直接 FAIL。

### Case C：scene.svg 单独打开有 Arrow，Web 中没有

属于：

```text
Web Rendering / SVG Embedding
```

排查方向：

- `<defs>`；
- `<marker>`；
- marker-start / marker-end；
- SVG id 冲突；
- CSS；
- clipPath；
- sanitizer；
- transform；
- SVG注入方式。

不能改变 Relation 语义来修视觉问题。

---

## 4. Arrow Golden

至少建立：

```text
ARROW-001：A → B
```

Original BEH 人工确认：

- relation native_id；
- source；
- target；
- direction；
- arrow position。

自动验证：

```text
scene.json arrow事实 PASS
scene.svg arrow视觉 PASS
Web arrow视觉 PASS
```

三层全部 PASS 才通过。

---

## 5. Port Golden

至少覆盖：

- 单输入；
- 单输出；
- 多输入；
- 多输出；
- INOUT；
- 不同位置 Port。

验证：

```text
native_id
owner
direction
world position
SVG visual
hit-map
Web click
```

---

## 6. Relation Golden

至少：

- 直线；
- 折线；
- 多段路径；
- 一源多分支；
- 多输入；
- Connector / Continuation；
- 交叉但不相连；
- 相同显示符号不同 Native ID。

---

## 7. SVG / Scene / HitMap 一致性

每个正式可见对象：

```text
scene.json
↔
scene.svg
↔
hit-map
```

必须可追踪对应。

如果 `scene.json` 有对象但 SVG 不可见：

```text
diagnostics 必须解释
否则 FAIL
```

---

## 8. Web 保真约束

Web 加载 Native Scene 后不得：

- 丢 marker；
- 改 Arrow Direction；
- 改 Relation Path；
- 改 Port Position；
- 隐藏原生 Label；
- 重排 Node；
- 重算 Geometry；
- 用前端规则重建正式 BEH Edge/Arrow。

Web 只允许叠加：

```text
Camera Transform
Selection Overlay
Annotation Overlay
Analysis Highlight
Proposal Overlay
```

---

## 9. 验证优先级

```text
1. Native ID / Relation / Arrow / Geometry 结构断言
2. Headless SVG DOM
3. Web SVG DOM
4. Screenshot Regression
```

Screenshot 不能作为唯一 Oracle。

---

## 10. 阶段门禁

以下任一存在时，不得宣称原生视图保真通过：

```text
Arrow丢失
Port丢失
Relation Path改变
Display Text错误
Native ID映射错误
Scene JSON / SVG不一致
Web自行补画正式Edge/Arrow
```
