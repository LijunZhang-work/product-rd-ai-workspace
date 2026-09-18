# BEH AI 图源工作台：最新总体设计书

## 1. 产品定义

目标不是做一个简单 XML Viewer。

最终产品定义：

> **一个面向 BEH / PLC 图源的本地人机统一图形工作台：人和 AI 看到并操作同一份 Graph IR；人可以圈选、拖图、草绘和用自然语言表达意图，AI可以解释、审查、补全和生成图源。**

---

# 2. 近期与长期目标

## 近期

先解决：

```text
AI能够读懂局部图源
```

包括：

- 图元身份；
- 原始位置；
- Relation；
- 箭头；
- Continuation；
- 局部簇；
- 参数；
- 给小白解释。

---

## 长期

走到：

```text
人 + AI共同写图源
```

输入可以是：

```text
自然语言
草图
人工拖图元
区域约束
已有图局部
```

输出：

```text
Proposal Graph
→ Review
→ Verified Graph
→ BEH Writer / Driver
```

---

# 3. 产品形式

## 推荐

```text
Local-first Desktop Web Workspace
```

第一阶段：

```text
本地后端
+
localhost Web UI
```

成熟后：

```text
Tauri
→ Windows桌面应用
```

不建议核心做成纯云 SaaS。

---

# 4. 核心数据架构

系统只维护一套正式图模型：

```text
Canonical Graph IR
```

核心对象：

```text
Node
Port
VisibleEdge
BoundaryEdge
ImplicitLink
Parameter
Geometry
Evidence
Scope
Unknown
```

关系：

```text
BEH XML
↓
Raw Index
↓
Graph Engine
↓
Graph IR
↓
Review
↓
Reviewed Graph
```

人、AI、Renderer都围绕 Reviewed Graph。

---

# 5. 大 XML 原则

BEH XML 可能几十 MB。

禁止：

```text
每次AI解释
→ 重新把大XML交给模型
```

正确：

```text
大XML
↓
一次性流式解析
↓
Node / Relation / Reference / Scope Index
↓
Graph Store
↓
局部查询
```

AI只接收几十 KB 级：

```text
Selection Pack
```

而不是几十 MB XML。

---

# 6. Graph-first 思想

参考 graph-first / provenance-first 架构：

```text
原始文件
→ 一次抽取
→ 持久图
→ 查询图
```

但是视觉“簇”不能使用知识图谱社区发现算法。

视觉簇定义仍然是：

```text
Reviewed VisibleEdges
↓
Connected Components
```

---

# 7. 核心画布

近期：

```text
Sprotty + SVG
```

不再继续强化：

```text
absolute HTML div
```

作为核心画布。

原因：

- Node / Port / Edge / Label同坐标系；
- 原生支持矢量线和箭头；
- 适合框选、缩放、平移；
- 适合 Annotation；
- 后续可升级 GLSP。

---

# 8. 两种正式视图

## Original View

```text
Node位置
= BEH XML _location

Relation
= Reviewed Graph
```

目标：

> 尽量和人眼 BEH 接近。

---

## Semantic View

后期用 ELK 自动布局：

```text
输入 → 判断 → 处理 → 输出
```

用于：

- AI解释；
- 小白学习；
- 复杂簇降噪。

两种 View 共用同一 Node / Edge ID。

---

# 9. 图元显示三模式

## BEH视觉模式

显示人眼在 BEH 中看到的：

```text
+
M_xxxFlag
TON
```

---

## 内部模式

显示：

```text
test-3
N173
内部type
```

---

## 混合模式

主显示：

```text
+
```

小字：

```text
test-3 / N173
```

开发 Review 默认推荐混合模式。

---

# 10. 主工作模式

顶部中间：

```text
[ Explain ] [ Compose ] [ Review ]
```

这是整个工作台最重要的状态切换。

---

# 11. Explain Mode

工具：

```text
Pointer
矩形选择
椭圆选择
Lasso
Pan
```

圈选后生成：

```text
Selection Pack
```

包括：

```text
Node
Edge
Boundary Edge
Implicit Link
Parameter
Evidence
```

AI输出：

- 一句话总结；
- 小白解释；
- 专业解释；
- 输入 / 处理 / 输出；
- 关键参数；
- 不确定项。

---

# 12. Compose Mode

支持四种逐渐增强的方式。

## A. 区域 + 自然语言

用户圈一块空区域：

```text
“这里增加一个低频持续2秒后告警逻辑。”
```

---

## B. 区域 + 草图

用户画：

```text
[输入] → [判断] → [延时] → [输出]
```

草图只是提示，不是正式图元。

---

## C. 区域 + 文字 + 草图

AI同时获得：

```text
空间约束
+
业务意图
+
布局提示
```

---

## D. 人工拖图元 + AI补全

用户先放：

```text
频率
比较器
告警
```

AI补：

```text
TON
参数
Relation
```

---

# 13. Review Mode

三层：

```text
图元身份 Review
拓扑 Review
Relation 身份 Review
```

重点不是盯着图瞎猜。

任何 Edge 都必须可展开：

```text
relation_id
source
target
port
scope
evidence
xml path
parser rule
```

---

# 14. Annotation / Intent Layer

正式图之上增加：

```text
矩形圈
椭圆圈
Lasso
自由笔
草图箭头
Text Note
高亮
```

Annotation 永远不是正式 Graph Node / Edge。

---

# 15. AI Proposal Layer

AI生成的内容先显示：

```text
半透明图元
虚线Relation
Proposal标记
```

只有 Review 通过后：

```text
Commit
```

进入正式 Graph IR。

---

# 16. UI整体布局

```text
┌─────────────────────────────────────────────────────────────┐
│ 项目名          [Explain][Compose][Review]        View/Zoom │
├────┬─────────────┬───────────────────────────┬──────────────┤
│工  │ Project /   │                           │              │
│具  │ Layers /    │        Main Canvas        │  AI Panel    │
│条  │ Components  │                           │              │
│    │             │                           │              │
├────┴─────────────┴───────────────────────────┴──────────────┤
│ Status / Selection / Warnings / Verification               │
└─────────────────────────────────────────────────────────────┘
```

---

# 17. 顶部

中间：

```text
Explain / Compose / Review
```

右侧：

```text
Original / Semantic
BEH视觉 / 混合 / 内部
Zoom
Fit
Search
```

---

# 18. 左侧

窄工具条：

```text
Pointer
Rect
Ellipse
Lasso
Pen
Arrow
Text
Pan
```

旁边：

```text
Project
Layers
Components
```

---

# 19. 右侧 AI Panel

## Explain

```text
当前选择
一句话总结
小白解释
专业解释
证据
```

## Compose

```text
目标区域
文字意图
草图状态
附近端口
生成建议
```

## Review

```text
风险项
Edge Provenance
Relation ID
Native Verification
```

---

# 20. Relation Review UI

不要让人逐条双击几千根线。

日常 Review 看：

```text
当前Node
IN数量
OUT数量
邻居列表
```

例如：

```text
+
IN: 2
OUT: 1

输入：
M_EnableFlag
M_FreqLow

输出：
TON_2
```

Relation ID 默认不占主视觉。

可切换：

```text
[显示Relation身份]
```

用小徽标显示：

```text
[r2]
```

---

# 21. Visual Style

整体：

> 专业、克制、高级工程控制台。

颜色：

```text
深石墨黑
暖灰
低饱和铜金
苔绿
砖红
暖琥珀
```

避免：

```text
亮蓝
大面积紫蓝渐变
霓虹
廉价科技感
```

---

# 22. 视觉状态

```text
正常：中性灰
选中：铜金
Verified：苔绿
Unknown：暖琥珀
Blocked / Error：砖红
AI Proposal：半透明铜金 + 虚线
```

---

# 23. 人和AI如何真正统一

不是只让 AI看截图。

真正统一：

```text
人点 N103
→ AI收到 N103

人圈 E17
→ AI收到 E17

AI解释 E17
→ UI高亮 E17

AI提出 P91
→ 人看到 Proposal P91
```

核心是共享 Object ID。

---

# 24. 长期写入

AI不直接自由生成 BEH 私有 XML。

AI输出：

```text
CreateNode
SetParameter
Connect
Move
Delete
```

即：

```text
Canonical Graph Operations
```

然后：

```text
BEH Writer
或
BEH Native Driver
```

负责真正落地。

---

# 25. 最终一句话

> **工作台不是“AI看图工具”，而是一层独立于 BEH 私有 XML 的统一图形语义平台：向下连接 BEH XML / BEH.exe，向上连接人和 AI。**
