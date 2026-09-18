# BEH AI 图源工作台：总体设计书

## 1. 产品定义

建立一个面向 BEH / PLC 图源的本地人机统一图形工作台。

核心目标：

> **人看到的图、AI理解的图、Review审查的图、未来AI生成的图，全部指向同一份 Graph IR。**

---

## 2. 产品形态

推荐：

> **Local-first Desktop Web Workspace**

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

不建议核心做成纯云 SaaS，因为：

- XML 可能几十 MB；
- 数据可能敏感；
- 后续需要本地索引；
- 后续可能连接 BEH.exe；
- 可能需要 UIA / Java Access Bridge / Computer Use。

---

## 3. 总体数据架构

```text
BEH XML
↓
Streaming Parser
↓
Persistent Index / Graph Store
↓
Canonical Graph IR
↓
Review Engine
↓
Reviewed Graph
```

Reviewed Graph 同时服务：

```text
Renderer
AI Explain
人工 Review
Native Verification
AI Compose
BEH Writer / Driver
```

---

## 4. Graph IR 核心对象

至少包含：

```text
Node
Port
VisibleEdge
BoundaryEdge
ImplicitLink
Parameter
Geometry
Scope
Evidence
Unknown
```

任何最终图中的 Edge 必须能够回溯：

```text
relation_id
xml_path
source
target
port
scope
parser_rule
evidence
```

---

## 5. 核心画布

近期推荐：

```text
Sprotty + SVG
```

不再把大量绝对定位 HTML `div` 作为长期核心图形画布。

原因：

- Node / Port / Edge 同坐标系；
- SVG适合箭头、折线、路径；
- 方便 hit-test；
- 方便圈选；
- 方便高亮；
- 后续可以升级 GLSP。

---

## 6. 两种正式视图

### Original View

目标：

> 尽可能接近原生 BEH 中的空间布局。

```text
Node位置
= XML _location / Geometry

Relation
= Reviewed Graph 中的 Approved VisibleEdge
```

### Semantic View

后续使用 ELK 等自动布局：

```text
输入 → 判断 → 处理 → 输出
```

用于：

- AI解释；
- 小白学习；
- 降低交叉；
- 理解复杂簇。

两个 View 共用同一 Object ID。

---

## 7. 图元显示模式

### BEH视觉模式

显示人眼在 BEH 里看到的：

```text
+
M_xxxFlag
TON
```

### 内部模式

显示：

```text
test-3
N173
内部type
```

### 混合模式

主显示：

```text
+
```

小字：

```text
test-3 / N173
```

开发 Review 优先使用混合模式。

---

## 8. 三种主模式

顶部中间：

```text
[ Explain ] [ Compose ] [ Review ]
```

---

## 9. Explain Mode

支持：

```text
矩形
椭圆
Lasso
```

圈选后执行 Graph Hit Test，生成：

```text
Selection Pack
```

AI输出：

- 一句话总结；
- 小白解释；
- 专业解释；
- 输入；
- 处理；
- 输出；
- 参数；
- 不确定项；
- 边界关系。

---

## 10. Compose Mode

逐步支持：

### A. 区域 + 自然语言

```text
圈一块
“这里增加低频持续2秒后告警。”
```

### B. 区域 + 草图

草图作为：

```text
Layout Hint
Flow Hint
```

### C. 区域 + 文字 + 草图

AI同时获得：

```text
空间约束
+
业务意图
+
视觉提示
```

### D. 人工拖图元 + AI补全

用户先放基础节点，AI补：

```text
缺失Node
参数
Relation
```

---

## 11. Review Mode

必须分三层：

```text
图元身份
拓扑关系
Relation身份
```

最终画面对了，不代表 relation_id 就对。

---

## 12. Annotation / Intent Layer

正式图上叠加：

```text
矩形圈
椭圆圈
Lasso
自由笔
草图箭头
Text Note
高亮
```

这些 Annotation 不属于正式 Graph IR Node / Edge。

---

## 13. Proposal Layer

AI生成内容不直接进入正式工程。

先显示：

```text
半透明Node
虚线Edge
Proposal标记
```

Review 后再：

```text
Commit
```

---

## 14. UI 总体布局

```text
┌─────────────────────────────────────────────────────────────┐
│ 项目名          [Explain][Compose][Review]        View/Zoom │
├────┬─────────────┬───────────────────────────┬──────────────┤
│工  │ Project /   │                           │              │
│具  │ Layers /    │        Main Canvas        │  AI Panel    │
│条  │ Components  │                           │              │
│    │             │                           │              │
├────┴─────────────┴───────────────────────────┴──────────────┤
│ Status / Selection / Review / Verification                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 15. 顶部工具栏

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

## 16. 左侧

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

可展开面板：

```text
Project
Layers
Components
```

---

## 17. 右侧 AI Panel

### Explain

```text
Selection摘要
小白解释
专业解释
证据
```

### Compose

```text
目标区域
自然语言
草图
附近端口
Proposal
```

### Review

```text
Suspicious Edges
Relation Identity
Evidence
Native Verification
```

---

## 18. 线的人工 Review

不要要求人逐条双击几千个 relation。

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

Relation ID 作为机器证据和异常调查信息。

可切换显示小徽标：

```text
[r2]
```

---

## 19. 视觉风格

定位：

> 专业、克制、高级工程控制台。

推荐：

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
大面积亮蓝
紫蓝渐变
霓虹
廉价科技感
```

状态：

```text
正常：中性灰
选中：铜金
Verified：苔绿
Unknown：暖琥珀
Error：砖红
Proposal：半透明铜金 + 虚线
```

---

## 20. 人和AI真正统一

不是“AI看相同截图”就算统一。

真正统一：

```text
人点 N103
→ AI收到 N103

人圈 E17
→ AI收到 E17

AI解释 E17
→ UI高亮 E17

AI提出 P91
→ UI显示 Proposal P91
```

核心是共享同一 Object ID。

---

## 21. 最终写入原则

AI不直接自由写 BEH 私有 XML。

AI只输出：

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

再由：

```text
BEH Writer
或
BEH Native Driver
```

落地。

---

## 22. 一句话定义

> **工作台是一层独立于 BEH 私有 XML 的统一图形语义平台：向下连接 BEH XML / BEH.exe，向上连接人和 AI。**
