# PLC / BEH 图元 XML 中的连接关系与“视觉连通簇”识别

## 一、核心结论

如果 BEH 图元工具参考了 PLCopen XML / IEC 61131-10 一类图形化 PLC 数据模型，那么：

> **图元之间是否“连接”，核心通常不是看坐标，而是看 XML 中的连接引用关系。**

在标准 PLCopen XML 中，最典型的连接链路是：

```text
connectionPointIn
    ↓
connection
    ↓
refLocalId
```

可以简单理解为：

```text
当前图元的某个输入端
    ↓
声明存在一条连接
    ↓
refLocalId 指向上游图元
```

因此，判断两个图元在逻辑图中是否由一条显式连接线相连，应该优先分析：

- `localId`
- `connectionPointIn`
- `connection`
- `refLocalId`
- `formalParameter`

而不是优先根据 `x / y / position` 判断。

---

# 二、PLCopen XML 中典型的连接表达

一个典型结构类似：

```xml
<block localId="7" typeName="MUX">
    <inputVariables>
        <variable formalParameter="K">
            <connectionPointIn>
                <connection
                    refLocalId="3"
                    formalParameter="OUT1"/>
            </connectionPointIn>
        </variable>
    </inputVariables>
</block>
```

可以理解为：

```text
图元 3.OUT1
      │
      ▼
图元 7.K
```

也就是：

> 图元 `3` 的 `OUT1` 输出端连接到图元 `7` 的 `K` 输入端。

---

# 三、几个关键字段分别表示什么

| XML 字段 / 元素 | 主要作用 |
|---|---|
| `localId` | 标识当前图元是谁 |
| `connectionPointIn` | 当前图元的输入连接点 |
| `connection` | 声明存在一条连接关系 |
| `refLocalId` | 指向连接来源的上游图元 |
| `formalParameter` | 指定具体输入 / 输出端口 |
| `position` | 描述图元或连线的几何位置 |
| `relPosition` | 描述端口相对图元的位置 |
| `connector` | 图形上的逻辑连接器 |
| `continuation` | 与 connector 配合实现逻辑延续 |

---

# 四、为什么 `refLocalId` 很重要

PLCopen XML 的一种典型表达方式是：

不是让上游图元说：

```text
“我连接到谁”
```

而是在下游输入端记录：

```text
“我的输入来自谁”
```

例如：

```xml
<block localId="20">
    <connectionPointIn>
        <connection refLocalId="10"/>
    </connectionPointIn>
</block>
```

解析后可以建立：

```text
10 ─────→ 20
```

因此：

```text
localId
```

解决的是：

> **这个图元是谁？**

而：

```text
refLocalId
```

解决的是：

> **这条连接来自哪个图元？**

---

# 五、`position` 不是主要连接依据

需要特别区分：

## 1. 拓扑连接

回答：

> 哪个图元连接到哪个图元？

主要依靠：

```text
connection
+
refLocalId
+
端口引用
```

---

## 2. 几何布局

回答：

> 这根线在画布上怎么画？

主要依靠：

```text
position
relPosition
折点
路径点
```

例如：

```xml
<connection refLocalId="3">
    <position x="320" y="72"/>
    <position x="312" y="72"/>
    <position x="312" y="40"/>
    <position x="272" y="40"/>
</connection>
```

可以理解为一根带折线的连接：

```text
A ─────┐
       │
       │
       └──── B
```

因此不要使用下面这种错误方法：

```text
两条线坐标相交
        ↓
认为两个图元连接
```

更可靠的做法应该是：

```text
connection + refLocalId
        ↓
确定拓扑关系

position / relPosition
        ↓
恢复视觉几何
```

---

# 六、与“视觉连通簇”的关系

这里定义：

> **视觉连通簇（Visual Connected Component）**  
> 是在同一个画布 / 页面内，通过显式连接线形成的最大连通图元集合。

例如 XML 解析后得到：

```text
1 ── 2 ── 3

4 ── 5

6
```

那么：

```text
Cluster 1 = {1, 2, 3}

Cluster 2 = {4, 5}

Cluster 3 = {6}
```

其中 `6` 是一个孤立图元，也可以视作单节点连通分量。

---

# 七、计算簇时为什么可以暂时忽略方向

PLC 控制图中的信号通常存在方向：

```text
A → B → C
```

但是识别“视觉上是否连成一片”时，只需要判断有没有连续连接路径。

因此计算视觉簇时，可以暂时视作：

```text
A — B — C
```

于是：

```text
A、B、C
```

属于同一个视觉连通簇。

图论上可以使用：

- Connected Components
- Weakly Connected Components
- DFS
- BFS
- Union-Find

进行计算。

---

# 八、Connector / Continuation 是一个重要特殊情况

PLC 图形工具为了避免画很长的连接线，经常会存在：

```text
connector
continuation
```

类似：

```text
[A]────▶ C1


                    C1 ────▶[B]
```

视觉上：

```text
A 所在区域
```

和：

```text
B 所在区域
```

之间没有连续可见的长线。

但逻辑上：

```text
C1
```

把它们关联起来。

因此应该区分两层。

---

## 第一层：视觉连通关系

```text
[A]──[B]──[Connector C1]
```

属于：

```text
Visual Cluster 1
```

而：

```text
[Continuation C1]──[C]──[D]
```

属于：

```text
Visual Cluster 2
```

---

## 第二层：隐式逻辑关系

进一步得到：

```text
Visual Cluster 1
        │
        │ Connector / Continuation C1
        ▼
Visual Cluster 2
```

因此：

> **逻辑上有关，不代表视觉上必须属于同一个簇。**

这点非常重要。

---

# 九、推荐的数据模型

建议将 BEH XML 解析结果至少拆成三类。

## 1. Node：图元

```text
Node
- node_id
- node_type
- name
- x
- y
- input_ports
- output_ports
- xml_location
```

---

## 2. VisibleEdge：显式视觉连接

```text
VisibleEdge
- source_node
- source_port
- target_node
- target_port
- wire_id
- route_points
- xml_location
```

它表示：

> 画布上真实存在的一条显式连接。

---

## 3. LogicalReference：隐式逻辑关系

```text
LogicalReference
- source
- target
- reference_type
- signal_name
- xml_location
```

例如：

- Connector / Continuation
- 相同变量
- 跨页引用
- 全局信号
- 输入输出映射
- 其他逻辑引用

这些关系不应该直接用于合并视觉簇。

---

# 十、如果 BEH 不是原生 PLCopen XML 怎么办

BEH 很可能是厂商或内部工具，并不一定原样使用 PLCopen XML 字段。

因此：

> **不要因为 XML 中没有 `localId` 或 `refLocalId` 就认为没有连接关系。**

实际字段可能被改成：

```text
id
uid
objectId
sourceId
targetId
from
to
src
dst
link
wire
edge
connection
portRef
nodeRef
```

等等。

真正应该寻找的是以下“角色”：

```text
节点唯一 ID
      +
源节点 / 目标节点引用
      +
输入 / 输出端口
      +
连接对象
      +
几何路径
```

也就是说，要寻找：

> **BEH XML 中，哪些字段分别等价于 PLCopen 的 `localId / refLocalId / connectionPointIn / formalParameter / position`。**

---

# 十一、分析真实 BEH XML 时的优先顺序

建议严格按下面顺序分析。

## 第一步：找到图元唯一 ID

确认：

```text
什么元素代表图元？
图元唯一编号是什么？
```

对应标准中的：

```text
localId
```

---

## 第二步：找到连接引用

确认：

```text
哪个字段表示：
当前图元和另外一个图元存在连接？
```

重点寻找类似：

```text
connection
source
target
from
to
ref
reference
link
wire
```

---

## 第三步：找到端口

确认：

```text
连接的是整个图元，
还是图元上的具体输入 / 输出端口？
```

寻找：

```text
input
output
port
pin
parameter
formalParameter
```

---

## 第四步：找到几何信息

确认：

```text
图元位置在哪里？
线经过哪些坐标？
是否有折点？
```

寻找：

```text
x
y
position
relPosition
point
route
path
```

---

## 第五步：找到隐式连接

单独寻找：

```text
connector
continuation
variable
signal
tag
reference
page reference
```

不要立即把它们加入视觉连通簇。

---

# 十二、最终建议的解析流程

```text
BEH XML
   │
   ▼
识别所有图元
Node
   │
   ▼
识别显式连接
VisibleEdge
   │
   ▼
建立图结构
Graph
   │
   ▼
计算视觉连通分量
Visual Connected Component
   │
   ▼
得到“簇”
   │
   ▼
再分析 Connector / 变量 / 跨页引用
LogicalReference
   │
   ▼
建立“簇与簇之间”的逻辑关系
```

---

# 十三、最需要防止的几个错误

## 错误 1：根据坐标距离判断连接

错误。

```text
[A][B]
```

距离再近，只要没有连接关系，也不能自动认为相连。

---

## 错误 2：根据线段视觉相交判断连接

错误。

两条线可能只是交叉，没有 Junction。

必须结合 XML 中真实连接定义判断。

---

## 错误 3：同一个变量名就合并视觉簇

错误。

相同变量可能代表隐式逻辑联系，但不代表画面上存在连续连接线。

---

## 错误 4：Connector / Continuation 直接合并视觉簇

如果两边之间没有实际连续可见线：

应该保留为两个视觉簇，再建立簇间逻辑关系。

---

## 错误 5：强行假定 BEH 一定完全符合 PLCopen

错误。

PLCopen 可以作为参考模型，但真实 BEH XML 才是最终事实来源。

---

# 十四、给弱 AI 的核心检查问题

拿到真实 BEH XML 后，首先让 AI 回答下面五个问题：

1. **哪个字段唯一标识一个图元？**
2. **哪个 XML 结构证明两个图元之间存在连接？**
3. **哪个字段指向连接的另一端图元？**
4. **如何识别输入端口和输出端口？**
5. **哪些字段只是控制坐标和绘制路径，而不是控制拓扑连接？**

然后进一步确认：

6. 是否存在 Connector / Continuation 一类非连续视觉连接？
7. 是否存在跨页面引用？
8. 是否存在同名变量形成的隐式逻辑关系？
9. 线交叉时如何区分“真正连接”和“仅仅交叉”？
10. 孤立图元如何表示？

---

# 十五、一句话记住

> **PLC / BEH 图元的“连接”首先看 ID 引用和 Connection 关系；坐标负责告诉软件“怎么画”，而不是主要告诉软件“谁和谁相连”。先由显式连接计算视觉连通簇，再单独建立 Connector、变量和跨页引用等簇间逻辑关系。**

---

## 参考规范

- PLCopen XML Exchange
- IEC 61131-10：PLCopen XML exchange format
- PLCopen XML Schema / Technical Documentation

如果 BEH 为内部或厂商自定义格式，应以真实 BEH XML 为最终事实依据，并将其字段映射到上述标准概念，而不是强行套用标准字段名。
