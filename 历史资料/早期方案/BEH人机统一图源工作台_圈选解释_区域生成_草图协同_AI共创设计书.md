# BEH 人机统一图源工作台设计书
## ——原始坐标复原、圈选解释、区域生成、草图协同与 AI 共创

## 1. 文档目的

本文设计一套面向 BEH 私有 XML 图源的统一人机协作工作台。

它不是单纯的 XML Viewer，也不是单纯的 AI 聊天窗口，而是希望逐步形成：

> **人看到的图、AI 理解的图、程序 Review 的图、未来 AI 生成的图，全部建立在同一份结构化 Graph IR 上。**

近期目标：

1. 尽可能还原 BEH XML 中带坐标的图元；
2. 恢复经过 Review 的 relation / 连线 / 箭头；
3. 允许用户用矩形、圆形、自由套索等方式选择局部图源；
4. AI 能准确解释用户圈选的局部；
5. 为未来“用户圈一块区域 + 自然语言 + 草图 → AI 生成图源”提前建立统一架构。

长期目标：

> **形成一个 AI 与人共同看图、解释图、修改图、生成图的 PLC / BEH 图形语言工作台。**

---

# 2. 产品形态：到底做网页还是桌面应用？

## 2.1 最终建议

推荐形态：

> **Local-first Desktop Web Workspace**  
> 本地优先的桌面 Web 工作台。

它的 UI 使用现代 Web 图形技术实现，但核心数据、XML、索引、Graph IR 都优先在本机处理。

不是典型的：

```text
浏览器
↓
上传几十MB XML到公网服务器
↓
云端处理
```

而是：

```text
本地 BEH XML
      ↓
本地 Parser / Indexer
      ↓
本地 Graph IR
      ↓
Web 图形界面
      ↓
需要 AI 时
只发送经过裁剪、脱敏后的 Selection / Intent Pack
```

## 2.2 第一阶段形态

第一阶段建议：

```text
Local Backend
+
localhost Web App
```

例如：

```text
Python / Node 后端
        ↓
localhost
        ↓
浏览器打开工作台
```

优点：

- 开发最快；
- 调试方便；
- 可以继续利用现有 XML Parser；
- 不需要第一天就处理桌面打包；
- Sprotty / SVG 等 Web 图形框架可直接使用。

## 2.3 第二阶段形态

当工作台稳定后：

> 使用 Tauri 等桌面壳封装为 Windows 桌面应用。

最终用户看到的是：

```text
BEH AI Workspace.exe
```

但里面的图形 UI 仍使用 Web 技术。

这样同时获得：

- 桌面应用体验；
- 本地文件访问能力；
- 本地后端 / sidecar；
- 以后连接 BEH Driver；
- Web 图形生态；
- AI 面板和复杂交互 UI。

## 2.4 为什么不建议做纯在线网站

真实 BEH XML：

- 体积可能几十 MB；
- 包含工作工程数据；
- 后续可能需要本地索引；
- 后续可能需要调用 BEH.exe；
- 后续可能需要 JRE / OpenJDK / UI Automation；
- 可能包含内部代码和私有信息。

所以“纯云端网页”不是最合适的核心形态。

---

# 3. 总体设计思想

整个系统只维护一份核心图模型：

```text
Canonical Graph IR
```

所有功能都围绕它工作。

```text
                   BEH XML
                      │
                      ▼
              Raw XML / Index
                      │
                      ▼
              Normalized Graph IR
                      │
                Structural Review
                      │
                      ▼
               Reviewed Graph
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
  原始坐标视图        AI             Annotation
  Sprotty/SVG       理解/生成        圈选/草图
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                同一个工作台
```

最重要的原则：

> **人和 AI 不维护两张图。**

---

# 4. 核心画布技术

## 4.1 当前建议

第一阶段核心：

> **Sprotty + SVG**

而不是继续使用大量 absolute-position HTML `div` 作为核心绘图层。

## 4.2 为什么使用 SVG 图形画布

PLC / BEH 图源同时包含：

- 图元；
- Port；
- Label；
- Relation；
- 箭头；
- 折线；
- Connector；
- Continuation；
- 高亮；
- 框选；
- 自由套索；
- 草图；
- AI 建议虚影。

这些对象天然属于同一个二维矢量坐标系。

SVG 更适合：

```text
Node
Port
Edge
Arrow
Path
Text
Annotation
```

统一处理。

## 4.3 为什么使用 Sprotty

Sprotty 本身已经具有：

```text
SGraph
SNode
SPort
SEdge
SLabel
```

因此可以比较自然地把：

```text
Graph IR Node
→ SNode

Graph IR Port
→ SPort

Graph IR VisibleEdge
→ SEdge
```

并以 SVG 方式渲染。

## 4.4 什么时候升级到 GLSP

近期：

```text
Graph IR
+
Sprotty
```

足够完成“读图 + 圈选 + AI解释”。

等以后正式进入：

- 拖图元；
- 创建 Edge；
- 参数编辑；
- undo / redo；
- AI 修改模型；
- AI 创建图元；
- Palette；
- Source Model 保存；
- BEH / PLCopen Writer；

再升级为：

```text
GLSP
+
Sprotty
+
Graph IR / Source Model
```

不要现在一次性把 GLSP 全部复杂度带进来。

---

# 5. 两种正式图形视图

## 5.1 Original View：原始坐标视图

作用：

> 最大程度接近人在 BEH 中看到的空间结构。

Node Position：

```text
直接使用 XML 中的 _location / geometry
```

Relation：

```text
使用 Reviewed Graph 中已经确认的 VisibleEdge
```

因此：

```text
节点位置
= BEH原始坐标真值

连线关系
= Graph IR结构真值
```

二者合并。

这是近期最核心的 View。

## 5.2 Semantic View：AI 整理视图

后期增加。

同样的 Node / Edge：

```text
ID不变
```

但交给 ELK 重新排版。

例如原始 BEH：

```text
      C
A ────┘
   B ───────── D
```

Semantic View：

```text
A → B → C → D
```

用途：

- 给小白解释；
- 看清输入 → 处理 → 输出；
- 减少线交叉；
- 快速理解复杂簇。

## 5.3 两种 View 必须同步

例如：

```text
Original View 的 N103
=
Semantic View 的 N103
```

用户点击任意一边：另一边同步高亮。

AI解释 N103：两边同时高亮。

---

# 6. 画布分层

画布不要把所有东西混成一个层。

建议至少分成四层。

```text
Layer 4
AI Proposal Layer
AI建议 / Ghost图元

Layer 3
Annotation / Intent Layer
用户圈选 / 草图 / 箭头 / 文字

Layer 2
Graph Edge Layer
正式Relation / VisibleEdge

Layer 1
Graph Node Layer
正式图元 / Port / Label
```

底层数据仍然是统一 Graph IR。

---

# 7. Annotation / Intent Layer

这是未来人机协作的关键层。

它不是正式 BEH 图元。

用于表达：

> 用户在“想什么”。

支持：

- 矩形；
- 椭圆 / 圆；
- 自由套索；
- 自由笔；
- 草图箭头；
- 文字注释；
- 高亮笔；
- 区域占位；
- AI建议区域。

---

# 8. 圈选工具设计

## 8.1 必须支持的三种区域选择

### 矩形选择

适合快速框一整块。

```text
┌───────────────┐
│ A → B → C     │
└───────────────┘
```

### 圆形 / 椭圆选择

适合自然圈重点。

### 自由套索 Lasso

用户手画一个任意闭合区域。

适合：

- L形结构；
- 弯曲局部；
- 避开旁边很近但不相关的图元；
- 复杂 PLC 图局部。

这是非常重要的模式。

## 8.2 圈选不能只是截截图

画完区域以后必须进行：

```text
Geometry Selection
↓
Graph Hit Test
```

自动得到：

```text
hit_nodes
hit_ports
hit_edges
boundary_edges
annotations
```

形成：

```text
Selection Pack
```

AI获得的是：

```text
结构化 Graph IR
+
区域信息
+
必要时区域预览图
```

而不是只拿一张截图猜。

---

# 9. Explain Mode：AI解释图源

这是第一种主工作模式。

用户：

```text
画矩形 / 圆 / Lasso
```

然后：

```text
“解释这一块”
```

系统：

```text
Selection Geometry
        ↓
Hit Test
        ↓
Selection Pack
        ↓
AI
```

AI输出：

1. 这块整体在做什么；
2. 输入是什么；
3. 中间经过什么判断 / 控制；
4. 输出是什么；
5. 关键参数；
6. 专业解释；
7. 小白解释；
8. 与外部还有哪些边界关系；
9. 哪些地方当前仍不确定。

---

# 10. Compose Mode：AI写图源

第二种主工作模式。

用户首先指定：

> 我要在哪里创建。

例如：

```text
圈出一个空区域
```

系统记录：

```text
Compose Region
```

## 10.1 方式 A：区域 + 纯自然语言

用户：

```text
“把新的低频延时告警逻辑放在这一块。”
```

输入：

```text
Region
+
Text Intent
```

AI生成：

```text
Proposed Graph IR
```

## 10.2 方式 B：区域 + 草图

用户圈一个区域，然后随手画：

```text
[输入] → [判断] → [延时] → [输出]
```

即使非常潦草。

草图只是：

```text
Visual Hint
```

不是正式图元。

AI根据：

```text
Region
+
Sketch
```

生成正式 Graph Proposal。

## 10.3 方式 C：区域 + 自然语言 + 草图

这是非常重要的高级模式。

用户：

1. 圈出生成区域；
2. 画大概布局；
3. 输入文字：

```text
“低于49.8Hz持续2秒再告警。”
```

AI同时得到：

```text
空间约束
+
视觉布局意图
+
业务语义
```

## 10.4 方式 D：人工拖几个图元 + AI补全

长期模式。

用户自己放：

```text
频率输入
比较器
告警
```

然后说：

```text
“中间补一个持续2秒确认，帮我把连接补完整。”
```

AI补：

```text
TON
参数
Relation
```

---

# 11. Explain / Compose / Review 模式选择放在哪里

推荐放在：

> **顶部主工具栏中间**

使用明显的 Segmented Control：

```text
[ 解释 Explain ] [ 创作 Compose ] [ 审查 Review ]
```

原因：

这是整个工作台最重要的“意图状态”。

不应该藏在右键菜单或二级设置里。

---

# 12. 左侧工具栏设计

画布左侧放一条窄的纵向工具条。

根据模式动态变化。

## Explain Mode 工具

```text
① Pointer
② 矩形选择
③ 椭圆选择
④ 自由套索
⑤ Pan / Hand
```

保持非常简单。

## Compose Mode 工具

增加：

```text
① Pointer
② 矩形区域
③ 椭圆区域
④ 自由套索
⑤ Freehand 草图笔
⑥ 草图箭头
⑦ Text Note
⑧ Eraser
⑨ Pan / Hand
```

后期再增加：

```text
正式图元 Palette
```

---

# 13. 左侧面板设计

工具条和侧边面板分开。

最左边：

```text
窄工具条
```

旁边可展开：

```text
Project / Layers / Components
```

建议 Tab：

```text
项目
图层
图元库（Compose后期）
```

---

# 14. 右侧 AI 面板

右侧是整个产品的 AI 协作中心。

宽度建议：

```text
320～420px 可拖拽
```

顶部根据模式变化。

## Explain Mode

显示：

```text
当前选择：
12 Nodes
9 Edges
2 Boundary Links

[解释这一块]
```

下面：

```text
一句话总结
小白解释
专业解释
输入/处理/输出
证据
不确定项
```

## Compose Mode

显示：

```text
当前生成区域
草图已识别
附近可连接端口
```

输入框：

```text
“描述你想在这里实现什么……”
```

操作：

```text
[生成建议]
[继续修改]
```

## Review Mode

显示：

```text
Proposed Nodes
Proposed Edges
Warnings
Unknown
Evidence
```

操作：

```text
[接受]
[部分接受]
[拒绝]
```

---

# 15. AI Proposal Layer

AI生成的新东西不能直接进入正式图。

必须先显示为：

> **Ghost / Proposal**

例如：

- 半透明节点；
- 虚线 relation；
- 铜金轮廓；
- 未确认标识。

流程：

```text
AI Proposed Graph
        ↓
Proposal Layer
        ↓
Review
        ↓
Accept
        ↓
正式 Graph IR
```

这样不会让 AI 悄悄改正式工程。

---

# 16. 区域生成约束

用户圈一个生成区域以后，不应该只有：

```text
bbox
```

还应该形成：

```text
allowed_region
preferred_region
forbidden_obstacles
nearby_ports
nearby_nodes
preferred_flow_direction
```

例如：

```text
Region R12

允许：
在这个区域内生成

禁止：
覆盖 N101 / N102

推荐入口：
N87.OUT

推荐出口：
Alarm.IN
```

这会显著提升 AI生成质量。

---

# 17. 草图数据模型

草图一定与正式 Graph IR 分开。

例如：

```json
{
  "annotation_id": "ANN_102",
  "type": "FREEHAND_STROKE",
  "points": [[100,200],[108,205],[120,211]],
  "mode": "COMPOSE"
}
```

草图箭头：

```json
{
  "annotation_id": "ANN_103",
  "type": "SKETCH_ARROW",
  "from": [300,200],
  "to": [500,200]
}
```

文字：

```json
{
  "annotation_id": "ANN_104",
  "type": "TEXT_NOTE",
  "text": "这里延时2秒"
}
```

AI读取这些 Annotation，但它们不是正式 Edge / Node。

---

# 18. Selection Pack

Explain Mode 圈选后生成：

```json
{
  "selection_id": "SEL_001",
  "geometry": {"type": "LASSO"},
  "nodes": [],
  "ports": [],
  "edges": [],
  "boundary_edges": [],
  "implicit_links": [],
  "annotations": [],
  "evidence_refs": []
}
```

这是 AI解释的正式输入。

---

# 19. Intent Pack

Compose Mode 生成：

```json
{
  "intent_id": "INTENT_001",
  "target_region": {},
  "existing_context": {},
  "text_prompt": "",
  "sketch_annotations": [],
  "nearby_ports": [],
  "constraints": {},
  "generation_mode": "ADD"
}
```

这是 AI写图源的正式输入。

---

# 20. 主 UI 布局

推荐桌面端整体：

```text
┌──────────────────────────────────────────────────────────────┐
│ Project          [Explain][Compose][Review]      Zoom / View │
├────┬───────────────┬─────────────────────────────┬────────────┤
│    │               │                             │            │
│工  │ Project /     │                             │    AI      │
│具  │ Layers /      │         Main Canvas         │  Assistant │
│条  │ Components    │                             │            │
│    │               │                             │            │
│    │               │                             │            │
├────┴───────────────┴─────────────────────────────┴────────────┤
│ Status / Selection / Review warnings / coordinates           │
└──────────────────────────────────────────────────────────────┘
```

---

# 21. 顶部工具栏

顶部不要堆太多功能。

左：

```text
产品名
项目名
文件
```

中：

```text
[Explain] [Compose] [Review]
```

右：

```text
Original / Semantic
Zoom
Fit
Search
Settings
```

---

# 22. Canvas 中的浮动上下文菜单

用户圈完一个区域以后，在圈选旁边出现小型浮动操作条。

Explain Mode：

```text
[解释] [只看内部] [包含边界] [取消]
```

Compose Mode：

```text
[在这里生成] [添加文字] [开始草图] [取消]
```

不要让用户每次都跑到右侧 AI 面板才能执行最基础操作。

---

# 23. UI 视觉风格

整体定位：

> **专业、克制、高级的工程控制台，而不是赛博霓虹 AI Demo。**

推荐：

```text
主背景：
深石墨黑 / 暖灰

主要表面：
深灰磨砂 / 轻微透明

主强调：
低饱和铜金

辅助状态：
苔绿
砖红
暖琥珀

避免：
大面积亮蓝
紫蓝渐变
霓虹发光
廉价科技感
```

---

# 24. Graph 视觉原则

正式图元：

```text
深灰/暖灰实体
清晰边界
较弱阴影
```

正式关系：

```text
中性浅灰 / 暖灰
箭头清楚
```

选中：

```text
铜金描边
```

AI Proposal：

```text
半透明铜金
虚线
```

未知 / 不确定：

```text
暖琥珀
```

错误 / Review Block：

```text
低饱和砖红
```

已验证：

```text
苔绿小标识
```

---

# 25. 视觉层级原则

不要让整个图都是彩色的。

颜色只表达：

```text
状态
选择
AI建议
风险
```

正常 BEH 图尽量保持：

```text
中性工程色
```

这样长时间看不会累。

---

# 26. Original View 的视觉目标

不是“重新美化成另一张图”。

而是：

> **尽可能接近 BEH 原始空间关系。**

所以：

```text
位置
大小
相对距离
```

优先尊重 XML。

视觉样式可以现代化，但不能破坏结构认知。

---

# 27. Semantic View 的视觉目标

强调：

```text
输入
↓
判断
↓
处理
↓
输出
```

这里可以：

- 自动布局；
- 减少线交叉；
- 正交 routing；
- 聚合复杂子图。

主要服务：

> AI解释和小白学习。

---

# 28. AI 看什么

AI不应该只看最终截图。

AI正式获得：

```text
Selection Pack / Intent Pack
+
Reviewed Graph IR
+
相关参数
+
必要时当前 SVG / 预览图
```

也就是说：

```text
结构理解
+
视觉理解
```

结合。

---

# 29. 人和 AI 的视角如何真正统一

关键不是：

> AI看一张和人一样的截图。

真正统一是：

```text
人点击 N103
AI知道 N103

人圈到 E17
AI收到 E17

AI解释 E17
UI高亮 E17

AI提出 Node P91
用户看到 Proposal P91
```

所有动作共享同一个 Object ID。

---

# 30. Graph IR 是唯一正式事实源

正式图：

```text
Reviewed Graph IR
```

Annotation：

```text
Annotation IR
```

AI生成建议：

```text
Proposal Graph IR
```

三者分离。

禁止把草图直接塞进正式图。

---

# 31. Explain 流程

```text
用户切换 Explain
        ↓
矩形 / 圆 / Lasso
        ↓
Hit Test
        ↓
Selection Pack
        ↓
AI解释
        ↓
UI同步高亮
```

---

# 32. Compose 流程

```text
用户切换 Compose
        ↓
圈生成区域
        ↓
文字 / 草图 / 拖图元
        ↓
Intent Pack
        ↓
AI生成 Proposal Graph
        ↓
Ghost Layer
        ↓
Review
        ↓
Accept
        ↓
正式 Graph IR
```

---

# 33. Review 流程

任何 AI生成内容都必须经过 Review。

```text
Proposal
↓
结构验证
↓
Scope验证
↓
Port验证
↓
Edge验证
↓
用户/规则Review
↓
Commit
```

后期再进入：

```text
BEH Writer / Native BEH Driver
```

---

# 34. 近期第一版不要做什么

暂时不要：

- 完整 GLSP Source Model 编辑；
- BEH XML 自动回写；
- AI直接控制 BEH.exe；
- 全量 Semantic View；
- 所有图元 Palette；
- 手写识别；
- 复杂自由草图识别；
- 多人实时协作。

---

# 35. 第一阶段 MVP

只做：

### 1. Graph IR → Sprotty

将已有带 `_location` 的图元迁移到 Sprotty/SVG。

### 2. Reviewed VisibleEdge

把 Review 通过的 relation 叠加到同一原位图。

### 3. 三种选择

```text
矩形
椭圆
自由套索
```

### 4. Hit Test

得到：

```text
Node IDs
Edge IDs
Boundary Edges
```

### 5. Explain Mode

AI解释 Selection Pack。

---

# 36. 第二阶段

增加：

```text
Compose Region
+
自然语言
```

AI可以在指定区域生成 Proposal Graph。

暂时不需要草图。

---

# 37. 第三阶段

增加：

```text
Freehand Sketch
Sketch Arrow
Text Annotation
```

形成：

```text
Region + Text + Sketch
```

多模态生成。

---

# 38. 第四阶段

增加：

- 图元 Palette；
- 拖图元；
- 人工 Port 连接；
- AI补全；
- 局部重构；
- Semantic View；
- ELK 自动布局。

---

# 39. 第五阶段

升级到：

```text
GLSP + Sprotty
```

正式支持：

- Source Model；
- Operations；
- Undo/Redo；
- AI/Human 共用编辑命令；
- BEH Adapter；
- PLCopen Adapter；
- Native BEH Driver；
- XML / Code Generation。

---

# 40. 推荐技术架构

```text
Desktop Shell
(Tauri later)
        │
        ▼
Web Frontend
        │
        ├── Sprotty / SVG Canvas
        ├── Annotation Layer
        ├── AI Panel
        └── Review UI
        │
        ▼
Local Backend
        │
        ├── BEH XML Streaming Parser
        ├── XML Index
        ├── Graph IR Builder
        ├── Review Engine
        ├── Selection / Intent Pack
        └── AI Orchestrator
        │
        ▼
Local Files
```

---

# 41. 为什么这个结构适合未来接 BEH

以后即使能够控制原生 BEH：

```text
AI
↓
Canonical Graph Operations
↓
BEH Driver
↓
BEH.exe
```

现在的工作台也不需要推翻。

因为核心仍然是：

```text
Canonical Graph IR
```

---

# 42. 最终产品一句话定义

> **一个以 BEH / PLC 图源为核心的本地人机统一图形工作台：人可以在同一张图上查看、圈选、涂鸦、拖画和表达意图，AI则读取同一份 Graph IR，对圈选区域进行解释，或根据区域、自然语言和草图生成新的图元结构；所有 AI修改先以 Proposal 形式出现，Review 后再进入正式工程。**

---

# 43. 当前最推荐的下一步

不要继续扩展旧的 absolute HTML Renderer。

保留现有版本作为对照。

新开一个很小的 PoC：

```text
Graph Workspace PoC
```

输入：

```text
5～10个有_location的Node
+
2～5根Reviewed Relation
+
1个Continuation
```

必须完成：

1. 原始坐标复原；
2. SVG Relation / Arrow；
3. 矩形圈选；
4. 椭圆圈选；
5. Lasso；
6. Hit Test 得到 Node/Edge ID；
7. 右侧展示 Selection Pack；
8. AI解释当前 Selection。

如果这个 PoC 成功：

> 后续正式迁移主 Renderer。

---

# 44. 技术依据与后续扩展参考

- Sprotty 的核心模型直接包含 Node、Port、Edge，并采用 SVG 渲染，适合作为当前 Viewer / Workspace 的核心画布。
- GLSP 的 GModel 同样以 Node、Port、Edge 为基本模型，并默认使用 Sprotty 作为客户端渲染框架，适合后续升级到真正的可编辑图形语言平台。
- Tauri 可作为后期桌面封装层，在保持 Web UI 的同时接入本地文件和 sidecar / 本地后端。

官方参考：

- Sprotty: https://sprotty.org/
- Eclipse GLSP: https://eclipse.dev/glsp/
- Tauri: https://tauri.app/
