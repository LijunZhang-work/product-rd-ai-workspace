# BEH AI 图源项目：DeepSeek 弱模型适配开发路线图

## 1. 本路线针对什么模型条件

公司环境按保守条件设计：

```text
DeepSeek V4 Flash
= 旧版 / Preview级能力
= 不按最新正式版Agent增强能力设计

DeepSeek Harness
= 官方开发者预览
= 插件 / 工具 / Agent编排框架

小视觉模型
= 能力有限
= 只承担局部视觉任务
```

因此架构原则：

> **工具强，模型弱；事实程序化，判断结构化，AI只做它擅长的有限推理。**

---

# 2. 不采用的开发思路

禁止：

```text
几十MB XML
→ 直接塞给 V4 Flash
→ “你帮我找线”
```

禁止：

```text
小视觉模型
→ 看完整BEH复杂画布
→ “请理解整个PLC图”
```

禁止：

```text
AI觉得A和B应该连
→ 直接生成正式Edge
```

禁止：

```text
AI自由改BEH XML
```

---

# 3. 总路线

分为四个主阶段。

```text
阶段1
大XML Graph Engine + Explain MVP
        ↓
阶段2
Relation结构化 Review + 原生BEH核验基础
        ↓
阶段3
DeepSeek Harness + 小视觉模型 自动验图Agent
        ↓
阶段4
Compose人机共创 + AI写图源 + Round-trip
```

并行支线：

```text
A. BEH原生自动化能力检测
B. PLCopen / IEC标准参照实验
```

支线不阻塞紧急“读图”主线。

---

# 4. 阶段1：先让AI真正读懂局部图

目标：

```text
几十MB BEH XML
↓
一次解析
↓
Graph Store
↓
Reviewed Graph IR
↓
Sprotty Original View
↓
圈选
↓
AI解释
```

关键产物：

- XML Streaming Parser；
- ID / Parent / Ref / Relation / Location Index；
- Graph Store；
- Graph IR；
- Edge Provenance；
- Original View；
- Selection Pack；
- Explain工具。

这一阶段尽量不让 AI参与底层解析。

---

# 5. 阶段2：先把准确性问题变得可审计

目标：

> 从“图看起来好像不对”，升级为“明确知道哪条结构记录错”。

关键：

```text
Raw Candidate
↓
Normalized
↓
Reviewed
↓
Rendered
```

增加：

- Neighborhood Review；
- 图元三显示模式；
- Relation身份自动审计；
- Suspicious Queue；
- 原生BEH核验任务格式；
- 固定的双击/弹窗/复制工具。

阶段2先不做智能 Agent。

---

# 6. 阶段3：Harness Agent化

在阶段2工具稳定后：

```text
V4 Flash
= Planner

Harness
= Tool Orchestrator

Small Vision
= Localizer

Fixed Tools
= Executor + Verifier
```

Agent只负责：

```text
下一步调用哪个工具？
点错后是否重试？
什么时候停止并UNRESOLVED？
```

不负责：

```text
relation_id精确比较
XML引用计算
Graph算法
```

---

# 7. 阶段4：AI写图源

先从最安全的：

```text
圈区域 + 自然语言
```

开始。

再扩展：

```text
+ 草图
+ 人工拖图元
+ AI补全
```

所有生成先进入：

```text
Proposal Graph
```

最后走：

```text
Review
→ Writer / Native Driver
→ BEH保存
→ 再解析
→ Round-trip Compare
```

---

# 8. 并行支线A：BEH原生接入能力检测

继续保留之前的：

```text
JAB
UIA
Canvas黑盒程度
菜单/属性面板可访问性
```

但它不是紧急读图 MVP 的前置条件。

用途：

> 决定阶段2/3能有多少原生自动化能力。

---

# 9. 并行支线B：标准参照

BEH主要是私有 XML。

因此标准研究用途改成：

```text
IEC 61131-3
→ 语义参考

PLCopen / IEC 61131-10
→ 公开图形数据模型参照

标准巨大XML
→ Graph Engine性能与查询器训练场
```

而不是：

```text
强行把BEH解析成IEC XML。
```

---

# 10. 为什么适合旧 V4 Flash

旧 V4 Flash 主要承担：

```text
局部解释
规则比较
工具选择
任务规划
异常归纳
```

而不会承担：

```text
50MB检索
全局图构建
精确图算法
exact match
桌面坐标执行
```

这样模型弱一点仍然可以工作。

---

# 11. 每阶段必须有确定性验收

禁止：

```text
“看起来比以前好了”
```

必须：

阶段1：

```text
Graph IR schema test
Selected Pack test
已知小簇 Explain test
```

阶段2：

```text
relation identity test
duplicate edge test
scope test
native verification sample
```

阶段3：

```text
自动验图 PASS/MISMATCH/UNRESOLVED准确率
```

阶段4：

```text
Proposal → BEH → Parse Back → Semantic Equality
```

---

# 12. 发布策略

每个阶段都必须：

```text
小样本
↓
固定回归
↓
真实局部
↓
扩大规模
```

不能：

```text
一开始整工程。
```

---

# 13. 一句话总纲

> **先把复杂问题拆成固定工具能证明的事实，再让旧版 V4 Flash 在 Harness 中做有限规划和解释；不要用模型能力补偿底层结构不确定性。**
