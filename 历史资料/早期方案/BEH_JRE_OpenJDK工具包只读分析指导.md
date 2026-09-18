# BEH 工具包（JRE / OpenJDK / Java）只读分析指导

## 一、任务目标

你现在需要分析一个基于 Java / OpenJDK 运行的 BEH 图元工具。

这个 BEH 工具会：

- 加载 XML 工程文件
- 在界面中显示 PLC / 电力图元
- 显示图元端口
- 显示图元之间的连接线
- 根据 XML 恢复图形布局和逻辑关系

本任务的目标不是修改 BEH，也不是破解授权，而是：

> **只读分析 BEH 工具包，找出它如何读取 XML、如何识别图元、如何建立连接关系、如何绘制连线。**

最终希望回答：

1. 哪个 JAR / 模块负责加载 XML？
2. 哪些 Java 类代表图元、端口、连接、网络或图？
3. BEH 从 XML 中读取哪些字段来建立连接？
4. 哪些字段只负责位置和绘制？
5. 是否存在 Net / Wire / Port / Connector 等中间对象？
6. 是否能够把这些结论和 `01.xml / 02.xml / 03.xml` 的差分结果互相验证？

---

# 二、总原则

## 1. 全程只读

不要：

- 修改 JAR
- 替换 CLASS
- 修改 XML 解析逻辑
- 注入代码
- 绕过授权
- 修改签名
- 修改运行环境
- 删除或覆盖原文件

如果需要产生分析结果：

> 复制到单独工作目录后分析。

---

## 2. 不要一开始反编译整个 BEH

大型 Java 工具可能包含：

```text
几十个
甚至几百个 JAR
```

如果一开始全部反编译：

- 噪音巨大
- 弱 AI 容易迷路
- 很难知道哪些类与 XML / 图元 / 连线有关

正确方法是：

```text
先找工具结构
↓
再找 XML 关键词
↓
再定位相关 JAR
↓
再定位相关 CLASS
↓
最后只分析少量关键类
```

---

## 3. 真实 BEH XML 是第一手线索

不要只搜索：

```text
connection
wire
edge
```

最优先搜索：

> **真实 XML 中出现的独特标签名、属性名、枚举值。**

例如真实 XML 中存在：

```xml
<GraphicObject ...>
<PinRelation ...>
<SomethingSpecial ...>
```

那么优先在 JAR / CLASS 中搜索：

```text
GraphicObject
PinRelation
SomethingSpecial
```

因为 BEH 既然能解析这些 XML，代码中通常会直接或间接出现这些字符串。

---

# 三、第一步：先识别 BEH 工具包目录结构

先只做目录调查。

不要分析代码。

记录 BEH 安装目录中是否存在：

```text
bin/
lib/
libs/
jre/
jdk/
runtime/
plugins/
plugin/
modules/
config/
conf/
resources/
app/
classes/
```

以及：

```text
*.jar
*.class
*.xml
*.properties
*.json
*.conf
*.ini
*.bat
*.cmd
*.sh
*.exe
```

输出类似：

```text
BEH/
├── bin/
├── jre/
├── lib/
│   ├── xxx.jar
│   ├── yyy.jar
│   └── zzz.jar
├── plugins/
├── config/
└── beh.exe
```

---

# 四、第二步：确认它使用的 Java / OpenJDK

重点确认：

```text
java.exe
java
javac
jar
javap
jdeps
jps
jcmd
jstack
```

是否存在。

如果 BEH 自带：

```text
jre/
```

或：

```text
runtime/
```

优先使用 BEH 自己携带的 Java 工具判断版本。

例如：

```bash
java -version
```

记录：

```text
Java 版本
OpenJDK 版本
Vendor
Runtime
VM
Architecture
```

例如可能看到：

```text
OpenJDK Runtime Environment
OpenJDK 64-Bit Server VM
```

注意：

> 不要因为系统也装了 Java，就默认 BEH 使用系统 Java。

需要确认 BEH 实际启动时使用的是：

```text
系统 Java
```

还是：

```text
BEH 自带 JRE / OpenJDK
```

---

# 五、第三步：确认 BEH 是怎么启动的

检查：

```text
*.bat
*.cmd
*.sh
启动配置文件
launcher 配置
```

寻找类似：

```text
java -jar xxx.jar
```

或者：

```text
-classpath
-cp
```

或者：

```text
-Xmx
-Dxxx=xxx
```

或者：

```text
mainClass
main.class
```

目标是回答：

```text
BEH 主入口是什么？
```

例如：

```text
Main JAR = beh-client.jar
Main Class = xxx.yyy.MainApplication
Classpath = lib/*
```

如果 BEH 由 EXE 启动，也要查看：

> EXE 是否只是 Java Launcher。

不要修改 EXE。

---

# 六、第四步：列出所有 JAR

使用 JDK 自带：

```bash
jar tf xxx.jar
```

查看 JAR 内容。

不要先解压全部 JAR。

先建立 JAR 清单，例如：

```text
beh-core.jar
beh-ui.jar
beh-model.jar
beh-xml.jar
graph.jar
plugin-xxx.jar
```

根据名称初步分类：

```text
UI
XML
Model
Graph
Editor
Plugin
Runtime
Utility
Third-party
```

但：

> 文件名只能作为线索，不能直接下结论。

---

# 七、第五步：优先寻找真实 XML 关键词

从：

```text
01.xml
02.xml
03.xml
```

中挑选 5～20 个有辨识度的：

- 标签名
- 属性名
- 枚举值
- 图元类型名
- 特殊常量

例如：

```text
<Comp>
<Pin>
<Relation>
type="XXX"
kind="YYY"
```

然后在 BEH 工具包中搜索这些字符串。

优先搜索：

```text
.jar
.class
.properties
.xml
配置文件
```

目标是定位：

> 哪个 JAR 知道这些 XML 字段。

输出类似：

```text
关键词：PinRelation

命中：
beh-model.jar
beh-xml.jar

疑似相关类：
com.xxx.xml.PinRelationReader
com.xxx.model.Connection
```

---

# 八、第六步：使用 `javap` 查看 CLASS 结构

如果已经定位到某个 class：

不要急着做完整反编译。

优先使用：

```bash
javap
```

查看：

- 类名
- 方法名
- 字段名
- 参数类型
- 返回类型
- 继承关系

例如：

```bash
javap -classpath xxx.jar -p com.xxx.ConnectionReader
```

必要时：

```bash
javap -classpath xxx.jar -p -c com.xxx.ConnectionReader
```

其中：

```text
-p
```

用于显示 private 成员。

```text
-c
```

用于查看 JVM 字节码指令。

本阶段重点寻找方法名，例如：

```text
load
read
parse
deserialize
unmarshal

createConnection
connect
addEdge
addLink
addWire

getSource
getTarget
getPort

draw
paint
render
route
```

---

# 九、第七步：重点寻找 XML 解析链

目标是找到类似：

```text
XML 文件
↓
XML Reader / Parser
↓
Java Model
↓
Graph Model
```

可能出现的技术包括：

```text
DOM
SAX
StAX
JAXB
Jackson XML
XStream
JDOM
dom4j
Spring XML
自定义 Parser
```

重点观察类名和方法：

```text
XmlParser
XmlReader
XMLLoader
Document
Element
Node
Attribute
Unmarshaller
deserialize
parse
```

以及代码是否读取：

```text
getAttribute(...)
getElementsByTagName(...)
attributeValue(...)
```

---

# 十、最重要的追踪方法：从 XML 字段反查代码

假设真实 XML 有：

```xml
<Something sourceId="123" targetId="456"/>
```

不要直接认为：

```text
sourceId / targetId
```

就是连接。

应该去 Java 中搜索：

```text
sourceId
targetId
```

然后追踪：

```text
谁读取 sourceId
↓
读取后保存到哪个 Java 字段
↓
这个字段被哪个方法使用
↓
是否最终创建 Edge / Connection / Wire
```

理想情况下得到：

```text
XML:
sourceId
↓
SomethingReader
↓
ConnectionModel.source
↓
Graph.addEdge(...)
↓
UI ConnectionFigure
```

这才是强证据。

---

# 十一、第八步：寻找图元类

重点搜索：

```text
Block
Node
Component
Element
Graphic
Figure
Symbol
FunctionBlock
Device
Object
```

目标是找到：

> BEH 内部用什么 Java 对象表示一个图元。

记录：

```text
Class:
ID字段:
类型字段:
坐标字段:
输入端口:
输出端口:
父对象:
```

---

# 十二、第九步：寻找端口类

重点搜索：

```text
Port
Pin
Terminal
Input
Output
InPort
OutPort
Connector
Socket
Anchor
```

回答：

```text
图元是否拥有 Port？
Port 是否有自己的 ID？
Port 是否保存 parent node？
Port 是否保存连接列表？
Port 是否保存坐标？
```

这一步很重要。

因为 BEH 可能不是：

```text
图元A → 图元B
```

而是：

```text
A.outPort → B.inPort
```

---

# 十三、第十步：寻找连接 / 网络类

重点搜索：

```text
Connection
Wire
Edge
Link
Net
Network
Relation
Branch
Segment
Route
Line
Flow
Signal
```

特别检查三种模型。

---

## 模型 A：直接连接

```text
Node A
   ↓
Connection
   ↓
Node B
```

---

## 模型 B：端口连接

```text
Node A
   ↓
Port A1
   ↓
Connection
   ↓
Port B1
   ↓
Node B
```

---

## 模型 C：共享 Net

```text
Node A.Port
      ↓
    Net 17
      ↑
Node B.Port
```

如果是模型 C：

> A 和 B 可能不会直接引用对方。

---

# 十四、第十一步：寻找绘图类

如果已经找到：

```text
Connection
Wire
Edge
```

继续寻找：

```text
paint
draw
render
Polyline
Line
Figure
Shape
Graphics
Graphics2D
Path
Route
Router
```

如果是 Swing，可能出现：

```text
java.awt.Graphics
java.awt.Graphics2D
paint
paintComponent
drawLine
draw
```

如果是 JavaFX，可能出现：

```text
javafx.scene
Line
Polyline
Path
Node
Canvas
GraphicsContext
```

也可能使用第三方图形框架。

这一步需要回答：

> **画一根线时，Java 对象从哪里拿到两端位置？**

---

# 十五、第十二步：使用 `jdeps` 看模块依赖

如果 JDK 中存在：

```bash
jdeps
```

可以用于查看某个 JAR 依赖哪些 Java 模块或其他包。

例如：

```bash
jdeps xxx.jar
```

或者：

```bash
jdeps -verbose:class xxx.jar
```

目标不是全面分析所有依赖。

主要用于判断：

```text
某个 JAR 是否依赖 XML 库
某个 JAR 是否依赖 UI / 图形库
某个 JAR 是否依赖 Graph / Model 模块
```

---

# 十六、运行态分析：仅在静态分析不足时使用

如果只看文件还无法确定：

可以在 BEH 正常运行时做只读观察。

不要注入代码。

---

## 1. `jps`

如果可用：

```bash
jps -lv
```

用于确认：

```text
BEH 对应哪个 Java 进程
Main Class
JVM 参数
```

---

## 2. `jcmd`

先：

```bash
jcmd
```

查看 Java 进程。

然后可针对 BEH 进程查看：

```bash
jcmd <PID> VM.command_line
```

或：

```bash
jcmd <PID> VM.system_properties
```

或者：

```bash
jcmd <PID> VM.flags
```

重点用于确认：

```text
实际启动命令
classpath
系统属性
JVM 配置
```

不要执行会改变程序状态的危险命令。

---

## 3. `jstack`

必要时：

```bash
jstack <PID>
```

只读查看线程堆栈。

最佳使用方式：

1. BEH 正常打开
2. 执行一次“加载 XML”
3. 或打开某个图形页面
4. 在相关操作期间抓线程栈

观察是否出现：

```text
XmlReader
XMLLoader
DiagramLoader
GraphBuilder
ConnectionLoader
```

等类。

注意：

> 线程栈只是一条线索，不一定每次都能抓到短暂调用。

---

# 十七、不要一开始使用过重的方法

暂时不要：

- 大规模反编译全部 JAR
- 修改 JVM
- 注入 Agent
- 改 CLASS
- Hook 程序
- 改启动参数尝试绕过保护
- 修改许可证
- 修改签名
- 修改 BEH 原目录内容

优先使用：

```text
目录
↓
JAR 清单
↓
字符串
↓
javap
↓
关键类
↓
运行态只读验证
```

---

# 十八、与 01 / 02 / 03 XML 差分结合

静态 Java 分析不能单独下结论。

必须与三个实验文件结合。

---

## 实验 1

```text
01.xml

[A]        [B]
```

无连接。

---

## 实验 2

```text
02.xml

[A]────────[B]
```

只增加一根连接。

---

## 实验 3

```text
03.xml

[A]────────────────────[B]
```

连接不变，只移动 B。

---

Java 代码和 XML 差分应互相验证。

例如：

```text
XML 差分发现：
01 → 02 新增 field X

Java 中发现：
XMLLoader 读取 field X
↓
ConnectionModel
↓
Graph.addEdge
```

则：

> field X 是连接相关字段的证据很强。

---

如果：

```text
02 → 03 field Y 变化
```

Java 中：

```text
field Y
↓
setPosition
↓
route
↓
drawLine
```

则：

> field Y 更可能是几何绘制字段。

---

# 十九、最终需要建立的完整链路

最终希望得到：

```text
01 / 02 / 03 XML
        │
        ▼
XML 标签 / 属性
        │
        ▼
XML Parser / Reader
        │
        ▼
Java Model
        │
        ├── Node / Block
        ├── Port / Pin
        ├── Connection / Wire
        └── Net / Network
        │
        ▼
Graph / Diagram Model
        │
        ▼
UI Figure / Shape
        │
        ▼
用户看到的图元和连线
```

---

# 二十、证据强度分级

所有结论分成三档。

## 高可信

同时满足：

```text
XML 差分
+
Java 代码读取
+
内部对象使用
```

例如：

```text
01无
02出现
03保持

Java读取该字段
↓
创建Connection
```

---

## 中可信

只有：

```text
XML 差分
+
Java 中出现相关字段
```

但还没追到最终连接对象。

---

## 低可信

只有：

```text
字段名称像 Connection
```

或者：

```text
类名像 Wire
```

但没有实际数据流证据。

禁止把低可信结论写成事实。

---

# 二十一、最终输出格式

## 1. Java / OpenJDK 环境

```text
Java Version:
JRE/JDK Path:
BEH 使用的 Java:
Main JAR:
Main Class:
Classpath:
```

---

## 2. BEH JAR 结构

```text
JAR 1:
作用：

JAR 2:
作用：
```

只列与本任务相关的 JAR。

---

## 3. XML 解析入口

```text
Class:
Method:
输入:
输出:
证据:
```

---

## 4. 图元数据模型

```text
Node Class:
ID:
Type:
Position:
Ports:
```

---

## 5. 连接数据模型

```text
Connection Class:
Source:
Target:
Port:
Net:
Wire:
```

---

## 6. 绘图模型

```text
Figure / Shape Class:
位置来源:
线路径来源:
```

---

## 7. XML → Java → UI 映射

例如：

```text
XML field X
↓
XmlReader.readX()
↓
Connection.source
↓
Graph.addEdge()
↓
ConnectionFigure
```

---

## 8. 与 01 / 02 / 03 的交叉验证

明确写：

```text
01 → 02：
发现……

02 → 03：
发现……

Java 代码验证：
……
```

---

## 9. 当前最可能的连接机制

在以下选项中选择：

```text
A. Node ID → Node ID

B. Port ID → Port ID

C. Node / Port → Net / Wire → Node / Port

D. 主要通过几何坐标匹配

E. 多种机制组合

F. UNKNOWN
```

必须给证据。

---

## 10. 未解决问题

所有不确定项列出：

```text
UNKNOWN 1:
原因:
下一步最小验证方法:
```

---

# 二十二、最重要的一句话

> **不要把 BEH 当成一个黑盒去猜 XML，也不要把整个 Java 工具包一次性反编译。先用 01/02/03 找到“可疑 XML 字段”，再从这些真实字段反查 JAR / CLASS，沿着“XML → Java Model → Connection / Port / Net → UI 绘图”逐层追踪，最终用两边证据互相验证。**
