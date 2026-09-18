# BEH 图源项目：不可违背的证据与工程原则

## 1. 文档性质

这是本项目的“红线规范”。

开发模型在：

- 修 Bug；
- 找 Relation 规律；
- 修改 Parser；
- 修改 Graph IR；
- 改 Renderer；
- 做 Review；
- 做 AI Agent；

时都必须遵守。

目标是防止：

> **为了让某个样本“看起来通过”，偷偷把输出凑成用户说的样子。**

---

# 2. 第一原则：用户观察是证据，不是实现规则

例如用户明确观察：

```text
原生BEH里这个图元只有1根线出去。
```

这意味着：

```text
这是一个失败样本 / Test Oracle。
```

开发模型应该问：

> 为什么当前程序产生2根？

然后寻找：

```text
一般性原因
```

禁止直接实现：

```text
if node == N173:
    keep_only_one_edge()
```

也禁止：

```text
只要OUT>1就去重成1
```

除非有独立证据证明这是 BEH 的一般规则。

---

# 3. 禁止“为了符合用户描述而硬凑”

用户说：

```text
A和B之间应该是某种连接
```

只能作为：

```text
待验证假设
```

程序必须从：

```text
XML
引用关系
Scope
原生BEH
固定实验
```

中独立验证。

禁止：

```text
先相信结论
再去XML里挑能支持它的证据
```

这叫 confirmation bias，项目中禁止。

---

# 4. 禁止静默去重

这是非常重要的红线。

如果系统发现：

```text
Edge Candidate 1
Edge Candidate 2
```

最终视觉上都像：

```text
A → B
```

禁止：

```text
set(edges)
```

或者：

```text
只保留第一条
```

然后不报告。

必须先判断：

```text
同一原始relation重复解析？
两个不同relation？
不同port？
不同scope？
一条隐式、一条可见？
解析错误？
```

如果不能解释：

```text
DUPLICATE_AMBIGUOUS
```

并保留证据。

---

# 5. 禁止偷偷删除“多出来的线”

如果真实预期1根、程序得到2根：

错误的处理：

```text
用户说只有1根
→ 删除第2根
```

正确：

```text
两根都进入Raw Candidate
↓
分别追Origin
↓
分别验证Scope / Endpoint / Port / Relation Family
↓
找到为什么一根应该被REJECT
```

---

# 6. Raw Evidence 永远不可被覆盖

必须保存：

```text
Raw Candidate
Normalized
Reviewed
Rendered
```

分层产物。

禁止：

```text
Review时直接修改Raw Candidate
```

Raw层代表：

> 当时程序真实发现了什么。

---

# 7. Renderer 禁止创造或删除语义

Renderer只画：

```text
Reviewed Graph
```

禁止：

- 自己补线；
- 自己去重；
- 自己按坐标猜source/target；
- 为了图好看隐藏某条正式Edge；
- 因为线重叠就改变语义。

视觉 routing 可以改变路径，不可改变 Graph Identity。

---

# 8. UNKNOWN 是合法结果

如果证据不足：

```text
UNKNOWN
```

比“猜一个答案”更正确。

允许：

```text
方向UNKNOWN
Relation Family UNKNOWN
Port UNKNOWN
```

禁止为了输出完整率硬填。

---

# 9. Fact / Inference / Hypothesis 必须分开

### FACT

固定证据直接证明。

例如：

```text
XML中存在relation_id=R2
```

### INFERENCE

由多个证据推导。

例如：

```text
R2可能是VisibleEdge
```

### HYPOTHESIS

尚未验证。

例如：

```text
所有Continuation都可能按某种方向解释
```

三者不能混写。

---

# 10. 每根 Edge 必须有 Provenance

最终可见 Edge 至少保存：

```text
edge_id
origin relation_id
xml_path
parser_rule
source
target
port
scope
evidence
review_status
```

没有 origin 的 Edge：

```text
不得成为 VERIFIED
```

---

# 11. Relation Identity 不能因为拓扑一样而忽略

真实：

```text
A -- relation_2 --> B
```

程序：

```text
A -- relation_10 --> B
```

即使视觉都是：

```text
A → B
```

也属于：

```text
解析身份错误
```

必须保留并核验。

---

# 12. 禁止按显示名称认对象

例如两个元素都显示：

```text
+
```

不能据此认为是同一个对象。

优先：

```text
XML identity
稳定ID
Parent Scope
Reference
```

---

# 13. 禁止按坐标接近判断Relation成立

坐标可以用于：

```text
显示
局部候选缩小
视觉定位
```

不能单独证明：

```text
有线
```

---

# 14. 禁止强套公开标准

BEH是私有 XML。

公开标准可以提供：

```text
语义启发
数据模型参照
实验方法
```

但不能：

```text
“标准这样，所以BEH一定这样。”
```

---

# 15. 用户指出一个错误后，正确处理流程

例如用户说：

```text
这个元素只有1根线，你画了2根。
```

必须：

### Step 1

把它注册为：

```text
Failing Case
```

### Step 2

定位：

```text
多出来Edge的origin
```

### Step 3

查：

```text
为什么进入Candidate
为什么通过Review
为什么Renderer画了
```

### Step 4

提出一般性根因假设。

### Step 5

用至少：

```text
该失败样本
+
一个相似正确样本
+
一个不相关回归样本
```

验证。

### Step 6

只有一般规则通过后才修改正式逻辑。

---

# 16. 修复必须解释“为什么”

提交修复必须包含：

```text
Root Cause
Evidence
General Rule
Changed Code Path
Positive Test
Negative Test
Regression Test
Remaining Unknown
```

不能只写：

```text
Fixed extra line.
```

---

# 17. 禁止特例名单不断增长

如果代码出现：

```text
special_case_A
special_case_B
special_case_C
```

必须停下来评估：

> 底层抽象是否错了？

私有 XML 确实可能需要 Relation Family 规则，但 Family 应来自结构证据，而不是某个具体工程 ID。

---

# 18. 规则必须版本化

例如：

```text
RULE_RELATION_FAMILY_03_V2
```

修改后必须跑：

```text
Verified Dataset
```

---

# 19. 任何规则修改必须有反例测试

如果规则说：

```text
结构X = VisibleEdge
```

至少需要：

```text
正例：结构X确实有可见线
反例：类似结构Y不应该被判成线
```

只有正例没有反例不够。

---

# 20. 禁止“测试数据和算法共用同一错误假设”

例如自己生成：

```text
Synthetic XML
```

再用同一套规则生成 Ground Truth。

这可能形成自证循环。

必须保留：

```text
独立官方样本
真实人工观察
原生BEH验证
```

等独立真值源。

---

# 21. AI不能修改测试期望来让测试通过

测试失败时禁止：

```text
actual != expected
→ 修改expected
```

除非有新的独立证据证明旧 expected 本身错了，并记录原因。

---

# 22. 自动化修复必须可追踪

任何：

```text
过滤
去重
合并
重定向
方向翻转
Scope剔除
```

必须记录：

```text
rule_id
input
output
reason
evidence
```

---

# 23. 原生BEH核验优先于模型争论

如果：

```text
Graph IR认为 r10
```

而原生 BEH 弹窗明确显示：

```text
r2
```

则：

```text
Native Evidence > AI推理
```

进入 MISMATCH。

模型不得解释成“也许都可以”。

---

# 24. 不确定时停止扩张影响范围

如果一个 Relation Family 未确认：

禁止让它：

```text
影响所有簇
```

先限制：

```text
UNKNOWN / experimental
```

直到验证。

---

# 25. 不修改原始工程做调查

调试/研究默认只读。

如果确实需要实验修改：

```text
复制工程
隔离环境
明确记录
```

---

# 26. 工作数据不外传

真实 BEH XML 不提供给外部 Codex / 外部模型。

开发：

```text
公开标准样本
合成样本
脱敏结构报告
```

公司内运行固定工具处理真实数据。

---

# 27. 代码评审检查表

每次修改 Relation / Graph 逻辑前问：

```text
[ ] 是否因为用户一个样本直接硬编码？
[ ] 是否存在静默去重？
[ ] 是否丢弃Raw Candidate？
[ ] 是否把Inference当Fact？
[ ] 是否每根新Edge都有origin？
[ ] 是否新增Negative Test？
[ ] 是否跑Verified Dataset？
[ ] 是否可能跨Scope污染？
[ ] 是否只是让图片“看起来对”？
```

任一关键项不满足：

```text
不得合并
```

---

# 28. 最重要的项目哲学

> **我们的目标不是让程序“画得像用户说的那样”，而是让程序用可复现证据独立得到与原生 BEH 一致的事实。**

用户观察用于：

```text
发现错误
提供真值线索
定义测试
```

但程序必须：

```text
自己证明为什么。
```
