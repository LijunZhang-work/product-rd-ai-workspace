# BEH FB 行为测试最小 MVP 实施指南

**版本：** v1.0  
**目标：** 针对一个真实 FB，完成可重复、可断言、可真实失败的最小行为测试闭环。  
**当前定位：** 不是建设通用 FB 测试平台，只验证“一个真实 FB 能否被可信地自动测试”。

---

# 1. 一句话目标

本轮只证明：

```text
真实 FB
→ 使用真实 BEH 解析与执行链加载
→ 注入真实输入
→ 执行一次或若干周期
→ 读取真实输出
→ 自动断言
→ 正确预期时 PASS
→ 故意错误预期时 FAIL
```

只有这条闭环真实跑通，后续才讨论通用化。

---

# 2. 本轮范围

## 2.1 必须完成

1. 选择一个真实 FB 作为 DUT（Device Under Test）。
2. 使用原始 BEH 代码仓和原始构建方式。
3. 加载该 FB 的真实 XML / Model。
4. 走真实 BEH / Ptolemy 执行链。
5. 找到并使用真实输入、输出端口或等价输入输出接口。
6. 注入至少一组输入。
7. 执行一次或若干周期。
8. 读取真实输出。
9. 自动比较 `expected` 与 `actual`。
10. 同一个用例：
    - 正确 `expected` 必须 PASS；
    - 故意写错 `expected` 必须 FAIL。
11. 输出可复现证据。

## 2.2 当前不做

- 不建设通用 FB 测试框架；
- 不批量支持多个 FB；
- 不做 Web UI；
- 不做测试用例自动生成；
- 不接入 AI API；
- 不做性能优化；
- 不做完整测试管理平台；
- 不做复杂报告系统；
- 不为“以后可能需要”提前设计大量抽象；
- 不顺带重构 BEH 正式代码。

---

# 3. DUT 选择原则

优先选择：

```text
真实存在
输入输出明确
业务结果容易确认
依赖较少
执行周期可控
```

如果当前已经指定要测的 FB，就必须使用该 FB。

如果尚未指定，选择一个最简单但真实的 FB，不得使用人工伪造的 Dummy FB 代替。

如果该 FB 有状态或时间行为，可先做一个最简单的静态输入输出 Case，再补一个最小多周期 Case。

---

# 4. 正确架构

```text
┌──────────────────────────────┐
│ Minimal FB Test Runner       │
│ 测试入口、输入、断言、报告     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Original BEH Runtime         │
│ 原始 Parser / Model / Runtime │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Real Target FB               │
│ 真实图元、Port、Relation、状态 │
└──────────────┬───────────────┘
               ↓
       initialize / iterate
               ↓
          Read Actual Output
               ↓
      ASSERT(expected, actual)
               ↓
          PASS / FAIL
```

必须满足：

> 测试 Runner 可以很小，但被测 FB 和执行 Runtime 必须是真实的。

---

# 5. 禁止取巧

以下任意一项出现，本轮不能宣称 MVP 成功：

```text
1. 把 FB 的业务逻辑重新手写一遍再测试
2. 只抽取几个 BEH 类重新拼一个“小 BEH”
3. 删除未经证明可删除的 GUI / RCP / Plugin 模块
4. 使用空 Stub / Fake 替代真实执行依赖
5. 使用 Fake 输出让断言通过
6. 跳过真实 Parser / Model / Runtime
7. 修改测试 Expected 迎合当前实现
8. 构建没复现成功就继续写测试逻辑
9. 只打印“PASS”，但没有真实读取 FB 输出
10. 只证明能运行，未证明能真实 FAIL
```

允许写：

```text
测试入口
诊断 Probe
日志
Class Origin 检查
最小断言工具
测试 Fixture
```

但这些不能替代真实 FB Runtime。

---

# 6. 开发顺序

## Phase 0：Baseline 构建确认

先确认原始 BEH 代码仓可以按原有方式构建。

必须记录：

```text
JDK版本
Maven版本
Eclipse Compiler / ECJ
Tycho / Target Platform（如有）
构建入口
构建命令
Profile
外部仓库 / settings.xml
环境变量
构建前生成步骤
```

要求：

```text
原始构建方式
+
不改业务源码
+
不加正式路径Stub
→ Baseline Build PASS
```

Baseline 未通过，不得进入后续阶段。

---

## Phase 1：确认目标 FB 的真实执行链

必须回答：

```text
FB从哪个XML/Model加载
由哪个Parser加载
真实FB对象Class是什么
Manager / Director是谁
initialize如何调用
iterate / fire如何调用
输入从哪里进入
输出从哪里读取
```

输出最短调用链：

```text
FB XML
→ Parser
→ Model
→ Runtime
→ initialize
→ iterate/fire
→ Output
```

如果链路断裂，明确写：

```text
BREAK_AT = ...
```

不要用替代实现补过去。

---

## Phase 2：最小测试 Fixture

构造最小测试环境：

```text
Test Input
→ Target FB
→ Test Output
```

要求：

- 使用真实 FB；
- 使用真实 Port / Parameter / Variable；
- 只保留完成本次测试所需的最小外围；
- 外围可以是测试适配器，但不能替代 DUT 内部逻辑；
- 所有输入和输出必须可追踪。

---

## Phase 3：第一个真实 PASS Case

选择一个结果容易确认的 Case。

示例：

```text
Case: normal_input

Input:
A = ...

Expected:
Y = ...
```

执行：

```text
load
→ initialize
→ inject input
→ iterate
→ read output
→ assert
```

输出：

```text
[ RUN  ] FB_Name.normal_input
[ PASS ] FB_Name.normal_input
```

必须同时打印：

```text
输入值
实际执行周期
实际输出
期望输出
```

---

## Phase 4：证明测试能真实 FAIL

使用完全相同的 DUT、输入和执行链，仅把 `expected` 故意改成错误值。

必须输出：

```text
[ RUN  ] FB_Name.intentional_failure
[ FAIL ] FB_Name.intentional_failure
         expected = ...
         actual   = ...
```

如果故意错误的 `expected` 仍然 PASS：

```text
MVP_FAIL
```

不得继续。

---

## Phase 5：最小关键行为 Case

根据 FB 类型，只选择一个最关键行为：

```text
边界值
状态变化
Reset
多输入组合
延时
周期推进
```

不要求一次覆盖完整业务。

如果 FB 有时间行为，最小示例：

```text
cycle 0: IN=false → Q=false
cycle 1: IN=true  → Q=false
cycle N: IN=true  → Q=true
reset:   IN=false → Q=false
```

---

# 7. 最小测试用例格式

第一版可以使用简单 JSON：

```json
{
  "suite": "TargetFB",
  "case": "normal_input",
  "inputs": {
    "A": 3,
    "B": 5
  },
  "execution": {
    "initialize": true,
    "iterations": 1
  },
  "expected": {
    "Y": true
  }
}
```

有周期时：

```json
{
  "suite": "TargetFB",
  "case": "state_transition",
  "steps": [
    {
      "cycle": 0,
      "inputs": {"IN": false},
      "expected": {"Q": false}
    },
    {
      "cycle": 1,
      "inputs": {"IN": true},
      "expected": {"Q": false}
    },
    {
      "cycle": 3,
      "inputs": {"IN": true},
      "expected": {"Q": true}
    }
  ]
}
```

第一版不必设计复杂 DSL。

---

# 8. 最小命令行体验

目标可以是：

```bash
beh-fb-test --fb path/to/fb.xml --case tests/normal_input.json
```

输出：

```text
BEH FB Behavior Test

FB: TargetFB
Runtime: Original BEH Runtime
Case: normal_input

Input:
  A = 3
  B = 5

Execution:
  initialize = PASS
  iterations = 1

Output:
  expected Y = true
  actual   Y = true

RESULT: PASS
```

错误时：

```text
RESULT: FAIL
expected Y = true
actual   Y = false
```

第一版允许直接使用 JUnit 或最小自定义断言，不要求模仿 gtest 的所有功能。

---

# 9. 真实性检查

测试运行时必须记录关键类来源：

```text
Parser Class:
FB Class:
Manager Class:
Director Class:
Runtime Class:
Input Port Class:
Output Port Class:
```

并打印它们实际来自哪个 JAR / Module / Bundle。

示例：

```java
clazz.getProtectionDomain()
     .getCodeSource()
     .getLocation()
```

目标是证明：

> 当前加载的是原始 BEH Runtime，而不是 AI 新建的替代类。

---

# 10. 现有 FB 测试框架如何处理

现有框架虽然不成熟，但可以逐项评估和复用。

建立能力表：

| 能力 | 可直接复用 | 需要修复 | 不可信/不用 | 证据 |
|---|---:|---:|---:|---|
| 加载真实FB |  |  |  |  |
| 创建Manager/Director |  |  |  |  |
| 输入注入 |  |  |  |  |
| 周期执行 |  |  |  |  |
| 输出读取 |  |  |  |  |
| 断言 |  |  |  |  |
| Reset |  |  |  |  |

原则：

> 只修当前 MVP 真正缺失的能力，不顺便重构整个旧框架。

---

# 11. 错误分类

MVP 失败时，必须明确归类：

```text
BASELINE_BUILD_FAIL
FB_LOAD_FAIL
RUNTIME_NOT_AUTHENTIC
MANAGER_OR_DIRECTOR_MISSING
INPUT_INJECTION_FAIL
EXECUTION_FAIL
TIME_OR_CYCLE_CONTROL_FAIL
OUTPUT_READ_FAIL
ASSERTION_FAIL
STUB_OR_FAKE_DETECTED
UNKNOWN
```

禁止只写：

```text
“还有一些依赖问题”
“暂时跑不通”
```

---

# 12. 交付物

本轮只要求以下产物：

```text
01_target_fb.md
02_runtime_call_chain.md
03_existing_fb_test_framework_capability.md
04_test_fixture.json
05_test_runner/
06_pass_case.log
07_intentional_fail_case.log
08_runtime_authenticity_report.md
09_mvp_conclusion.md
```

---

# 13. Runtime Authenticity Report 模板

```text
1. 是否使用原始代码仓：
YES / NO

2. 是否使用原始构建入口：
YES / NO
证据：

3. 是否修改正式业务源码：
YES / NO
文件：

4. 是否排除原模块：
YES / NO
模块：

5. 是否新增 Stub / Mock / Fake：
YES / NO
列表：

6. 是否有 Stub / Mock / Fake 进入 DUT 执行路径：
YES / NO
证据：

7. DUT 是否是真实 FB：
YES / NO
Class / XML：

8. Parser / Manager / Director / Runtime 的真实来源：
...

9. 输入是否进入真实 FB：
YES / NO
证据：

10. 输出是否来自真实 FB：
YES / NO
证据：

11. 当前结果是否有资格作为正确性证明：
YES / NO
原因：
```

---

# 14. MVP 成功标准

只有以下全部满足，才允许写：

```text
FB_BEHAVIOR_TEST_MVP_PASS
```

必须满足：

```text
[ ] 原始 Baseline Build 已通过
[ ] 使用真实 FB
[ ] 使用真实 BEH Parser / Model / Runtime
[ ] 输入成功进入真实 FB
[ ] 至少执行一次真实周期
[ ] 输出来自真实 FB
[ ] 正确 expected 能 PASS
[ ] 错误 expected 能 FAIL
[ ] 没有正式执行路径 Stub / Fake
[ ] 结果可重复运行
[ ] 已生成真实性报告
```

---

# 15. MVP 失败也可以是有效结果

如果真实链路跑不通，但准确定位到：

```text
缺少哪个执行入口
哪个依赖尚未复现
哪个模块阻塞
现有FB测试框架哪一段不可信
```

则本轮可输出：

```text
MVP_BLOCKED_WITH_EVIDENCE
```

这比通过裁剪、Stub、Fake 获得一个假 PASS 更有价值。

---

# 16. 后续扩展条件

只有第一个真实 FB MVP 通过后，才允许：

```text
第二个FB
↓
比较共性
↓
抽象通用Runner
↓
增加边界/异常/状态测试
↓
批量执行
↓
CI集成
```

不要先设计完整平台。

---

# 17. 最终原则

> **当前目标不是证明“我们会写一个测试框架”，而是证明“一个真实 FB 可以在真实 BEH Runtime 中被自动输入、执行、读取和断言”。**

最小成功闭环：

```text
真FB
+
真Runtime
+
真输入
+
真执行
+
真输出
+
真PASS
+
真FAIL
```
