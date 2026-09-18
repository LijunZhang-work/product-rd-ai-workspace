> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../../README.md)。资料归档不代表产品功能或实机验证已经完成。

# BEH Headless 图元行为测试 PoC 工程约束与防取巧指南

**版本：** v1.0  
**用途：** 约束 AI 在开发 BEH Headless 图元行为测试 PoC 时，必须优先保证正确性、真实性和可验证性，禁止为了“先跑起来”而把原始 BEH 系统裁剪、替换或伪造。

---

# 1. 本文档解决什么问题

当前 PoC 开发中已经出现以下风险：

- 没有先复现 BEH 原仓的真实构建方式；
- 只抽取部分源码单独编译；
- 缺依赖时再临时补依赖；
- 因为“不需要 GUI”就删除、跳过或排除 GUI/RCP 相关模块；
- 为了让编译通过而新增 Stub / Mock / Fake；
- 为了做“小测试”重新拼一套简化运行环境；
- 最终虽然可能“编译成功”或“测试能跑”，但实际运行的已经不是原始 BEH。

本项目的目标不是：

> 想办法让一个简化版系统跑起来。

而是：

> **在尽可能保持原始 BEH 运行语义不变的前提下，为其增加一个最小的 Headless 自动测试入口。**

---

# 2. 第一原则：Headless 不等于删掉 GUI

必须严格区分：

```text
Headless
= 不显示可见 GUI / 不要求人工操作界面

不是

Headless
= 删除 GUI 模块
= 删除 Eclipse RCP 模块
= 删除 Viewer / Editor / Canvas 依赖
= 把 GUI 类替换成 Stub
```

很多看似“GUI相关”的模块可能实际参与：

- OSGi / Eclipse Plugin 初始化；
- Extension Point 注册；
- Model / Resource 初始化；
- Editor Context；
- Command / Handler 注册；
- Ptolemy / Diva Figure 初始化；
- Layout / Routing；
- Class Loading；
- Target Platform；
- 静态初始化；
- 原生业务对象构造。

因此：

> **不能仅凭“测试不显示 GUI”就认定某个 GUI/RCP 模块可以删除。**

任何模块能否排除，必须有调用链和运行证据。

---

# 3. 第二原则：测试 Harness 可以小，被测系统不能偷偷变小

允许：

```text
一个很小的 Test Runner
↓
调用完整 BEH Runtime
↓
加载真实图源
↓
Headless 执行
↓
读取输出
↓
ASSERT
```

不允许：

```text
抽几个 BEH 类
+
自己拼 classpath
+
缺什么补什么
+
GUI模块删掉
+
Stub剩余依赖
+
再声称“BEH Headless测试跑通”
```

必须始终坚持：

> **缩小的是测试入口，不是被测对象。**

---

# 4. 正确开发顺序

## Phase 0：冻结当前 PoC 的“继续补洞式开发”

在完成下面验证前，不继续：

- 新增业务测试逻辑；
- 新增更多图元支持；
- 新增 Stub；
- 新增 Fake；
- 修改正式业务逻辑；
- 扩展新的简化运行环境。

先搞清楚：

> **当前正在运行的到底还是不是原始 BEH。**

---

## Phase 1：复现原始 BEH Baseline Build

首先只做原仓构建复现。

要求：

```text
原始代码仓
+
原始构建方式
+
原始依赖
+
原始编译器 / Target Platform
+
原始构建脚本 / Maven Profile
→
在不修改业务源码的情况下构建成功
```

必须找到并记录：

```text
官方/原项目构建入口
真实构建命令
JDK版本
Maven版本
Eclipse Compiler / ECJ版本
Tycho版本（如有）
Target Platform
Maven Profile
p2 Repository
依赖仓库 / 镜像
settings.xml要求
环境变量
构建前生成步骤
构建顺序
```

禁止默认使用：

```text
mvn clean install
```

除非源码和项目资料能够证明这就是原始构建入口。

---

# 5. 构建问题处理规则

每个构建失败只能先归类，不允许直接开始 patch。

允许的分类：

```text
ENVIRONMENT_MISSING
DEPENDENCY_MISSING
OFFICIAL_BUILD_ASSUMPTION_UNKNOWN
VERSION_MISMATCH
TARGET_PLATFORM_MISSING
DEPENDENCY_REPOSITORY_MISSING
GENERATED_ARTIFACT_MISSING
BUILD_ORDER_UNKNOWN
```

处理流程：

```text
报错
↓
定位它与原始构建环境的差异
↓
恢复原本应该存在的环境/依赖
↓
重新构建
```

禁止：

```text
报错
↓
找个类似Jar替代
↓
改版本
↓
写Stub
↓
跳过模块
↓
继续
```

---

# 6. Stub / Mock / Fake 的硬性规则

## 默认禁止

以下任何形式默认不得进入正式 PoC 执行路径：

```text
空类 Stub
空方法 Stub
返回默认值的 Fake
假的 GUI 类
假的 Manager / Director
假的 Resource / Workspace
假的 Renderer / Canvas
假的 Plugin / Service
```

尤其禁止：

```text
原依赖缺失
→ 新建同名空实现
→ 编译通过
```

这会把：

```text
“环境有问题”
```

伪装成：

```text
“系统运行成功”
```

---

## 唯一允许使用 Stub 的情况

仅用于：

```text
明确的探索性 Probe
```

并且必须同时满足：

1. 不进入最终被测执行链；
2. 不参与业务输出；
3. 不参与模型初始化；
4. 不影响生命周期；
5. 有调用链证据证明；
6. 在正式 PoC 中最终删除。

报告中必须标记：

```text
EXPLORATION_ONLY_STUB
```

不得把带 Stub 的执行结果作为：

```text
BEH_BEHAVIOR_TEST_PASS
```

证据。

---

# 7. GUI/RCP 模块不能“想当然删除”

如果 AI 认为某模块不需要，必须输出：

```text
模块：
为什么看起来可删除：
谁引用它：
实际运行时是否加载：
是否参与模型初始化：
是否参与Extension Point：
是否参与Command/Handler：
是否参与Figure/Layout/Router：
排除后行为差异：
证据：
```

只有证明：

```text
不加载
不初始化
不影响被测模型
不影响执行语义
```

后，才允许在专用 Headless Profile 中排除。

否则保持原样。

---

# 8. Baseline 成功的定义

以下条件同时满足，才允许写：

```text
BASELINE_BUILD_PASS
```

必须满足：

```text
[ ] 使用原始代码仓
[ ] 使用原始构建入口
[ ] 没有修改正式业务源码
[ ] 没有新增正式执行路径Stub
[ ] 没有为了通过编译随意替换依赖
[ ] 没有任意修改依赖版本
[ ] 没有随意跳过原模块
[ ] 构建产物与原项目类型一致
[ ] 核心类来自真实BEH模块/JAR
```

---

# 9. 第二阶段：证明“完整 BEH + Headless 入口”

Baseline Build 成功后，再做 Headless PoC。

目标：

```text
完整BEH Runtime
↓
不显示可见GUI
↓
加载真实POU
↓
真实Manager/Director
↓
initialize
↓
iterate
↓
读取真实Output
```

注意：

> “不显示 GUI”不代表“删除 GUI 模块”。

可以接受：

```text
完整模块仍然存在
但不创建可见窗口
```

或者：

```text
只避免启动Workbench UI
但仍加载必要Plugin/Runtime
```

具体方式必须由源码事实决定。

---

# 10. 第三阶段：最小图元行为测试

只有前两阶段完成后，才开始：

```text
Test Input
↓
真实被测图元
↓
Test Output
```

Runner：

```text
load
→ initialize
→ inject input
→ iterate
→ read output
→ assert
```

必须故意制造一个错误 expected，证明 Runner 会真实 FAIL。

禁止：

```text
测试永远PASS
```

或者：

```text
通过Fake Output让断言通过
```

---

# 11. AI 每轮必须输出“真实性检查表”

每一轮工作结束前，必须给出：

```text
## Runtime Authenticity Report

1. 当前是否使用完整原仓代码：
YES / NO

2. 当前是否修改原有业务源码：
YES / NO
修改文件：

3. 当前是否排除原始模块：
YES / NO
模块：

4. 当前是否新增 Stub / Mock / Fake：
YES / NO
列表：

5. 是否有 Stub 进入被测执行路径：
YES / NO
证据：

6. 当前构建命令是否来自原项目真实构建方式：
YES / NO
证据：

7. 当前核心 Runtime 类实际从哪里加载：
Manager:
Director:
Model:
图元实现:
Resource:
其他关键类:

8. 当前 PoC 是否仍然调用真实 BEH Runtime：
YES / NO / UNPROVEN

9. 当前结果是否有资格作为正确性证据：
YES / NO
原因：
```

---

# 12. 一票否决项

出现以下任意一项，本轮结果不得作为正确性证明：

```text
[ ] 使用空Stub替代真实运行依赖
[ ] 为了编译通过随意改依赖版本
[ ] 未证明就删除GUI/RCP模块
[ ] 从原仓抽取少量源码重新拼一个运行时
[ ] 自己实现原本BEH已有的业务逻辑
[ ] 使用Fake输出通过断言
[ ] 修改测试Expected迁就当前实现
[ ] Baseline Build尚未成功就宣称Headless行为正确
[ ] 无法证明核心类来自真实BEH
```

统一状态：

```text
AUTHENTICITY_FAIL
```

---

# 13. 允许 AI 做的探索性工作

为了理解工程，可以：

```text
写dependency scanner
写classpath probe
打印classloader来源
打印OSGi bundle状态
打印Extension Point
打印Manager/Director调用链
分析pom.xml
分析target platform
分析build log
写一次性diagnostic launcher
```

这些都属于：

```text
Observation / Probe
```

非常鼓励。

但：

> Probe 不能替代真实系统。

---

# 14. 推荐增加 Class Origin Probe

PoC运行时建议自动输出关键类来源：

```java
Class<?> c = Manager.class;
System.out.println(
    c.getProtectionDomain()
     .getCodeSource()
     .getLocation()
);
```

对关键类全部记录：

```text
Manager
Director
CompositeActor
被测图元Class
Parser
Resource
BEH自定义Runtime类
```

这样可以防止：

> AI以为自己运行的是原BEH，实际ClassLoader加载的是自己拼的替代类。

---

# 15. 推荐增加依赖锁定报告

自动生成：

```text
build-environment.lock.md
```

内容：

```text
JDK
Maven
ECJ
Tycho
Profiles
Target Platform
Repository
核心Bundle版本
核心Jar Hash
构建命令
```

一旦 Baseline Build 成功：

> 后续 PoC 不允许随意改变这些版本。

任何变更必须标：

```text
BUILD_ENVIRONMENT_CHANGE
```

并重新跑 Baseline。

---

# 16. 最终正确架构

正确：

```text
┌───────────────────────┐
│ Small Test Harness    │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Original BEH Runtime  │
│ Full real modules     │
└───────────┬───────────┘
            ↓
      Real Graph Model
            ↓
    Real Execution Chain
            ↓
       Read Output
            ↓
       PASS / FAIL
```

错误：

```text
抽一些BEH代码
+
删掉GUI
+
缺依赖就补
+
Stub剩余类
+
重新拼一个“小BEH”
+
PASS
```

---

# 17. 当前开发模型的工作优先级

从现在开始优先级固定为：

```text
P0 证明原仓真实构建方式
↓
P1 Baseline Build
↓
P2 Runtime真实性证明
↓
P3 Headless最小执行
↓
P4 一个真实图元行为测试
↓
P5 抽象Test Runner
↓
P6 扩展更多图元
```

禁止倒序。

---

# 18. 一句话原则

> **我们宁可现在 PoC 失败，也不要通过裁剪、Stub、Fake、替代依赖做出一个“看起来成功但测的不是原始 BEH”的假 PoC。**

本项目评价成功的第一标准不是：

```text
能不能编过
能不能跑
```

而是：

```text
跑的到底是不是原来的BEH
测的到底是不是真实业务行为
结果到底能不能作为正确性证据
```
