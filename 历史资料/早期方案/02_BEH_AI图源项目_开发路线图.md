# BEH AI 图源项目：开发路线图

## 1. 模型与工具条件

公司环境采用：

```text
DeepSeek V4 Flash
+
DeepSeek Harness
+
小视觉模型
```

所有能力以公司实际可验证行为为准。

工程设计原则：

> **工具强、模型职责窄；事实程序化、判断结构化、AI只承担有限推理和编排。**

---

## 2. 主路线

```text
准备步骤
合并现有“坐标视图”和“关系/簇图”能力
        ↓
阶段1
大XML Graph Engine + Explain MVP
        ↓
阶段2
Relation结构化 Review + 原生BEH核验
        ↓
阶段3
DeepSeek Harness + 小视觉模型自动验图 Agent
        ↓
阶段4
Compose人机共创 + AI写图源 + Round-trip
```

---

## 3. 准备步骤：合并已有两条功能链

当前已有两类能力：

```text
A. 根据 _location 精确显示图元
B. 根据 Relation / 簇关系生成关系图
```

不要再长期维护成两个互不相干的最终视图。

应合并成：

```text
Geometry Provider
+
Topology Provider
↓
Graph IR
↓
同一张 Original View
```

详细执行见：

```text
03_现有坐标视图与关系图_合并迁移指南.md
```

---

## 4. 阶段1：Graph Engine + Explain

目标：

```text
几十MB XML
↓
一次解析
↓
Graph Store
↓
Reviewed Graph IR
↓
Original View
↓
圈选
↓
AI解释
```

重点：

- 不让 AI重新扫大 XML；
- Relation必须有 provenance；
- Renderer不创造Edge；
- Selection Pack 小而明确。

---

## 5. 阶段2：Review + Native Verification

目标：

> 从“看起来不准”升级到“明确知道哪条结构记录错”。

增加：

- 图元三显示模式；
- Neighborhood Review；
- Relation identity审计；
- Suspicious Queue；
- 原生 BEH 属性弹窗核验；
- PASS / MISMATCH / UNRESOLVED。

---

## 6. 阶段3：Harness 多模型自动验图

分工：

```text
DeepSeek V4 Flash
= Planner

DeepSeek Harness
= Tool Orchestrator

小视觉模型
= 局部视觉定位

固定程序
= 执行 / 读取 / 精确比较
```

不让视觉模型理解整个图。

不让 V4 Flash 做 exact compare。

---

## 7. 阶段4：Compose + 写图源

按安全顺序：

```text
区域 + 自然语言
↓
区域 + 草图
↓
人工拖图元 + AI补全
↓
Proposal
↓
Review
↓
Writer / Native Driver
↓
BEH保存
↓
Parse Back
↓
Round-trip Compare
```

---

## 8. 并行支线：BEH原生可自动化能力探测

检测：

```text
UIA
Java Access Bridge
Canvas黑盒程度
属性面板
菜单
```

用途：

> 决定阶段2/3能多大程度依赖结构化桌面自动化。

它不是阶段1 Explain MVP 的前置条件。

---

## 9. 并行支线：标准参照

BEH XML 主要是私有语法。

因此：

```text
IEC 61131-3
→ 语义参考

PLCopen / IEC 61131-10
→ 公开连接模型与测试参照
```

禁止：

```text
为了符合标准而修改BEH解释。
```

---

## 10. 每阶段必须有确定性验收

禁止只写：

```text
“看起来好很多”
```

### 阶段1

```text
Graph IR schema tests
Known cluster tests
Selection Pack tests
Explain tests
```

### 阶段2

```text
relation identity
duplicate origin
cross scope
native verification
```

### 阶段3

```text
PASS / MISMATCH / UNRESOLVED 对照人工真值
```

### 阶段4

```text
Proposal → BEH → Parse Back → Semantic Equality
```

---

## 11. 所有阶段遵守两份规范

```text
08_DeepSeekV4Flash_Harness_小视觉模型工程开发规范.md
09_BEH图源项目_不可违背的证据与工程原则.md
```

---

## 12. 总纲

> **先把复杂图源变成固定程序能证明的结构化事实，再让 AI 解释和编排；不要用模型能力掩盖底层结构不确定性。**
