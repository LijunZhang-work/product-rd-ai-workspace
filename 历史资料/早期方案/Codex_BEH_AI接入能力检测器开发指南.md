# Codex 指南：开发 BEH 原生工具“AI 可接入能力检测器”
## 目标：先体检 BEH.exe，再决定 AI 到底能接入到什么程度

> **给 Codex 的任务说明**
>
> 你现在不要开发 BEH 自动写图元功能，也不要继续猜 XML。
>
> 先开发一个 **BEH Automation Capability Detector（BEH 自动化能力检测器）**。
>
> 这个工具的唯一目的：
>
> **检测一个正在运行的 BEH.exe，到底暴露了多少可供 AI / 自动化程序访问和控制的能力。**
>
> 最终输出一份清晰报告，回答：
>
> 1. BEH 是否真的是 Java/OpenJDK 程序？
> 2. BEH 实际使用哪个 JRE/JDK？
> 3. Java Access Bridge 能不能看到 BEH？
> 4. Windows UI Automation 能不能看到 BEH？
> 5. 菜单、工具栏、项目树、图元库、属性面板分别能看到多少？
> 6. 中央图形画布是不是“黑盒”？
> 7. 能不能识别画布内部的图元、端口、文字、连线？
> 8. 能不能结构化执行 click/invoke/set-value/select？
> 9. 如果结构化操作不行，鼠标/键盘坐标操作能不能作为兜底？
> 10. 最终 BEH 属于 5星、4星、3星、1星还是0星自动化能力？
>
> 本轮不做正式写图元，只做能力检测。

---

# 一、为什么现在先做这个

我们的长期目标是：

```text
人自然语言
   +
人拖画图元
   ↓
AI理解
   ↓
AI修改/补充图元
   ↓
尽可能让原生 BEH 自己执行创建、连接、参数设置、保存
   ↓
BEH 自己生成 XML、隐藏字段、内部 ID、附属代码
```

这样比我们自己直接拼 BEH XML 更安全。

但是在设计 BEH Driver 之前，必须先知道：

```text
BEH 到底给不给外部程序“看”和“操作”
```

所以这次做的是：

```text
BEH.exe
   ↓
自动体检
   ↓
Capability Report
   ↓
决定后续技术路线
```

---

# 二、安全边界：本轮只能“检测”，不能“改工程”

## 默认只读

禁止自动执行：

- 删除图元
- 修改工程
- 保存工程
- 覆盖 XML
- 修改 JAR
- 修改 CLASS
- 修改 BEH 配置
- 修改授权
- Hook / 注入 BEH
- 修改 JRE/JDK
- 安装 Java Agent
- 反编译后修改代码

允许：

- 枚举进程
- 获取窗口句柄
- 查看命令行
- 查看安装目录
- 查看 JRE/JDK 版本
- 查看 JAR 文件名
- 查看 accessibility tree
- 查看 UI Automation tree
- 截图
- 查询控件属性
- 读取控件文本
- 查看焦点元素
- 记录边界矩形
- 调用无副作用的结构查询

## 如需“交互测试”

只允许使用明确无破坏性的控件，例如：

```text
Help → About
切换一个不会修改工程的 tab
选择项目树中的已有节点
展开/折叠树节点
聚焦搜索框
```

不要自动点击：

```text
Save
Delete
Apply
OK（如果会修改数据）
Generate
Compile
Download
Write
```

如果无法确认某动作是否无副作用：

```text
SKIP
```

---

# 三、最终要输出哪些文件

工具至少生成：

```text
output/
├── beh_capability_report.json
├── beh_capability_report.html
├── process_report.json
├── java_report.json
├── uia_tree.json
├── jab_tree.json
├── window_screenshot.png
└── logs/
```

其中最重要的是：

```text
beh_capability_report.json
```

和：

```text
beh_capability_report.html
```

---

# 四、总检测流程

```text
启动 BEH
   ↓
阶段 A：进程 / 运行时识别
   ↓
阶段 B：Java/OpenJDK 能力识别
   ↓
阶段 C：Windows UI Automation 检测
   ↓
阶段 D：Java Access Bridge 检测
   ↓
阶段 E：区域能力检测
   ↓
阶段 F：画布黑盒程度检测
   ↓
阶段 G：安全交互检测
   ↓
阶段 H：评分
   ↓
最终报告
```

---

# 五、阶段 A：确认 BEH 到底是什么程序

## A1. 找到 BEH 进程

工具允许用户提供：

```text
--process-name beh.exe
```

也允许自动枚举窗口标题。

记录：

```text
PID
exe_path
window_title
main_hwnd
process_architecture
start_time
```

## A2. 获取进程命令行

Windows 可通过 WMI/CIM 获取。

例如 PowerShell：

```powershell
Get-CimInstance Win32_Process |
Where-Object { $_.Name -eq "beh.exe" } |
Select-Object ProcessId, ExecutablePath, CommandLine
```

重点寻找：

```text
java.exe
javaw.exe
-jar
-classpath
-cp
-D...
-Xmx...
```

## A3. 扫描 BEH 安装目录

只读扫描：

```text
jre/
jdk/
runtime/
bin/
lib/
libs/
plugins/
modules/
*.jar
java.exe
javaw.exe
jvm.dll
```

生成：

```json
{
  "embedded_java_found": true,
  "java_candidates": [],
  "jar_count": 0,
  "jar_candidates": []
}
```

---

# 六、阶段 B：确认实际 Java / JVM 情况

## B1. 检测 Java 进程

优先尝试：

```text
jcmd -l
```

以及：

```text
jps -lv
```

如果 BEH 自带 JDK：

优先使用 BEH 自带 JDK 中的：

```text
jcmd.exe
jps.exe
```

不要默认使用系统 Java。

## B2. 记录 JVM 信息

如果能够通过 `jcmd` 找到 BEH JVM：

记录：

```text
JVM PID
Main Class
Command Line
Java Home
Java Version
VM Name
VM Vendor
VM Arguments
Classpath（如果可得）
```

可使用只读命令，例如：

```text
jcmd <PID> VM.command_line
jcmd <PID> VM.system_properties
jcmd <PID> VM.flags
```

## B3. 判断 BEH.exe 是否只是 Java Launcher

最终报告给出：

```text
JAVA_NATIVE_APP
JAVA_LAUNCHED_BY_EXE
NATIVE_APP_WITH_EMBEDDED_JVM
UNKNOWN
```

不要只根据文件名判断。

---

# 七、阶段 C：Windows UI Automation（UIA）检测

Windows UI Automation 的目标：

> 看 Windows 从外部到底能看到 BEH 的多少 UI。

Microsoft UI Automation 将桌面应用暴露为树结构：

```text
Desktop
└── BEH Window
    ├── Menu
    ├── Toolbar
    ├── Tree
    ├── Buttons
    ├── Panels
    └── ...
```

## C1. 优先检测 `winapp ui`

先检测：

```text
winapp --help
```

如果存在：

使用：

```text
winapp ui inspect
```

对 BEH 窗口导出 accessibility tree。

注意：

`winapp CLI` 当前属于微软公开预览工具。

因此：

> 它是非常好的检测辅助工具，但不要把整个最终项目永久绑死在它上面。

## C2. 如果没有 winapp

不要强制安装。

可以选择：

### 方案 A

使用 Windows SDK：

```text
Inspect.exe
```

人工验证 UIA。

### 方案 B

Codex 实现一个小型 UIA Probe：

```text
uia_probe.exe
```

建议使用：

```text
C# + UIAutomation
```

或者：

```text
C++ + IUIAutomation COM API
```

## C3. UIA Probe 要采集什么

对 BEH 主窗口遍历：

```text
Control View
Content View
必要时 Raw View
```

每个元素记录：

```json
{
  "name": "",
  "automation_id": "",
  "control_type": "",
  "class_name": "",
  "framework_id": "",
  "is_enabled": true,
  "is_offscreen": false,
  "bounding_rectangle": {},
  "patterns": [],
  "children": []
}
```

重点 patterns：

```text
Invoke
Selection
SelectionItem
Value
Text
ExpandCollapse
Toggle
Scroll
Transform
LegacyIAccessible
```

---

# 八、阶段 D：Java Access Bridge（JAB）检测

这个阶段非常重要，因为 BEH 已知很可能使用 OpenJDK / Java。

Oracle 的 Java Access Bridge 可以让 Windows 外部程序访问支持 Java Accessibility API 的 Java GUI。

JDK 中通常提供：

```text
jabswitch
jaccesswalker
jaccessinspector
```

## D1. 查找 JAB 工具

扫描：

```text
<JAVA_HOME>\bin\
```

查：

```text
jabswitch.exe
jaccesswalker.exe
jaccessinspector.exe
```

报告：

```json
{
  "jaccesswalker_found": true,
  "jaccessinspector_found": true,
  "jabswitch_found": true
}
```

## D2. 不要自动启用 Java Access Bridge

如果发现 JAB 当前没有启用：

只报告：

```text
JAB_AVAILABLE_BUT_NOT_ENABLED
```

不要偷偷执行：

```text
jabswitch -enable
```

因为这是环境修改。

报告中告诉用户：

> 可以由用户明确允许后再启用测试。

## D3. 第一种验证：jaccesswalker / jaccessinspector

如果 JAB 已启用：

启动：

```text
jaccesswalker
```

观察是否能够看到：

```text
BEH Main Window
├── MenuBar
├── ToolBar
├── Project Tree
├── Component Palette
├── Property Panel
└── Diagram Canvas
```

`jaccesswalker` 用于查看 Java GUI 的 accessibility component hierarchy。

`jaccessinspector` 用于检查当前 Java accessible object 的详细信息。

## D4. 更推荐：实现自己的 JAB Probe

Codex 可以开发：

```text
jab_probe.exe
```

只读调用 Oracle Java Access Bridge Native API。

核心 API 包括：

```text
initializeAccessBridge()

IsJavaWindow(HWND)

GetAccessibleContextFromHWND(...)

GetAccessibleContextInfo(...)

GetAccessibleChildFromContext(...)

GetAccessibleParentFromContext(...)

shutdownAccessBridge()
```

目标：

```text
HWND
 ↓
IsJavaWindow
 ↓
AccessibleContext Root
 ↓
递归遍历 Java Component Tree
 ↓
jab_tree.json
```

## D5. JAB Probe 记录字段

至少：

```json
{
  "name": "",
  "description": "",
  "role": "",
  "states": "",
  "index_in_parent": 0,
  "children_count": 0,
  "x": 0,
  "y": 0,
  "width": 0,
  "height": 0,
  "accessible_text": false,
  "accessible_action": false,
  "accessible_selection": false,
  "children": []
}
```

---

# 九、阶段 E：按 BEH 区域评估能力

不要只输出：

```text
UIA works
JAB works
```

必须按“产品区域”评估。

## E1. 主菜单

检测：

```text
File
Edit
View
Project
Help
...
```

评分：

```text
VISIBLE
READABLE
INVOKABLE
NOT_EXPOSED
UNKNOWN
```

## E2. 工具栏

检测：

```text
按钮名称
tooltip
automation id
Java accessible name
invoke capability
```

## E3. 项目树

检测：

```text
是否识别 Tree
是否识别每个 TreeItem
是否能读 item text
是否能 Expand/Collapse
是否能 Select
```

## E4. 图元库 / Palette

这是后续 AI 创建图元最重要的区域之一。

检测：

```text
能不能找到 TON / AND / OR / relation 等图元入口
能不能获得图元名称
能不能选择
能不能拖拽
```

## E5. 属性面板

检测：

```text
Parameter Name
Parameter Value
TextBox
ComboBox
CheckBox
Table
```

以及：

```text
能不能 read
能不能 set value
```

本轮只检测能力，不真正修改工程。

## E6. 中央 Diagram Canvas

这是最关键的一项。

需要判断：

### Case 1：最好情况

JAB / UIA 能看到：

```text
Canvas
├── Block A
├── Block B
├── Relation R1
├── Continuation C1
└── ...
```

说明：

```text
STRUCTURED_CANVAS
```

### Case 2：中等情况

只能看到：

```text
Canvas
```

但能够拿到 Canvas 的：

```text
x
y
width
height
```

内部图元全看不到。

说明：

```text
BLACKBOX_CANVAS_WITH_GEOMETRY
```

以后可能：

```text
结构化控制外围 UI
+
坐标/视觉操作 Canvas
```

### Case 3：更差情况

连 Canvas 都无法稳定识别，只能看到整个窗口。

说明：

```text
FULL_BLACKBOX
```

---

# 十、阶段 F：专门做“画布黑盒程度测试”

这一阶段非常重要。

不要修改工程。

## F1. 使用现有工程

让用户打开一个已经存在的简单 BEH 工程。

例如里面有：

```text
Block A
Block B
Relation
Continuation
```

## F2. 比较三份证据

同时拿：

```text
BEH Screenshot
UIA Tree
JAB Tree
```

然后建立对照：

| 人眼看到 | UIA看到 | JAB看到 |
|---|---|---|
| Block A | ? | ? |
| Block B | ? | ? |
| Relation | ? | ? |
| Continuation | ? | ? |
| Canvas | ? | ? |

## F3. 输出 Canvas Visibility Score

例如：

```text
canvas_visible_to_uia = 0%
canvas_visible_to_jab = 70%
```

不需要第一次就做到非常精确。

可以先基于：

```text
已知人眼对象数量
vs
自动化树可识别对象数量
```

计算粗略覆盖率。

---

# 十一、阶段 G：安全交互能力测试

只有用户明确允许：

```text
--safe-interaction-test
```

才执行。

## G1. 测试结构化 Invoke

例如：

```text
Help → About
```

如果成功：

```text
structured_invoke = true
```

然后关闭 About。

## G2. 测试 Selection

例如：

选择项目树中一个已有 page。

验证：

```text
selection_before
selection_after
```

不修改工程。

## G3. 测试 ExpandCollapse

展开 / 折叠树节点。

## G4. 测试 Value Pattern

只在存在一个明确不会修改工程的文本控件时测试。

否则：

```text
SKIP
```

## G5. 测试鼠标坐标兜底

如果 UIA/JAB 无法 invoke，但能得到 Bounding Rectangle：

可以在安全控件上：

```text
center point click
```

记录：

```text
coordinate_fallback_possible = true
```

这一步只能用于安全控件。

---

# 十二、不要只测“能不能点”，还要测“稳定不稳定”

AI最终不能依赖一个每次都变化的控件树。

所以需要做：

```text
Snapshot 1
Snapshot 2
Snapshot 3
```

至少重复三次：

```text
关闭/打开一个非破坏性 panel
切换 page
改变窗口大小
```

观察：

```text
AutomationId 是否稳定
Accessible Name 是否稳定
Tree Path 是否稳定
Class Name 是否稳定
Bounding Rectangle 是否按预期变化
```

输出：

```text
selector_stability
```

例如：

```text
HIGH
MEDIUM
LOW
```

---

# 十三、最终评分：BEH AI 接入等级

最终一定要输出一个明确等级。

## ★★★★★ Level 5：原生结构化自动化非常好

条件大致：

```text
菜单可见
工具栏可见
项目树可见
图元库可见
属性面板可见
Canvas 内部图元/端口也可见
支持结构化操作
选择器稳定
```

结论：

> 可以优先做真正的 BEH Driver，让 AI 高可靠操作原生 BEH。

## ★★★★ Level 4：外围全结构化，Canvas 部分受限

例如：

```text
菜单 √
工具箱 √
属性 √
项目树 √

Canvas：
只能看到部分对象
或者只能看到 Canvas 容器
```

结论：

```text
JAB/UIA
+
坐标/XML几何
+
视觉确认
```

可以做很有价值的 BEH Driver。

## ★★★ Level 3：Canvas 黑盒，但位置稳定

例如：

```text
菜单/工具栏部分可见
Canvas只能拿到矩形
图元无法结构化读取
```

结论：

> 仍可做混合自动化，但要大量依赖我们的 XML Parser、坐标、截图确认。

## ★ Level 1：几乎纯像素自动化

例如：

```text
只能看到主窗口
几乎没有内部控件
Canvas完全黑盒
```

只能：

```text
截图
鼠标
键盘
坐标
```

结论：

> 可以做辅助 Demo，不适合作为高可靠自动生成 BEH 工程的主路线。

## ☆ Level 0：不建议原生自动化

例如：

```text
UIA无有效信息
JAB无有效信息
窗口/控件不稳定
无法安全定位
鼠标操作高度不确定
```

结论：

> 放弃把“操作原生 BEH”作为主写入路径。

后续优先：

```text
BEH Template + Patch Writer
```

或：

```text
AI设计 → 人在BEH中最终落地
```

---

# 十四、评分不要只给一个总分

必须分别评分：

```json
{
  "process_visibility": 5,
  "java_visibility": 5,
  "uia_visibility": 4,
  "jab_visibility": 5,
  "menu_automation": 5,
  "project_tree_automation": 5,
  "palette_automation": 4,
  "property_panel_automation": 5,
  "canvas_visibility": 2,
  "canvas_interaction": 2,
  "selector_stability": 4,
  "overall_level": 4
}
```

这样以后我们知道：

> 到底卡在哪里。

---

# 十五、最终 HTML 报告应该让小白也看得懂

不要只给日志。

`beh_capability_report.html` 顶部直接显示：

```text
BEH AI 接入检测结果

总体：★★★★ 4级

结论：
BEH 很适合做“混合型 AI Driver”。

AI可以可靠控制：
✓ 菜单
✓ 工具栏
✓ 项目树
✓ 属性面板

AI目前看不到：
✗ Canvas 内部图元
✗ Relation

推荐路线：
Java Access Bridge + Windows UIA
+
XML坐标辅助
+
Canvas视觉验证
```

然后下面才放专业数据。

---

# 十六、最好做一个 UI 覆盖可视化

非常推荐。

拿 BEH 窗口截图：

```text
window_screenshot.png
```

然后把 UIA / JAB 识别到的 Bounding Rectangle 画到截图上。

例如：

```text
绿色框 = UIA识别
黄色框 = JAB识别
红色区域 = 两者都看不到
```

生成：

```text
automation_overlay.png
```

这样用户一眼就能看到：

> AI 到底“看得见” BEH 的哪些地方。

---

# 十七、建议的技术实现

第一版不要做复杂 UI。

推荐：

```text
Python / C# Orchestrator
        │
        ├── process_probe
        ├── java_probe
        ├── uia_probe
        ├── jab_probe
        ├── screenshot_probe
        ├── scoring
        └── report_generator
```

如果 JAB 原生 API 用 C/C++ 更容易：

```text
jab_probe.exe
```

可以单独做一个小工具，然后主程序调用它。

最终：

```text
beh-detector.exe
```

或：

```text
python beh_detector.py
```

均可。

重点不是技术栈统一，而是：

> 探针之间解耦。

---

# 十八、推荐目录结构

```text
beh-automation-detector/
├── README.md
├── src/
│   ├── orchestrator/
│   ├── process_probe/
│   ├── java_probe/
│   ├── uia_probe/
│   ├── jab_probe/
│   ├── screenshot_probe/
│   ├── scoring/
│   └── report/
├── schemas/
│   └── capability_report.schema.json
├── tests/
├── output/
└── docs/
```

---

# 十九、第一里程碑不要贪大

Milestone 1 只需要完成：

```text
1. 找到 BEH 进程
2. 找到 BEH HWND
3. 判断是不是 Java Window
4. 导出 UIA Tree
5. 导出 JAB Tree
6. 截取 BEH 窗口
7. 生成一个简单 HTML 报告
```

暂时不要：

```text
控制画布
创建图元
连接 Relation
修改属性
保存 XML
```

---

# 二十、Milestone 1 的成功标准

至少回答：

```text
Q1：BEH是不是Java程序？

Q2：使用哪个Java？

Q3：UIA看到了多少？

Q4：JAB看到了多少？

Q5：中央Canvas是否暴露内部图元？

Q6：Menu / Tree / Palette / Property Panel是否可访问？

Q7：最推荐下一步采用什么自动化路线？
```

---

# 二十一、如果 JAB 比 UIA 看得多

例如：

```text
UIA：
BEH Window
└── Canvas

JAB：
BEH Window
├── Menu
├── Project Tree
├── Palette
├── Canvas
│   ├── Block A
│   ├── Block B
│   └── ...
└── Properties
```

那么明确结论：

> 后续 BEH Driver 应优先以 Java Access Bridge 为主。

---

# 二十二、如果 UIA 比 JAB 看得多

则：

> 后续优先 Windows UI Automation。

不要因为 BEH 是 Java 就强制使用 JAB。

---

# 二十三、如果两边各有优势

这很可能是现实情况。

例如：

```text
JAB：
Java内部控件信息强

UIA：
窗口级定位、标准Windows对话框强
```

最终方案：

```text
Hybrid Driver

JAB
+
UIA
+
XML Semantic Model
+
Screenshot Verification
```

---

# 二十四、如果 Canvas 是黑盒

不要立即判死刑。

继续检查：

```text
Canvas HWND / Accessible Bounds 是否稳定？
XML _location 是否可以映射到 Canvas 坐标？
缩放/平移状态能不能读？
截图中能不能可靠定位 Canvas？
```

如果这些可以：

后续仍可以：

```text
结构化控制外围
+
Canvas坐标操作
+
XML语义定位
+
视觉验证
```

判为 Level 3～4，而不是直接0分。

---

# 二十五、什么时候才判定“真的不适合接入”

只有当：

```text
UIA几乎不可见
JAB几乎不可见
Canvas完全黑盒
Canvas坐标还不稳定
窗口缩放后定位规律不稳定
菜单/属性也无法结构化控制
只有纯截图+鼠标
```

才把原生 BEH 自动化判为：

```text
Level 0 / Level 1
```

---

# 二十六、检测报告里必须给“下一步建议”

例如：

## Result A

```text
Level 5
```

建议：

```text
直接开发 BEH MCP / Driver
```

## Result B

```text
Level 4
```

建议：

```text
JAB/UIA Driver
+
Canvas 坐标适配器
```

## Result C

```text
Level 3
```

建议：

```text
XML Parser 负责图模型
UIA/JAB负责外围控件
Canvas鼠标操作
截图做验证
```

## Result D

```text
Level 1
```

建议：

```text
不要把原生BEH自动化作为主生成通道
优先Native Template + Patch Writer
```

---

# 二十七、不要让检测工具自己“决定事实”

所有关键结果都必须保留原始证据。

例如：

```json
{
  "canvas_visibility": {
    "result": "BLACKBOX_CANVAS_WITH_GEOMETRY",
    "evidence": {
      "uia_nodes": [],
      "jab_nodes": [],
      "canvas_bounds": {
        "x": 300,
        "y": 100,
        "width": 1200,
        "height": 800
      }
    }
  }
}
```

这样后面换模型、换算法仍可重新判断。

---

# 二十八、日志必须可追溯

每次检测生成唯一：

```text
run_id
```

例如：

```text
2026-08-14_012200
```

保存：

```text
BEH版本
Java版本
Windows版本
窗口大小
检测时间
检测工具版本
```

避免以后 BEH 升级后无法比较。

---

# 二十九、后续可增加“版本回归检测”

以后每次 BEH 升级：

```text
BEH v1
↓
Detector
↓
Level 4

BEH v2
↓
Detector
↓
Level 3
```

马上知道：

> 新版本让自动化能力退化了。

---

# 三十、给 Codex 的工作原则

你现在是在做：

> **调查工具**

不是：

> **自动化产品**

所以：

1. 先收集证据。
2. 不猜。
3. 不修改 BEH。
4. 不修改用户工程。
5. 不为了“测试成功”而点击危险控件。
6. 每项能力独立评分。
7. Canvas 单独评估。
8. JAB 和 UIA 都测，不预设谁更强。
9. 最终报告要让非专业用户也能看懂。
10. 完成本轮后停止，不扩展成写图元工具。

---

# 三十一、第一阶段完成标志

当用户打开 BEH 并运行：

```text
beh-detector
```

最终能看到：

```text
BEH AI 接入能力：★★★★

Java：
✓ OpenJDK detected

Windows UI Automation：
✓ 可访问

Java Access Bridge：
✓ 可访问

菜单：
✓

项目树：
✓

图元库：
✓ / 部分

属性面板：
✓

图形Canvas：
⚠ 只能看到Canvas本身，内部图元不可见

推荐：
开发 Hybrid BEH Driver：
JAB/UIA + XML坐标 + Canvas视觉验证
```

那么本阶段就完成。

---

# 三十二、核心一句话

> **现在不要猜“AI能不能控制BEH”。先造一个体检器，让它分别从进程/JVM、Windows UI Automation、Java Access Bridge、画布暴露程度和安全交互能力五个方向检测 BEH，然后按证据给出自动化等级；只有体检完成以后，才决定后续到底做纯原生 Driver、混合 Driver，还是回到 XML Template/Patch 路线。**

---

# 三十三、官方技术依据（供实现时核对）

## Oracle Java Access Bridge

Oracle Java Accessibility 文档说明：

- Java Access Bridge 用于让 Windows 上的辅助技术访问支持 Java Accessibility API 的 Java 应用。
- JDK 提供 `jaccesswalker` 和 `jaccessinspector` 用于查看 Java GUI accessibility 信息。
- Java Access Bridge Native API 提供：
  - `initializeAccessBridge`
  - `IsJavaWindow`
  - `GetAccessibleContextFromHWND`
  - `GetAccessibleContextInfo`
  - `GetAccessibleChildFromContext`
  - 等接口。

实现时优先对照 Oracle 官方文档。

## Microsoft Windows UI Automation

Windows UI Automation 将应用 UI 暴露为可遍历的 Automation Tree，并提供：

- element properties
- control type
- AutomationId
- bounding rectangle
- Invoke / Value / Selection / ExpandCollapse 等 patterns

实现时优先对照 Microsoft Learn 官方 UI Automation 文档。

## Microsoft `winapp ui`

微软当前提供 `winapp ui`：

```text
inspect
screenshot
search
invoke
set-value
click
drag
send-keys
```

可用于 AI agent 和开发者检查、操作运行中的 Windows 应用。

但当前 `winapp CLI` 属于 Public Preview。

因此：

> 可以作为第一阶段非常方便的探测工具，但核心架构不要永久依赖它的某个具体 CLI 行为。
