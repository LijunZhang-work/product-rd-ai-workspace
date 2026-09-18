# BEH Native Headless Full Scene 可行性验证文档

## 1. 文档目的

当前已经确认：

- BEH 工具的 JRE + JAR 可以在无 GUI 环境运行；
- 可以解析 POU XML；
- 解析后可以获得部分图元的 SVG 描述；
- 当前已知 `_icondescription` 可以提供图元自身的 SVG 描述；
- 当前未确认完整能力包括：
  - Port 的生成与渲染；
  - Relation / Edge 的生成与渲染；
  - Arrow 的方向与渲染；
  - Relation Path / Routing 的计算；
  - 完整画布是否可以在 Headless 环境中复用原生 Renderer 输出。

本阶段目标不是继续开发 Web UI、Sprotty、AI Agent 或新的 XML 解析逻辑。

本阶段唯一目标是：

> **验证 BEH 原生 Java 代码是否能够在不启动 BEH GUI 的情况下，完整产出与原生 BEH 画布一致的结构化 Scene 和图形描述。**

如果该验证成功，后续架构将优先采用：

```text
BEH Native Headless Java Core
        ↓
Full Native Scene
        ↓
Web 人机协作工作台
        ↓
AI / Harness
```

而不是重新实现第二套 BEH Renderer。

---

# 2. 本阶段禁止事项

在完成本验证前，禁止继续扩展以下方向：

```text
Sprotty 原始画布复刻
新的 Relation 猜测算法
新的 Web Renderer
DeepSeek Harness Agent
GLM / DeepSeek AI Explain
Playwright 自动化
Compose / AI 写图元
大 XML 性能优化
```

原因：

> 当前最大的架构未知不是“AI 能不能理解”，而是“BEH 原生 Java 能不能直接产出完整 Scene”。

必须先验证底层事实。

---

# 3. 验证总目标

最终希望实现一个独立 Headless 调用：

```text
renderPouToFullScene(pouXml)
```

不启动 BEH GUI，直接得到：

```text
FullSceneBundle
├── scene.svg
├── scene.json
├── hit-map.json
├── model.json
└── diagnostics.json
```

其中：

## scene.svg

完整画布视觉描述：

```text
Node
Port
Relation / Edge
Arrow
Label / Text
```

## scene.json

完整场景结构：

```text
Node
Port
Relation
Geometry
Display Text
Z Order
Scope
```

## hit-map.json

用于后续人点击、框选、Lasso：

```text
视觉对象
→ native_id / relation_id / port_id
```

## model.json

原生模型属性：

```text
Node Type
Properties
Source
Target
Port
Parent
Scope
Relation ID
```

## diagnostics.json

输出：

```text
未能解析对象
未能渲染对象
UNKNOWN Relation
缺失 Port
Headless 异常
字体 / Graphics 环境异常
```

---

# 4. 验证样本要求

不要使用几十 MB 大工程作为第一验证样本。

必须先准备一个极小、人工可确认的 POU。

推荐最小结构：

```text
[A] ─────→ [B]
```

要求：

```text
A 有一个明确 OUT Port
B 有一个明确 IN Port
A 与 B 之间只有一根明确 Relation
箭头方向明确为 A → B
```

如果可以，再增加第二个稍复杂样本：

```text
      ┌→ [B]
[A] ──┤
      └→ [C]
```

用于验证：

```text
一个 Source
多个 Relation
多个 Target
```

样本必须能够在原生 BEH GUI 中人工确认。

---

# 5. P0：追踪完整原生绘制调用链

这是本阶段最高优先级。

不要继续围绕 `_icondescription` 猜完整画面。

必须通过源码分析确认：

```text
POU XML
↓
Loader / Parser
↓
Domain Model
↓
Node
↓
Port
↓
Relation
↓
Geometry / Routing
↓
Arrow
↓
Renderer
↓
最终 Canvas
```

需要明确回答以下问题。

---

## 5.1 Node

确认：

```text
Node 对象由哪个类表示？
Node Geometry 从哪里获得？
Display Text 从哪里决定？
_icondescription 在整个绘制链中的职责是什么？
```

输出：

```text
Node Model Class
Node Renderer Class
Node Geometry Source
Node Display Text Source
```

---

## 5.2 Port

重点确认：

```text
Port 是否是真实 Java 对象？
Port 是解析 XML 时创建，还是渲染时动态生成？
Port 是否有稳定 ID？
Port Geometry 在哪里计算？
Port 是否单独 paint / draw？
Port 是否属于 Node Renderer 的一部分？
```

输出：

```text
Port Model Class
Port Geometry Class / Method
Port Renderer
Port Identity Strategy
```

---

## 5.3 Relation / Edge

重点确认：

```text
Relation 对象由哪个类表示？
relation_id 存放在哪里？
source / target 如何获得？
source port / target port 如何获得？
Relation 是否区分多种 Family？
```

输出：

```text
Relation Model Class
Relation ID Source
Source Resolution Method
Target Resolution Method
Port Resolution Method
```

---

## 5.4 Relation Path / Routing

必须找到：

```text
折线路径由谁计算？
路径点是否保存在 Model 中？
还是 Render 时动态计算？
是否存在自动绕线 / Orthogonal Routing？
是否依赖 Canvas / Viewport？
```

输出：

```text
Routing Class
Routing Method
Input
Output
Dependency
```

---

## 5.5 Arrow

必须确认：

```text
Arrow Direction 在哪里决定？
Arrow Shape 在哪里绘制？
箭头位置是 source、target 还是中间？
是否存在不同 Relation 类型不同 Arrow 规则？
```

输出：

```text
Arrow Direction Rule
Arrow Renderer
Arrow Geometry Source
```

---

# 6. P0：确认是否存在统一 Graphics2D 渲染链

源码重点搜索：

```text
Graphics
Graphics2D
paint
paintComponent
draw
drawLine
drawPolyline
drawString
Path2D
GeneralPath
Stroke
AffineTransform
FontMetrics
```

目标是回答：

> **Node、Port、Relation、Arrow、Text 是否最终都进入同一个或兼容的 Graphics2D 绘制链？**

---

## 6.1 如果答案是 YES

例如存在类似：

```java
renderer.paint(Graphics2D g)
```

并且内部完整绘制：

```text
Node
Port
Relation
Arrow
Text
```

则优先验证：

```text
Screen Graphics2D
替换为
SVGGraphics2D
```

目标：

> 复用原生绘制代码直接导出完整 SVG，而不是重新实现 Renderer。

此路径优先级最高。

---

## 6.2 如果答案是 NO

继续分类：

```text
Node Renderer
Port Renderer
Relation Renderer
Arrow Renderer
```

分别确认它们是否能够在 Headless 环境独立调用。

最终仍要求：

```text
原生 Geometry / 原生 Renderer
→ Full Scene Exporter
```

禁止把 Edge / Port 重新交给 Web 或 Sprotty 推导。

---

# 7. P1：Headless 原生模型完整性验证

在不启动 BEH GUI 的环境中加载最小 POU。

必须输出结构化结果。

至少包括：

## Node

```text
native_id
internal_name
display_text
type
bounds
```

## Port

```text
port_id
owner_node_id
port_type
direction
position
```

## Relation

```text
relation_id
source_node_id
source_port_id
target_node_id
target_port_id
direction
```

## Geometry

```text
Node Bounds
Port Position
Relation Path Points
Arrow Position / Direction
```

---

# 8. P1：Headless 真实性要求

不能仅仅：

```text
电脑有桌面环境
BEH GUI 没打开
```

就认为 Headless 成功。

至少要证明：

```text
不启动 BEH GUI
↓
独立 Java 进程
↓
直接加载 JRE + JAR
↓
解析 POU XML
↓
生成 Native Model
↓
生成 Node / Port / Relation / Geometry
↓
输出 JSON / SVG
```

如果需要：

```text
-Djava.awt.headless=true
```

则记录具体行为。

如果某些功能在真正 `java.awt.headless=true` 下失败，也必须记录：

```text
FAIL 原因
依赖的 GUI / Graphics 能力
是否可通过 Offscreen Graphics 解决
```

禁止掩盖。

---

# 9. P1：GUI 与 Headless 结构一致性验证

同一个最小 POU：

## 原生 GUI 人工确认

记录：

```text
Node 数量
Node 显示名称
Port 数量
Relation 数量
Relation ID
Source / Target
Arrow Direction
Node 大致坐标
Relation Path
```

## Headless 输出

输出同样字段。

建立对照表：

| 项目 | GUI | Headless | 结果 |
|---|---|---|---|
| Node 数量 |  |  | PASS / FAIL |
| Display Text |  |  | PASS / FAIL |
| Port 数量 |  |  | PASS / FAIL |
| Relation 数量 |  |  | PASS / FAIL |
| Relation ID |  |  | PASS / FAIL |
| Source / Target |  |  | PASS / FAIL |
| Arrow Direction |  |  | PASS / FAIL |
| Node Geometry |  |  | PASS / FAIL |
| Relation Path |  |  | PASS / FAIL |

本阶段先追求：

> **结构一致性 100%。**

像素级一致可后续单独验证。

---

# 10. P1：视觉对象与原生对象身份绑定验证

未来目标不是只有：

```text
SVG 里出现一个 +
```

而是：

```text
这个 +
=
native_id: test-3
```

必须验证 Renderer 绘制时是否知道当前对应的原生对象。

目标输出类似：

```xml
<g data-native-id="test-3">
    ...
</g>
```

Relation：

```xml
<path data-relation-id="relation-2" ... />
```

Port：

```xml
<circle data-port-id="port-17" ... />
```

如果原生 Renderer 无法直接写入这些属性，则必须建立：

```text
Rendered Primitive
↔
Native Object
```

稳定映射。

禁止依赖：

```text
坐标最近
显示文字相同
SVG 顺序相同
```

作为主身份规则。

---

# 11. P1：Hit Test 能力验证

未来人需要：

```text
点击
框选
Lasso
```

所以必须调查原生 BEH 是否已有：

```text
hitTest(x, y)
getElementAt(x, y)
selection model
contains(point)
intersects(rect)
```

验证：

```text
点击图元
→ native_node_id

点击 Relation
→ native_relation_id

点击 Port
→ native_port_id
```

如果原生 Hit Test 可复用，优先直接复用。

如果没有，则 Full Scene Exporter 必须导出：

```text
bounds
path
hit_shape
```

供 Web 层做几何 Hit Test。

---

# 12. P2：Full Native Scene Export PoC

只有 P0 + P1 成功后开始。

目标接口：

```text
renderPouToFullScene(pouXml)
```

输出：

```text
scene.svg
scene.json
hit-map.json
model.json
diagnostics.json
```

---

# 13. scene.json 推荐最小结构

示例：

```json
{
  "scene_version": "0.1",
  "viewport": {},
  "nodes": [
    {
      "native_id": "test-3",
      "internal_name": "test-3",
      "display_text": "+",
      "type": "xxx",
      "bounds": {
        "x": 100,
        "y": 200,
        "width": 60,
        "height": 40
      }
    }
  ],
  "ports": [
    {
      "port_id": "port-1",
      "owner_node_id": "test-3",
      "direction": "OUT",
      "position": {
        "x": 160,
        "y": 220
      }
    }
  ],
  "relations": [
    {
      "relation_id": "relation-2",
      "source_node_id": "test-3",
      "source_port_id": "port-1",
      "target_node_id": "test-4",
      "target_port_id": "port-2",
      "path_points": [],
      "arrow_direction": "SOURCE_TO_TARGET"
    }
  ]
}
```

---

# 14. diagnostics.json 必须真实记录未知项

例如：

```json
{
  "unknown_ports": [],
  "unknown_relations": [],
  "unrendered_objects": [],
  "headless_warnings": [],
  "font_warnings": [],
  "renderer_failures": []
}
```

禁止为了输出完整：

```text
猜 Port
猜 Relation
猜 Direction
猜 Path
```

UNKNOWN 是合法结果。

---

# 15. 成功标准

## P0 成功

以下全部明确：

```text
✓ Node 绘制链
✓ Port 生成 / 绘制链
✓ Relation 解析链
✓ Relation Routing
✓ Arrow Direction
✓ 最终 Renderer
✓ 是否可 Headless 调用
```

## P1 成功

最小真实 POU 在不启动 GUI 的情况下：

```text
✓ Node
✓ Display Text
✓ Port
✓ Relation ID
✓ Source
✓ Target
✓ Direction
✓ Geometry
```

均能从原生 Java 代码获得，并且与 GUI 人工真值一致。

## P2 理想成功

能够生成：

```text
✓ Full Native scene.svg
✓ scene.json
✓ hit-map.json
```

其中：

```text
Node / Port / Relation
↔
native ID
```

可以稳定一一对应。

---

# 16. 失败也必须分类

如果无法完整 Headless，不允许简单写：

```text
不可行
```

必须归因到具体层级：

```text
A. Parser 可 Headless
B. Model 可 Headless
C. Port 依赖 GUI
D. Relation Geometry 依赖 Canvas
E. Renderer 依赖 Graphics Environment
F. FontMetrics 依赖 GUI
G. Native Hit Test 依赖组件
```

并说明是否能通过以下方式解决：

```text
Offscreen Component
BufferedImage Graphics2D
SVGGraphics2D
Mock Graphics Context
提取 Geometry Service
```

---

# 17. 本阶段输出物

最终必须提交：

```text
01_native_render_pipeline.md
02_headless_capability_matrix.md
03_minimal_pou_ground_truth.md
04_headless_scene_output.json
05_gui_vs_headless_diff.md
06_full_scene_feasibility_conclusion.md
```

如果生成 SVG：

```text
07_full_scene.svg
```

如果有实验程序：

```text
poc/
```

但不要为了 PoC 大规模重构生产代码。

---

# 18. 最终报告必须回答的 10 个问题

1. `_icondescription` 在完整 Renderer 中到底负责什么？
2. Port 在哪里产生？
3. Port 在哪里绘制？
4. Relation 从哪里解析？
5. Source / Target / Port 如何解析？
6. Relation Path 由谁计算？
7. Arrow Direction 和 Arrow Shape 由谁决定？
8. Node / Port / Relation 是否最终走 Graphics2D？
9. 完整 Scene 是否可以真正 Headless 生成？
10. 是否可以让每个视觉对象稳定绑定 native ID？

---

# 19. 后续阶段进入条件

只有本验证基本通过后，才进入：

```text
Full Scene Web Viewer
↓
Playwright
↓
Selection / Lasso / Annotation
↓
DeepSeek Harness
↓
GLM / DeepSeek Explain
↓
Compose / AI修改图元
```

如果 Headless Full Scene 不成立，则重新评估架构。

禁止在结论未知时继续堆上层功能。

---

# 20. 核心原则

> **不要再尝试“理解 BEH 怎么画，然后重新画一遍”。**

本阶段要证明的是：

> **能否直接调用 BEH 原生 Java 代码，让它自己在 Headless 环境中产出完整、可查询、可绑定 native ID 的 Scene。**

如果可以：

```text
BEH 原生代码
= 唯一图形事实源

Web
= 人机交互层

AI
= 理解、规划与生成层
```

这将成为后续整个 AI 图源平台的基础。
