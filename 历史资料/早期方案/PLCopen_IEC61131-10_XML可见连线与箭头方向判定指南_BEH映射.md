# PLCopen / IEC 61131-10 XML：可见连线、图元与箭头方向判定指南
## ——用于 BEH XML / `relation` / `continuation` 反向分析

> **目标**
>
> 本文不是要强行假设某个 BEH 工具完全等同于 PLCopen XML，而是先把 PLCopen XML / IEC 61131-10 的标准数据模型研究清楚，再把它作为分析 BEH XML 的“基准模型”。
>
> 最终解决两个问题：
>
> 1. XML 里的哪些东西代表用户真正看到的**连接线**？
> 2. 一条连接在不同图元之间时，应该怎样判断**真实信号/箭头方向**？

---

# 1. 先记住最重要的结论

对于 PLCopen / IEC 61131-10 图形语言：

> **不能通过“XML 谁包含谁”“谁引用谁”“坐标点从前到后”直接判断箭头方向。**

最可靠的方向判定原则是：

```text
ConnectionPointOut
= Producer / Source
= 数据生产端 / 输出端
= 箭头从这里出去

              ↓

ConnectionPointIn
= Consumer / Target
= 数据消费端 / 输入端
= 箭头进入这里
```

因此真正的语义方向始终优先理解成：

```text
OUT / Producer  ─────────→  IN / Consumer
```

---

# 2. 为什么会出现“XML 看起来和箭头反了”

这是 PLCopen XML 中非常重要、也非常容易看错的一点。

PLCopen XML v2.01 对 `connection` 的定义明确区分了：

- 数据消费端（consumer）
- 数据生产端（producer）

标准的典型存储方式是：

```text
消费者 / 输入端
    │
    └── connection
          │
          └── refLocalId = 生产者的 localId
```

也就是说，XML 看起来像：

```text
B
└── connection refLocalId="A"
```

但真正的数据流是：

```text
A ─────────→ B
```

不是：

```text
B ─────────→ A
```

因为：

```text
A = Producer / ConnectionPointOut
B = Consumer / ConnectionPointIn
```

所以：

> **`connection` 写在谁下面，不代表箭头从谁出发。**

---

# 3. `refLocalId` 到底表示谁

PLCopen XML v2.01 和 IEC 61131-10 的标准模型都给出了一个非常关键的规则：

> `refLocalId` 标识的是 **connection 从哪个元素开始**。

因此，如果有：

```xml
<ElementB localId="20">
    <connectionPointIn>
        <connection refLocalId="10"/>
    </connectionPointIn>
</ElementB>
```

则应该解释为：

```text
localId=10
    │
    │  source
    ▼
localId=20
```

即：

```text
10 ─────────→ 20
```

而不是：

```text
20 ─────────→ 10
```

---

# 4. 更危险：连接线的坐标列表也可能是“反着存”的

这是分析 BEH `relation` 时尤其值得注意的地方。

PLCopen XML v2.01 对连接路径的描述中，位置点列表包含：

```text
输入 / Consumer 一端
↓
若干折点
↓
输出 / Producer 一端
```

IEC 61131-10 的机器可读 Code Components 也明确把连接位置描述为有序的连接路径，并指出当位置存在时，列表包含 consumer/input 端。

因此可能出现：

## 实际信号方向

```text
A.OUT ───────────────────→ B.IN
```

## XML position 数组

```text
position[0] = B.IN
position[1] = 中间折点
position[2] = 中间折点
position[n] = A.OUT
```

于是：

```text
position[0] → position[n]
```

可能恰好是：

```text
B → A
```

而真正信号方向却是：

```text
A → B
```

所以：

> **绝对不要用 position 点数组的顺序直接判断箭头方向。**

坐标主要用于：

```text
线画在哪里
怎么拐弯
经过哪些点
```

而不是优先用于：

```text
谁向谁发送数据
```

---

# 5. XML 中哪些东西是真正的“连接线”

这里必须把“连接线”和“看起来像线的图元”分开。

---

## 5.1 第一类：真正连接两个图形对象的线

### PLCopen XML v2.01

核心对象：

```text
connection
```

标准明确把它定义为：

> 一个数据消费元素和数据提供元素之间的 graphical coupling（图形连接）。

它可能包含：

```text
refLocalId
formalParameter
position[]
```

其中：

```text
refLocalId
```

负责找到连接来源。

```text
formalParameter
```

负责在多输出图元上进一步定位具体输出端口。

```text
position[]
```

负责描述线路径。

所以对“视觉簇”来说：

> **标准 `connection` 是最重要的显式连线依据。**

---

## 5.2 IEC 61131-10:2019

IEC 61131-10:2019 当前标准在 `Connections` 中明确列出：

```text
ConnectionPointIn
Connection
FeedbackConnection
ConnectionPointOut
```

因此当前标准已经明确区分：

```text
普通 Connection
FeedbackConnection
```

两类连接结构。

### 注意

对于 BEH：

如果 XML 中叫：

```text
relation
```

不要直接说：

```text
relation = PLCopen Connection
```

更准确的说法应该是：

> `relation` 很可能是 BEH 厂商自己的“显式图形关系线”对象，其角色可能对应或扩展标准中的 `Connection` / `FeedbackConnection`。

必须通过实际 XML 和 Java 程序验证。

---

# 6. 标准中没有一个通用的 `relation` 元素

在 PLCopen XML v2.01 标准 XSD 中，没有找到标准元素：

```xml
<relation>
```

IEC 61131-10:2019 的标准连接章节使用的是：

```text
Connection
FeedbackConnection
```

而不是：

```text
Relation
```

因此如果 BEH XML 中存在：

```xml
<relation ...>
```

应该优先认为：

> **这是 BEH / 厂商自己的命名或扩展模型，而不是 PLCopen 标准元素名。**

但是它仍然可能遵循 PLCopen 相似的：

```text
Producer
↓
Connection
↓
Consumer
```

语义。

---

# 7. 第二类：“人眼看起来像线”，但它本身是图元，不是连接边

这是做视觉簇时非常容易误判的地方。

标准中有一些元素本身画出来就是：

- 竖线
- 横线
- 接点线
- 线圈
- 分支横杠
- 汇合横杠

但这些对象应该在图结构中作为：

```text
Node / 图元
```

而不是：

```text
Edge / Relation
```

---

# 8. LD（梯形图）中的线状图元

## 8.1 `leftPowerRail`

它是一个真正的图形对象：

```text
leftPowerRail
```

它有：

```text
ConnectionPointOut
```

而没有对应的普通输入连接点。

因此方向角色是：

```text
LeftPowerRail
      │
      ▼
   OUT / Source
```

也就是：

```text
LeftPowerRail ─────→ 后续梯形图元素
```

它在画面上通常像一根竖直电源母线。

但算法上应该理解成：

```text
一个“有输出端口的图元”
```

而不是普通 relation 线。

---

## 8.2 `rightPowerRail`

标准定义它拥有：

```text
ConnectionPointIn
```

因此：

```text
前级 ─────→ RightPowerRail
```

它是：

```text
Consumer / Sink
```

同样，它可能在 UI 上看起来是一根竖线，但它是：

```text
图元
```

不是普通连接边。

---

## 8.3 `contact`

LD 的 `contact` 同时有：

```text
ConnectionPointIn
ConnectionPointOut
```

因此：

```text
上游
  │
  ▼
contact
  │
  ▼
下游
```

它在梯形图中内部会画出接点符号和短线。

这些线：

> 属于 `contact` 图元自己的符号外观。

它和邻居之间真正的连接关系，仍然应该通过：

```text
Connection
ConnectionPointIn
ConnectionPointOut
```

恢复。

---

## 8.4 `coil`

`coil` 同样同时具有：

```text
ConnectionPointIn
ConnectionPointOut
```

因此：

```text
上游 ───→ coil ───→ 下游
```

其内部的线圈图形：

```text
( )
```

是图元符号本身。

不要把这些内部笔画识别成 relation。

---

# 9. FBD 中的方向规则

FBD 是判断 BEH 图元箭头方向时非常有参考价值的一类。

---

## 9.1 旧 PLCopen：`inVariable`

PLCopen XML v2.01 明确把：

```text
inVariable
```

称为：

```text
Producer
```

它具有：

```text
connectionPointOut
```

因此不要望文生义认为：

```text
inVariable
= 箭头进入它
```

实际上是：

```text
inVariable ─────────→ Block
```

因为这里的 “in” 表示：

> 它是当前 FBD 网络的输入数据来源。

从网络内部看，它是在向后面提供数据。

---

## 9.2 旧 PLCopen：`outVariable`

标准把：

```text
outVariable
```

称为：

```text
Consumer
```

它拥有：

```text
connectionPointIn
```

所以：

```text
Block ─────────→ outVariable
```

而不是：

```text
outVariable → Block
```

---

## 9.3 `inOutVariable`

它同时具有：

```text
ConnectionPointIn
ConnectionPointOut
```

因此仅仅看到：

```text
inOutVariable
```

这个元素类型，还不足以判断某条线的方向。

必须继续看：

> 这根连接落在它的 `ConnectionPointIn` 还是 `ConnectionPointOut`。

---

# 10. IEC 61131-10:2019 的 FBD 命名更清楚

当前 IEC 61131-10:2019 已使用更直接的概念：

```text
DataSource
DataSink
```

理解方式：

```text
DataSource
= 数据源
= Producer
= ConnectionPointOut 一侧
```

因此：

```text
DataSource ─────────→ 后续图元
```

而：

```text
DataSink
= 数据汇 / 消费端
= ConnectionPointIn 一侧
```

因此：

```text
前级图元 ─────────→ DataSink
```

这个命名比旧版：

```text
inVariable / outVariable
```

更不容易把方向看反。

---

# 11. Block 中的端口怎么判断方向

Function / Function Block 的端口不要只看 Block 本身。

标准把 Block 的端口分成：

```text
InputVariables
InOutVariables
OutputVariables
```

---

## InputVariable

具有：

```text
ConnectionPointIn
```

所以：

```text
外部 Producer ─────→ Block.Input
```

---

## OutputVariable

具有：

```text
ConnectionPointOut
```

所以：

```text
Block.Output ─────→ 外部 Consumer
```

---

## InOutVariable

同时具有：

```text
ConnectionPointIn
ConnectionPointOut
```

需要根据具体端口决定。

---

# 12. `connector`：最容易看反的元素之一

PLCopen 标准中的：

```text
connector
```

具有：

```text
ConnectionPointIn
```

所以从局部可见连线看：

```text
上游 ─────────→ connector C1
```

也就是：

```text
connector
= 接收端
= Consumer side
```

因此：

> 如果 BEH 中某个 `relation` 的一端连到了标准语义的 connector，那么箭头应该朝 connector 这一侧进入。

---

# 13. `continuation`：方向和 connector 正好相反

标准明确规定：

```text
continuation
```

是：

```text
connector 的 counterpart
```

并且 continuation 有：

```text
ConnectionPointOut
```

所以局部可见线应该理解成：

```text
continuation C1 ─────────→ 下游
```

而不是：

```text
下游 ─────────→ continuation C1
```

因此如果 BEH XML 里：

```text
continuation
```

对应的 relation 在 XML 结构上看起来像“别人引用它”或者路径点顺序从下游指回来，

不要立刻认定箭头也应该跟着 XML 顺序。

标准语义首先告诉你：

```text
Continuation = OUT / Producer
```

因此：

```text
箭头应从 Continuation 向外
```

这是一个非常重要的候选规则。

---

# 14. Connector 与 Continuation 之间有没有一根可见长线？

一般不要把它们直接当成一根连续可见线。

概念上：

```text
上游 ──→ [Connector C1]

          …… 隐式继续 ……

[Continuation C1] ──→ 下游
```

它们表达的是：

> 一条逻辑关系在画面其他位置继续。

因此这里存在两类不同关系：

## 局部视觉关系

```text
上游 ──→ Connector
```

以及：

```text
Continuation ──→ 下游
```

这些局部线可以进入“视觉簇”。

---

## 跨区域隐式关系

```text
Connector C1
      ·········
Continuation C1
```

这不是连续的肉眼可见长线。

因此如果你的“簇”定义是：

> 只有用户真正看到的连续连线才算同一个簇，

那么：

```text
Connector
```

和：

```text
Continuation
```

之间仅凭同名/同标签关系：

> **不应该直接合并视觉簇。**

可以另外建立：

```text
ImplicitLogicalLink
```

---

# 15. Connector → Continuation 的隐式方向如何理解

根据标准的端口角色：

```text
Connector
= ConnectionPointIn
= 接收上游信号
```

而：

```text
Continuation
= ConnectionPointOut
= 从这里重新产生后续输出
```

因此从整体逻辑上可以理解成：

```text
上游
  │
  ▼
Connector C1
  ·
  ·  隐式连续关系
  ·
  ▼
Continuation C1
  │
  ▼
下游
```

即整体信号方向：

```text
上游
→ Connector
→ [隐式继续]
→ Continuation
→ 下游
```

但需要注意：

> `Connector → Continuation` 中间这一段是逻辑关系，不等价于一根用户可见的 Relation。

---

# 16. SFC 中“横杠”也不能当普通连接线

SFC 中有：

```text
SelectionDivergence
SelectionConvergence
SimultaneousDivergence
SimultaneousConvergence
```

这些在 UI 上经常表现为：

- 横线
- 双横线
- 分叉条
- 汇合条

但它们在 XML 中本身是：

```text
图形对象
```

而不是普通 Connection。

---

## 16.1 SelectionDivergence

标准结构：

```text
1 个 ConnectionPointIn
多个 ConnectionPointOut
```

因此：

```text
             ┌──→ 分支 1
上游 ──→ [D] ├──→ 分支 2
             └──→ 分支 3
```

方向：

```text
1 入 → 多出
```

---

## 16.2 SelectionConvergence

标准结构：

```text
多个 ConnectionPointIn
1 个 ConnectionPointOut
```

因此：

```text
分支1 ──┐
分支2 ──┼──→ [C] ──→ 下游
分支3 ──┘
```

方向：

```text
多入 → 1 出
```

---

## 16.3 SimultaneousDivergence

同样是：

```text
1 个 ConnectionPointIn
多个 ConnectionPointOut
```

方向：

```text
1 入 → 多出
```

---

## 16.4 SimultaneousConvergence

标准结构：

```text
多个 ConnectionPointIn
1 个 ConnectionPointOut
```

方向：

```text
多入 → 1 出
```

---

# 17. SFC `step` / `transition` 怎么看方向

标准的 `transition` 同时拥有：

```text
ConnectionPointIn
ConnectionPointOut
```

因此：

```text
前级 Step
   │
   ▼
Transition
   │
   ▼
后级 Step
```

`step` 同样属于具有连接端口的图形对象。

所以：

> `Step` 或 `Transition` 本身不是连接线。

它们是连接线两端的节点。

---

# 18. Jump / JumpStep：逻辑跳转不等于可见长线

这是另一类必须和“视觉簇”分离的结构。

旧 PLCopen XML 中：

```text
jump
```

具有：

```text
ConnectionPointIn
```

并通过：

```text
label
```

指定逻辑跳转目标。

`label` 本身是一个图形对象，但没有普通 ConnectionPoint。

因此可能出现：

```text
前级 ──→ Jump L1

        …… 没有一根连续长线 ……

Label L1
```

这和 Connector / Continuation 类似：

> **存在逻辑关系，不代表存在一根用户可见连续连接线。**

当前 IEC 61131-10 中 `Jump` 使用：

```text
targetNetworkLabel
```

表达目标网络标签。

所以视觉簇识别时：

```text
Jump → Target Label
```

不能因为逻辑跳转关系就当作普通可见边。

---

# 19. Free-floating line：标准甚至可能不导出

PLCopen XML v2.01 还有一个非常有用的说明：

> 没有任何连接的 free-floating lines，在图形语言中不会被导出。

也就是说，标准主要关心：

```text
有拓扑意义的图形连接
```

而不是任意绘图软件式的：

```text
装饰线
随手画的线
无连接线段
```

所以如果 BEH XML 能保存纯装饰线：

> 那很可能属于 BEH 自己的厂商扩展，而不是 PLCopen 标准核心连接模型。

---

# 20. “人可见的线”应该分成四类

这是后续程序最建议采用的分类。

| 类别 | 示例 | 是不是图结构 Edge | 是否用于视觉簇 |
|---|---|---:|---:|
| 显式连接线 | Connection、BEH relation 候选 | 是 | 是 |
| 图元本身的线状外观 | PowerRail、Contact、Coil、SFC 横杠 | 否，是 Node 的图形 | 作为图元参与，不把内部笔画当 Edge |
| 隐式逻辑连接 | Connector↔Continuation、Jump→Label | 否，单独 LogicalLink | 不直接合并视觉簇 |
| 装饰/自由线 | 厂商自定义 Drawing Line | 通常否 | 按需求决定，不能默认是业务连接 |

---

# 21. BEH `relation` 最合理的初始定位

由于 PLCopen / IEC 标准里没有通用标准元素：

```text
relation
```

所以对 BEH 应先采用：

```text
relation
= CandidateVisibleEdge
= “疑似可见显式关系线”
```

然后通过实验验证：

### 实验 A

删除画面上一根肉眼可见箭头。

如果 XML 中：

```text
一个 relation 消失
```

则：

```text
relation ≈ 显式可见连接
```

可信度大幅提高。

---

### 实验 B

只改变线路径，不改变两端。

如果：

```text
relation 的 position/path/point 改变
```

但端点引用保持不变：

说明 relation 同时携带：

```text
拓扑 + 几何
```

---

### 实验 C

保持 A、B 位置完全不动，只反转箭头方向。

比较：

```text
A → B
```

与：

```text
A ← B
```

看 relation 中：

- 哪些引用交换
- 哪个 port 角色改变
- 哪个 source/target 字段改变
- point 数组是否只是倒序

这个实验专门用于确认 BEH 的方向编码。

---

# 22. 箭头方向判定：推荐严格优先级

不要让弱 AI 自己“看着像”。

建议固定成下面的优先级。

---

## 优先级 1：ConnectionPointOut / ConnectionPointIn

如果两端角色明确：

```text
A.ConnectionPointOut
B.ConnectionPointIn
```

直接判断：

```text
A ─────────→ B
```

这是最可靠的语义依据。

---

## 优先级 2：Producer / Consumer

如果 XML 或 Java Model 明确标记：

```text
Producer
Consumer
Source
Sink
DataSource
DataSink
```

则：

```text
Producer / Source
        ↓
Consumer / Sink
```

---

## 优先级 3：标准 `connection` 的 `refLocalId`

如果 BEH 使用 PLCopen 风格：

```xml
<B>
    <connectionPointIn>
        <connection refLocalId="A"/>
    </connectionPointIn>
</B>
```

则：

```text
A ─────────→ B
```

因为：

```text
refLocalId = connection 的来源
owner = consumer
```

---

## 优先级 4：元素类型天然角色

有些元素只有一种端口角色。

可以直接使用：

```text
Continuation     = OUT
Connector        = IN

DataSource       = OUT
DataSink         = IN

旧 inVariable   = OUT
旧 outVariable  = IN

LeftPowerRail    = OUT
RightPowerRail   = IN

Jump             = IN
Return           = IN
```

---

## 优先级 5：端口级别

对于同时有 IN 和 OUT 的元素：

```text
Block
InOutVariable
Contact
Coil
Step
Transition
Divergence / Convergence
```

不能仅凭元素名字判断。

必须找到：

```text
这根 relation 具体接的是哪个 ConnectionPoint
```

---

## 最后才看：坐标和箭头几何形状

只有当所有语义证据都缺失时，才考虑：

```text
箭头三角形位置
start/end 坐标
point 顺序
左右关系
```

并且必须标记为：

```text
低可信 / 待实验验证
```

因为标准已经证明：

> **position 的 XML 顺序可能与信号方向相反。**

---

# 23. 不同元素的方向速查表

| 元素 | 标准连接角色 | 真实方向理解 | 能否单凭元素类型判方向 |
|---|---|---|---:|
| `Connection` | Producer ↔ Consumer 的显式连接 | OUT → IN | 是，结合两端 |
| `relation`（BEH） | 非标准名，待映射 | 不可直接猜 | 否 |
| `Connector` | ConnectionPointIn | 上游 → Connector | 是 |
| `Continuation` | ConnectionPointOut | Continuation → 下游 | 是 |
| `DataSource` | Source / OUT | DataSource → 后级 | 是 |
| `DataSink` | Sink / IN | 前级 → DataSink | 是 |
| `inVariable`（旧） | Producer / OUT | inVariable → 后级 | 是 |
| `outVariable`（旧） | Consumer / IN | 前级 → outVariable | 是 |
| `inOutVariable` | IN + OUT | 看具体端口 | 否 |
| Block Input | IN / Consumer | 前级 → Block | 是 |
| Block Output | OUT / Producer | Block → 后级 | 是 |
| Block InOut | IN + OUT | 看具体端口 | 否 |
| `leftPowerRail` | OUT | Rail → rung | 是 |
| `rightPowerRail` | IN | rung → Rail | 是 |
| `contact` | IN + OUT | IN → Contact → OUT | 需看端口 |
| `coil` | IN + OUT | IN → Coil → OUT | 需看端口 |
| `transition` | IN + OUT | IN → Transition → OUT | 需看端口 |
| `step` | IN + OUT（常规） | IN → Step → OUT | 需看端口 |
| SelectionDivergence | 1 IN + N OUT | 1 → N | 是 |
| SelectionConvergence | N IN + 1 OUT | N → 1 | 是 |
| SimultaneousDivergence | 1 IN + N OUT | 1 → N | 是 |
| SimultaneousConvergence | N IN + 1 OUT | N → 1 | 是 |
| `jump` | IN + 逻辑目标 | 前级 → Jump；之后逻辑跳转 | 局部可判 |
| `label`（旧） | 无普通 CP | Jump 逻辑目标 | 不是普通边 |
| `return` | IN | 前级 → Return | 是 |

---

# 24. 对 `continuation + relation` 的专门判定

这是当前最值得在 BEH 中验证的一条。

假设 XML 里有：

```text
Continuation C1
Relation R
Element B
```

如果 BEH 的 Continuation 语义遵循 PLCopen：

```text
Continuation = ConnectionPointOut
```

那么真实信号方向首先应假设：

```text
Continuation C1 ──R──→ Element B
```

前提是 B 这一端是：

```text
IN / Consumer
```

即使 XML 表面引用关系看起来是：

```text
B
└── relation ref="Continuation C1"
```

也不奇怪。

这和标准 connection 的存储模式完全一致：

```text
Consumer
└── 引用 Producer
```

但真实箭头仍然：

```text
Producer → Consumer
```

---

# 25. 对 `connector + relation` 的专门判定

如果：

```text
Element A
Relation R
Connector C1
```

Connector 按标准是：

```text
ConnectionPointIn
```

所以：

```text
Element A ──R──→ Connector C1
```

如果 XML 中 relation 挂在 Connector 下面并引用 A：

```text
Connector
└── relation/ref → A
```

也不要读成：

```text
Connector → A
```

正确解释仍然可能是：

```text
A → Connector
```

---

# 26. 如果两个元素都同时有 IN 和 OUT 怎么办

例如：

```text
Block A
Block B
```

二者都有：

```text
Input
Output
```

此时仅仅知道：

```text
relation(A, B)
```

还不够。

必须进一步恢复：

```text
Relation
├── A 的哪个 Port
└── B 的哪个 Port
```

例如：

```text
A.OUT1 ─────────→ B.IN3
```

才可以确定方向。

所以程序的数据结构不要只保存：

```text
sourceNode
targetNode
```

最好保存：

```text
sourceNode
sourcePort

targetNode
targetPort
```

---

# 27. 如果 XML 里的方向和 UI 箭头相反，先不要认为 BEH 出错

按标准经验，出现这种情况完全可能是因为：

## 情况 A：XML connection 写在 Consumer 下面

```text
XML owner = Target
ref = Source
```

于是表面看反。

---

## 情况 B：position 点序列是 Consumer → Producer

但信号方向是：

```text
Producer → Consumer
```

于是坐标数组看反。

---

## 情况 C：Continuation 本身是 OUT

如果只看 XML 层级，没有看端口角色，会把它错读成 IN。

---

## 情况 D：旧版 `inVariable` / `outVariable` 望文生义

实际是：

```text
inVariable = Producer
outVariable = Consumer
```

和中文直觉非常容易相反。

---

# 28. 给弱 AI 的固定判定算法

建议以后直接要求 AI 按下面顺序，不准跳步。

```text
STEP 1
识别 relation / connection 两端分别连接哪个元素

STEP 2
识别两端具体 Port / ConnectionPoint

STEP 3
给每个端口标记：
IN / OUT / UNKNOWN

STEP 4
如果：
一端 OUT
另一端 IN

则：
OUT → IN

STEP 5
如果一端是 Continuation：
优先标记 OUT

如果一端是 Connector：
优先标记 IN

STEP 6
如果一端是 DataSource / inVariable：
标记 OUT

如果一端是 DataSink / outVariable：
标记 IN

STEP 7
如果是 Block：
继续进入具体 InputVariable / OutputVariable / InOutVariable

STEP 8
如果仍然不能确定：
查看 refLocalId / source-target 语义

STEP 9
仍不能确定：
用 A→B / A←B 的最小差分实验验证

STEP 10
禁止只根据 position 顺序判断方向
```

---

# 29. 推荐程序内部建立三层关系，不要全部叫 Relation

为了避免后续 AI 混乱，建议内部数据模型分三类。

---

## 29.1 VisibleEdge

真正用户可见的连接线：

```text
VisibleEdge
- edge_id
- source_node
- source_port
- target_node
- target_port
- geometry
- xml_evidence
```

BEH 的：

```text
relation
```

如果实验确认它就是可见箭头，应映射到这里。

---

## 29.2 ImplicitLogicalLink

没有连续可见长线，但业务/控制逻辑存在连接：

```text
ImplicitLogicalLink
- Connector → Continuation
- Jump → Label
- 跨页引用
- 同名信号
```

这类关系：

> 不直接用于视觉簇合并。

---

## 29.3 GraphicalNode

本身视觉上可能包含大量线条，但其实是图元：

```text
PowerRail
Contact
Coil
Step
Transition
Divergence
Convergence
Connector
Continuation
```

不要把它们内部画出来的横线、竖线、框线拆成 Edge。

---

# 30. “视觉簇”最终应该使用什么

如果定义：

> 簇 = 用户在同一个画布上通过真实连续可见连接线能够走通的一组图元

那么最合理的是：

```text
Nodes
=
Block
Variable
Connector
Continuation
Contact
Coil
Step
Transition
...
```

加上：

```text
VisibleEdges
=
明确画出来的 Connection / BEH Relation
```

然后忽略方向做：

```text
Weakly Connected Components
```

得到视觉簇。

---

## 不应该用于视觉簇合并的关系

```text
Connector ↔ Continuation 的隐式对应
Jump → Label
跨页逻辑引用
同名变量
全局变量
其他不可见逻辑关系
```

这些应该在视觉簇生成之后，再建立：

```text
Cluster-to-Cluster Logical Link
```

---

# 31. BEH 当前最值得验证的四条假设

基于标准，可以把接下来的 BEH 实验缩小到四条。

## 假设 1

```text
relation
```

就是 BEH 的：

```text
显式用户可见连接边
```

---

## 假设 2

relation 的 XML 引用方向：

```text
Consumer → ref Producer
```

但 UI 箭头方向：

```text
Producer → Consumer
```

因此表面相反。

---

## 假设 3

```text
Continuation
```

是：

```text
OUT / Producer
```

所以：

```text
Continuation → 下游
```

---

## 假设 4

```text
Connector
```

是：

```text
IN / Consumer
```

所以：

```text
上游 → Connector
```

如果四条都被 01/02/03 和反向箭头实验验证，那么 BEH 的基本连接模型就已经非常接近被反推出了。

---

# 32. 最后的一句话规则

> **看到 XML 中一根线时，永远先问“两端谁是 OUT、谁是 IN”，而不是问“XML 从谁写到谁”。标准的真实数据方向是 Producer/ConnectionPointOut → Consumer/ConnectionPointIn；`connection` 可以存放在 Consumer 端，坐标点顺序也可能从 Consumer 开始，因此 XML 表面方向与用户看到的箭头方向相反是完全可能的。**

---

# 33. 标准版本边界

本文主要参考两个层级：

## PLCopen XML v2.01

优势：

- 官方完整 Technical Documentation 可公开查看
- 官方 XSD 可完整查看
- 对 `connection`、`refLocalId`、`position`、`connector`、`continuation` 的语义描述非常明确
- 非常适合用来理解旧版/厂商自定义 PLC XML 的设计思路

---

## IEC 61131-10:2019

PLCopen XML 在 2019 年进入 IEC 61131 系列成为：

```text
IEC 61131-10
PLC open XML exchange format
```

当前标准仍然明确具有：

```text
Connector
Continuation

DataSource
DataSink

LeftPowerRail
RightPowerRail
Coil
Contact

Step
Transition
SelectionDivergence
SelectionConvergence
SimultaneousDivergence
SimultaneousConvergence

ConnectionPointIn
Connection
FeedbackConnection
ConnectionPointOut
```

但 PLCopen 官方同时明确说明：

> IEC 61131-10:2019 是一次较大重构，与以前的 PLCopen XML 版本并不兼容。

因此：

> **不能拿 PLCopen v2.01 的标签名机械套 BEH；应该使用“Producer / Consumer、ConnectionPointOut / ConnectionPointIn、显式连接 / 隐式连接”的数据模型去映射 BEH 的真实字段。**

---

# 34. 官方参考依据

1. **PLCopen TC6 XML — XML Formats for IEC 61131-3, Version 2.01**
   - `connection`：Technical Documentation，约第 33 页
   - `continuation / connectionPointOut`：约第 34 页
   - graphical languages / free-floating lines：约第 38 页

2. **PLCopen XML Version 2.01 XSD Documentation**
   - `connector` / `continuation`
   - `inVariable` / `outVariable`
   - Block input/output/inOut variables
   - LD `leftPowerRail` / `rightPowerRail` / `coil` / `contact`
   - SFC divergence / convergence / transition
   - `jump` / `label`

3. **IEC 61131-10:2019 — PLC open XML exchange format**
   - §13.2 Common elements
     - Connector
     - Continuation
   - §13.3 FBD elements
     - Block
     - DataSource
     - DataSink
     - Jump
     - Return
   - §13.4 LD elements
   - §13.5 SFC elements
   - §13.6 Connections
     - ConnectionPointIn
     - Connection
     - FeedbackConnection
     - ConnectionPointOut

4. **PLCopen 官方 IEC 61131-10 Code Components**
   - IEC 61131-10 的机器可读 XML Schema / Code Components
   - 其中仍明确区分 consumer-side `ConnectionPointIn` 与 producer-side `ConnectionPointOut`
   - `refLocalId` 仍用于识别 connection 的来源元素

---

# 35. 给 BEH 分析任务的直接结论

后续分析 BEH XML 时，建议固定采用：

```text
relation
    ↓
先判断它是不是 VisibleEdge
    ↓
找到两个 endpoint
    ↓
找到 endpoint 对应元素
    ↓
找到 ConnectionPoint / Port 角色
    ↓
OUT → IN
    ↓
得到真实箭头方向
```

而不要采用：

```text
XML标签顺序
    ↓
谁引用谁
    ↓
position[0] → position[n]
    ↓
直接当箭头方向
```

后者在 PLCopen 标准模型下本身就存在方向看反的风险。
