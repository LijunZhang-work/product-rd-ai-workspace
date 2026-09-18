> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../../README.md)。资料归档不代表产品功能或实机验证已经完成。

# BEH FB 行为测试最小 MVP 实施规范（独立于旧 FB 测试框架）

**版本：** v2.0  
**状态：** 当前执行规范  
**目标：** 在不依赖现有旧 FB 测试框架的前提下，基于真实 BEH Runtime，为一个真实 FB 建立最小、可信、可重复的行为测试闭环。

---

# 1. 核心决策

本轮正式决策如下：

> **新的 FB Test MVP 不基于、不依赖、不继承现有旧 FB 测试框架。**

原因：

- 现有 CB 小图元测试框架相对成熟，可继续作为独立资产使用；
- 现有 FB 大图元测试框架当前成熟度不足，不能作为新 FB 行为测试的可信基础；
- 如果继续沿旧 FB 框架修补，容易继承其历史设计限制、不完整执行链和错误假设；
- 当前目标不是“修好旧 FB 测试框架”，而是证明一个真实 FB 能否通过真实 BEH Runtime 被独立、可信地自动测试。

因此当前路线是：

```text
旧 FB 测试框架
    ↓
仅作为非权威参考资料
    ↓
可查看、可借鉴个别已验证的小工具实现
    ↓
但不得成为新 MVP 的基础依赖

新 FB Test MVP
    ↓
直接基于真实 BEH Runtime
    ↓
真实 Parser / Model / Manager / Director / Execution
    ↓
真实 FB
    ↓
输入 → 执行 → 输出 → ASSERT
```

---

# 2. 一句话目标

本轮只证明：

```text
真实 FB
→ 使用真实 BEH Parser / Model / Runtime 加载
→ 注入真实输入
→ 真实执行一次或若干周期
→ 读取真实输出
→ 自动断言
→ 正确预期时 PASS
→ 故意错误预期时 FAIL
```

满足以上闭环，才算 MVP 成功。

---

# 3. 非目标

本轮明确不做：

- 不修复整个旧 FB 测试框架；
- 不要求兼容旧 FB 测试框架；
- 不把旧 FB 测试框架迁移为新架构；
- 不建设通用 FB 测试平台；
- 不批量支持多个 FB；
- 不做 Web UI；
- 不做测试用例自动生成；
- 不接 AI API；
- 不做完整测试管理系统；
- 不为了未来可能需求提前设计复杂抽象；
- 不顺带大规模重构 BEH 正式业务代码。

---

# 4. 新 MVP 的唯一基础

新 MVP 的基础必须是：

```text
原始 BEH 代码仓
+
原始 BEH Runtime
+
真实 FB XML / Model
+
真实 Ptolemy / BEH 执行链
```

允许新写的内容仅限：

```text
最小 Test Runner
测试输入适配
测试输出读取
断言
诊断 Probe
日志
测试 Fixture
真实性校验
```

这些新代码只能“驱动”和“观察”真实 FB，不能重新实现 FB。

---

# 5. 旧 FB 测试框架的地位

现有旧 FB 测试框架定义为：

> **Non-authoritative Reference Only**

即：

- 可以阅读；
- 可以用于理解历史做法；
- 可以查看其如何寻找 Port、初始化对象、组织测试等；
- 可以选择性借鉴个别工具函数；
- 但任何复用都必须单独证明其正确性；
- 不能因为“旧框架已经有”就默认可信；
- 不能把旧框架引入为新 MVP 的必需依赖；
- 不能让新 MVP 的成功条件依赖旧框架 PASS。

### 5.1 允许的选择性复用

只有满足以下全部条件，才允许复用旧框架中的某段代码：

```text
1. 功能边界清晰；
2. 不包含 FB 业务逻辑重实现；
3. 不绕过真实 BEH Runtime；
4. 不引入 Stub / Fake 执行链；
5. 可以单独验证；
6. 即使删除旧 FB 测试框架主体，新 MVP 仍然可以运行。
```

例如：

```text
“根据端口名寻找 TypedIOPort”
```

如果只是调用 BEH/Ptolemy 官方 API 的简单工具函数，且验证正确，可以选择性复用。

但：

```text
“旧框架自己的 FB 执行器”
“旧框架自己的状态模拟”
“旧框架自己的 Fake Director”
```

默认不得进入正式 MVP。

---

# 6. 禁止事项

以下任意情况出现，不允许宣称 MVP 成功。

## 6.1 禁止依赖旧框架

```text
禁止：
新 MVP → legacy-fb-test-framework → FB
```

正确关系：

```text
新 MVP → 原始 BEH Runtime → FB
```

旧框架只能旁路参考。

## 6.2 禁止重新实现 FB

禁止：

```text
读取FB逻辑
→ 手写一个C++/Java等价版本
→ 测这个新版本
```

因为这只能证明“重新实现的逻辑”正确。

## 6.3 禁止抽取部分源码拼“小 BEH”

禁止：

```text
复制几个Parser类
+
复制几个Actor类
+
补几个依赖
+
组成简化版运行环境
```

正式测试必须尽可能走原始 BEH Runtime。

## 6.4 禁止 Stub / Fake 进入 DUT 正式执行路径

以下默认禁止：

```text
Empty Stub
Fake Manager
Fake Director
Fake Port
Fake Actor
Fake Runtime
Fake Output
```

如果某个测试外围必须 Mock，只能用于 DUT 外围环境，且必须证明：

> 它没有替代 DUT 内部真实行为，也没有改变被测语义。

## 6.5 禁止为了 PASS 修改 Expected

Expected 必须来自：

```text
业务规格
人工已知简单结果
已有可信测试
明确数学/逻辑定义
```

不能根据当前程序实际输出反推 Expected。

---

# 7. MVP 架构

```text
┌──────────────────────────────┐
│ Minimal FB Test Runner       │
│ 输入 / 控制 / ASSERT / 报告    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Original BEH Runtime         │
│ Parser / Model / Runtime     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Real Target FB               │
│ Actor / Port / Relation      │
└──────────────┬───────────────┘
               ↓
      initialize / execute
               ↓
        Read Actual Output
               ↓
      ASSERT(expected, actual)
               ↓
          PASS / FAIL
```

---

# 8. DUT 选择

本轮只选一个真实 FB。

要求：

- 来自真实项目；
- 当前确实需要测试；
- 输入输出可以识别；
- 预期行为至少有一个简单 Case 可以人工确认。

不得为了 MVP 容易通过，人工造一个 Dummy FB 替代真实 FB。

如果当前目标 FB 很复杂，也仍然使用该真实 FB，但第一轮只选择最简单的可验证行为。

---

# 9. 实施阶段

## Phase 0：确认原始 BEH Baseline

首先复现原始 BEH 工程的真实构建环境。

记录：

```text
JDK
Maven
ECJ
Tycho / Target Platform
settings.xml
内部仓库
Profile
环境变量
生成步骤
正式构建入口
```

要求：

```text
原始代码
+
原始构建方式
+
不引入测试 Stub
→ Baseline Build PASS
```

如果 Baseline 不能建立：

```text
MVP_BLOCKED_BASELINE
```

不得绕过。

---

## Phase 1：调查真实 FB Runtime 调用链

这一阶段只调查，不开发通用框架。

必须回答：

```text
目标 FB 从哪里加载？
真实 XML / Model 路径是什么？
由哪个 Parser 加载？
加载后对象实际 Class 是什么？
Manager 是谁？
Director 是谁？
initialize 如何发生？
fire / iterate / execute 如何发生？
输入 Port 如何拿到？
输出 Port 如何拿到？
一个执行周期如何推进？
状态如何保存？
```

最终输出：

```text
FB XML
→ Real Parser
→ Real Model
→ Real FB Object
→ Real Manager / Director
→ initialize
→ input
→ execute
→ output
```

所有关键步骤必须指向真实源码位置。

---

# 10. Phase 2：建立独立最小 Runner

新建一个非常小的 Runner。

它只做：

```text
load
initialize
set input
execute
read output
assert
```

Runner 不包含：

```text
FB业务算法
FB状态机重实现
自定义Actor替代品
自定义Director替代品
```

Runner 的价值只是：

> 驱动真实系统。

---

# 11. Phase 3：第一个真实 PASS Case

选一个最简单、人工容易确定结果的 Case。

示例：

```text
Input:
A = 3
B = 5

Expected:
Y = true
```

执行链：

```text
真实FB加载
→ initialize
→ 输入注入
→ execute
→ 输出读取
→ ASSERT
```

输出至少包含：

```text
FB:
Input:
Execution count:
Expected:
Actual:
Result:
```

示例：

```text
[ RUN  ] TargetFB.normal_case
Input A = 3
Input B = 5

Expected Y = true
Actual   Y = true

[ PASS ] TargetFB.normal_case
```

---

# 12. Phase 4：必须证明“真 FAIL”

这是 MVP 的硬门禁。

使用：

```text
相同FB
相同输入
相同Runtime
相同执行步骤
```

只把 Expected 故意改错。

例如：

```text
真实输出 = true
故意Expected = false
```

必须得到：

```text
[ FAIL ] TargetFB.intentional_failure
Expected Y = false
Actual   Y = true
```

如果错误 Expected 仍然 PASS：

```text
MVP_FAIL_FALSE_PASS
```

立即停止。

---

# 13. Phase 5：增加一个关键行为

第一个 PASS/FAIL 闭环成立后，再选择该 FB 一个最关键行为：

- 边界值；
- 多周期；
- 状态；
- Reset；
- 延时；
- 多输入组合。

只选一个。

目的不是覆盖率，而是证明 Runner 能处理真实 FB 的关键语义。

---

# 14. Runtime 真实性验证

正式报告必须打印：

```text
Parser Class
FB Class
Manager Class
Director Class
Input Port Class
Output Port Class
```

并记录这些类实际来自：

```text
Module
JAR
Bundle
Source path
```

可使用类似：

```java
clazz.getProtectionDomain()
     .getCodeSource()
     .getLocation()
```

如果关键 Runtime Class 来自新建测试替代模块，而不是原始 BEH Runtime：

```text
RUNTIME_AUTHENTICITY_FAIL
```

---

# 15. 旧 FB 框架隔离检查

最终必须明确回答：

```text
新 MVP 是否需要旧 FB 测试框架才能编译？
YES / NO

新 MVP 是否需要旧 FB 测试框架才能运行？
YES / NO

新 MVP 是否调用旧 FB 框架执行器？
YES / NO

删除/禁用旧 FB 测试框架后，新 MVP 是否仍可运行？
YES / NO
```

正式成功要求：

```text
编译依赖旧框架：NO
运行依赖旧框架：NO
调用旧框架执行器：NO
禁用旧框架后仍可运行：YES
```

如果只复用了少量已验证工具函数，应将其复制/提取为独立 Utility，并记录来源，不得继续形成 legacy framework runtime dependency。

---

# 16. 最小目录建议

```text
fb_behavior_mvp/
├── runner/
│   └── MinimalFbRunner.java
├── fixtures/
│   └── target_fb_case.json
├── probes/
│   └── RuntimeOriginProbe.java
├── reports/
│   ├── pass_case.log
│   ├── intentional_fail_case.log
│   └── runtime_authenticity.md
└── README.md
```

目录只是建议。

原则是：

> 越小越好，不建设平台。

---

# 17. 错误分类

失败必须明确分类：

```text
BASELINE_BUILD_FAIL
REAL_FB_LOAD_FAIL
REAL_RUNTIME_NOT_FOUND
RUNTIME_AUTHENTICITY_FAIL
INPUT_PORT_NOT_FOUND
INPUT_INJECTION_FAIL
INITIALIZE_FAIL
EXECUTION_FAIL
TIME_CONTROL_FAIL
OUTPUT_PORT_NOT_FOUND
OUTPUT_READ_FAIL
ASSERTION_FAIL
FALSE_PASS
LEGACY_FRAMEWORK_DEPENDENCY_DETECTED
STUB_FAKE_DETECTED
UNKNOWN
```

禁止只写：

```text
“依赖还有问题”
“环境有些复杂”
“基本跑通”
```

---

# 18. 交付物

本轮只交付：

```text
01_target_fb.md
02_real_runtime_call_chain.md
03_minimal_runner/
04_test_fixture.json
05_pass_case.log
06_intentional_fail_case.log
07_runtime_authenticity_report.md
08_legacy_framework_independence_report.md
09_mvp_conclusion.md
```

---

# 19. Legacy Framework Independence Report

模板：

```text
1. 是否读取旧 FB 测试框架作为参考：
YES / NO

2. 是否复用了旧框架代码：
YES / NO

3. 如复用，具体文件/函数：
...

4. 复用内容是否只是工具性代码：
YES / NO

5. 是否复用旧框架的执行器：
YES / NO

6. 是否复用旧框架的状态模拟：
YES / NO

7. 是否依赖旧框架才能编译：
YES / NO

8. 是否依赖旧框架才能运行：
YES / NO

9. 禁用旧框架后新 MVP 是否仍能执行：
YES / NO

10. 结论：
INDEPENDENT / NOT_INDEPENDENT
```

正式验收要求：

```text
INDEPENDENT
```

---

# 20. Runtime Authenticity Report

模板：

```text
1. 原始 BEH 代码仓：
YES / NO

2. 原始构建方式：
YES / NO

3. 真实 FB：
YES / NO

4. 真实 Parser：
YES / NO

5. 真实 Model：
YES / NO

6. 真实 Manager：
YES / NO

7. 真实 Director：
YES / NO

8. 真实 Port：
YES / NO

9. 是否重新实现 FB 业务逻辑：
YES / NO

10. 是否有 Stub / Fake 进入执行路径：
YES / NO

11. 正确 Expected 是否 PASS：
YES / NO

12. 错误 Expected 是否 FAIL：
YES / NO

13. 当前结果是否具备正式可信度：
YES / NO
```

---

# 21. MVP 成功标准

只有全部满足，才能输出：

```text
FB_BEHAVIOR_TEST_MVP_PASS
```

必须满足：

```text
[ ] 原始 BEH Baseline Build 成功
[ ] 新 MVP 不依赖旧 FB 测试框架
[ ] 使用真实目标 FB
[ ] 使用真实 BEH Parser / Model / Runtime
[ ] 使用真实 Manager / Director
[ ] 输入进入真实 FB
[ ] 至少执行一次真实周期
[ ] 输出来自真实 FB
[ ] 正确 Expected → PASS
[ ] 错误 Expected → FAIL
[ ] 无正式执行路径 Stub / Fake
[ ] 禁用旧 FB 框架后仍可运行
[ ] 已生成 Runtime Authenticity Report
[ ] 已生成 Legacy Framework Independence Report
```

---

# 22. 允许的失败结果

如果真实链路暂时跑不通，但已经确定阻塞位置，可以输出：

```text
MVP_BLOCKED_WITH_EVIDENCE
```

例如：

```text
真实FB已经成功加载
真实Parser确认
真实Manager确认
但Director依赖Eclipse Runtime Context，当前Headless环境未建立
```

这是有效结果。

不得为了“做出 PASS”而：

```text
Stub Director
Fake Port
绕过 Runtime
手写 FB 逻辑
依赖旧测试框架兜底
```

---

# 23. 第一个 MVP 成功后再做什么

只有第一个真实 FB 成功后，才进入：

```text
第二个真实FB
↓
验证Runner是否可复用
↓
识别公共部分
↓
逐步抽象
↓
最终形成通用FB Behavior Harness
```

通用框架必须从多个真实成功 Case 中“长出来”。

不能提前设计一个大框架再把 FB 往里塞。

---

# 24. 最终原则

当前路线不是：

```text
修旧FB框架
→ 继续依赖旧框架
→ 让它勉强支持目标FB
```

而是：

```text
绕开旧FB测试框架
→ 直接连接真实BEH Runtime
→ 驱动真实FB
→ 真输入
→ 真执行
→ 真输出
→ 真PASS
→ 真FAIL
```

旧 FB 测试框架的唯一定位是：

> **可查看、可学习、可选择性借鉴；但不可信、不依赖、不继承。**

本轮最重要的验收问题只有两个：

```text
1. 这个测试测到的到底是不是真实 FB？
2. 把旧 FB 测试框架完全禁用后，它还能不能正常运行？
```

只有两个答案都是：

```text
YES
```

这个 MVP 才真正符合当前方向。
