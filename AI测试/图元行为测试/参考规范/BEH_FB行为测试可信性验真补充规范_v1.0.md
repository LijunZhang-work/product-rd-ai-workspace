> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../../README.md)。资料归档不代表产品功能或实机验证已经完成。

# BEH FB 行为测试可信性验真补充规范

**版本：** v1.0  
**定位：** 对《BEH FB 行为测试最小 MVP 实施规范》的补充  
**适用阶段：** 第一个 FB MVP 已跑通，开始验证第二个及后续更复杂 FB 时  
**核心问题：** 如何证明“测试通过”不是因为开发 AI 看过实现后把当前输出抄进 Expected，而是真正具备发现错误的能力。

---

# 1. 本补充规范解决什么问题

FB 测试出现：

```text
TEST PASS
```

本身不能证明测试有效。

尤其当同一个 AI 同时做了：

```text
阅读 FB 实现
→ 写测试
→ 决定 Expected
→ 运行测试
```

就存在明显风险：

```text
先看到当前实现结果
→ 把当前结果写进 Expected
→ 测试自然 PASS
```

这种情况只能证明：

> 测试代码和当前实现“彼此一致”。

不能证明：

> 当前 FB 的业务行为正确。

因此，从第二个稍复杂 FB 开始，正式验收对象不再只是：

```text
FB 是否 PASS
```

还必须增加：

```text
这套测试有没有能力让错误 FB FAIL
```

---

# 2. 核心原则

以后评价一套 FB 测试，不问：

> “它有多少个 PASS？”

而问：

> **“如果 FB 真写错了，这套测试能不能把错误抓出来？”**

测试可信度的核心证据必须来自：

```text
Expected 来源独立性
+
Mutation Testing
+
Hidden Test
+
Property / Invariant / Metamorphic Test
```

其中 Mutation Testing 为当前阶段最重要的硬门禁。

---

# 3. Expected 不得默认来自当前实现

每一个确定值断言，都必须标注 Expected 的来源。

允许来源分类如下：

```text
S1 — Specification
来自需求、规格、正式设计定义

S2 — Mathematical / Logical Definition
来自明确数学、布尔、状态或时序定义

S3 — Independent Human Calculation
由人依据规则独立计算

S4 — Trusted Golden
来自已经验证过的 Golden / 正确历史版本

S5 — Independent Reference Model
来自独立实现的参考模型，且该模型不是复制 DUT 实现

I1 — Current Implementation Derived
通过阅读当前 FB 实现、当前运行结果或当前输出反推
```

正式正确性测试允许：

```text
S1 / S2 / S3 / S4 / S5
```

默认禁止：

```text
I1
```

作为正式 Oracle。

---

# 4. Expected 来源报告

每个正式 Case 至少记录：

```text
Case ID:
...

Inputs:
...

Expected:
...

Expected Source:
S1 / S2 / S3 / S4 / S5 / I1

Source Evidence:
...

Was Current FB Implementation Consulted When Deriving Expected:
YES / NO

Oracle Confidence:
HIGH / MEDIUM / LOW
```

如果：

```text
Expected Source = I1
```

则该 Case 只能作为：

```text
OBSERVATION / REGRESSION SNAPSHOT
```

不能作为：

```text
CORRECTNESS PROOF
```

---

# 5. Mutation Testing 是正式硬门禁

## 5.1 定义

Mutation Testing 的目的不是测试断言本身，而是故意把 DUT 改坏，然后观察现有测试是否失败。

正确闭环：

```text
Original FB
→ Tests PASS

故意制造 Bug #1
→ Tests FAIL

故意制造 Bug #2
→ Tests FAIL

故意制造 Bug #3
→ Tests FAIL
```

这才能证明测试真正“会抓错”。

---

# 6. Mutation 不得改 Expected

Mutation 实验期间固定：

```text
测试输入不变
Expected 不变
测试 Runner 不变
Oracle 不变
```

只允许改变：

```text
DUT
```

禁止：

```text
Mutation 后重新生成 Expected
Mutation 后让 AI 修改测试来适配
Mutation 后更新 Golden
```

否则实验失效。

---

# 7. 第一版 Mutation 数量

第二个稍复杂 FB：

```text
至少 3 个 Mutation
建议 3~5 个
```

不追求大规模自动 Mutation Framework。

当前重点是验证：

> 测试是否对真实业务错误敏感。

---

# 8. Mutation 必须“有代表性”

不要只做语法错误或编译失败。

好的 Mutation 应该满足：

```text
程序仍能加载
程序仍能执行
但业务行为发生错误
```

优先从以下类别选择。

## M1 — 条件边界错误

例如：

```text
>  → >=
<  → <=
== → !=
```

## M2 — 运算错误

例如：

```text
+ → -
* → /
AND → OR
```

## M3 — 参数错误

例如：

```text
threshold = 100 → 101
delay = 3 → 2
gain = 1000 → 100
```

## M4 — Port / Relation 错误

例如：

```text
正确输出 Port
→ 接到另一个合法 Port
```

要求仍能形成合法模型。

## M5 — 状态错误

例如：

```text
Reset 后不清状态
状态提前切换
状态保持条件错误
```

## M6 — 时序错误

例如：

```text
3周期触发
→ 2周期触发
```

## M7 — 初始化错误

例如：

```text
初始值 false
→ true
```

---

# 9. Mutation 结果术语

每个 Mutation 必须输出：

```text
KILLED
```

或：

```text
SURVIVED
```

定义：

```text
KILLED
= 原始测试至少有一个 Case 因该错误而 FAIL

SURVIVED
= 故意错误存在，但所有正式测试仍 PASS
```

SURVIVED 不是“Mutation 不重要”。

默认含义是：

> 当前测试存在覆盖或 Oracle 缺口。

---

# 10. Mutation 结果模板

```text
Mutation ID:
MUT-001

Mutation Type:
Boundary Condition

Changed Behavior:
x > threshold
→
x >= threshold

Why This Is Wrong:
...

Original FB:
PASS

Mutated FB:
FAIL / PASS

Result:
KILLED / SURVIVED

Which Test Detected It:
...

If SURVIVED:
Why Current Tests Missed It:
...

Required New Test:
...
```

---

# 11. 必须避免“为了 Mutation 写针对答案的测试”

Mutation 的作用是验证已有测试。

正确顺序：

```text
先冻结正式测试集
↓
再创建 Mutation
↓
运行冻结测试
```

禁止：

```text
先看 Mutation
↓
再专门写一个只能抓该 Mutation 的 Case
↓
宣布 Mutation KILLED
```

如果要补 Case，允许，但必须分两阶段记录：

```text
Before Fix:
SURVIVED

Gap Analysis:
...

Added Test:
...

After Fix:
KILLED
```

这样才能保留真实测试改进证据。

---

# 12. Hidden Test 机制

为了进一步降低“开发 AI 已知答案”的风险，正式阶段建议保留一小组 Hidden Tests。

基本角色：

```text
Builder AI
→ 负责 Runner / DUT 接入

Test Designer / Human
→ 依据规格设计 Hidden Test

Evaluator
→ 最后执行 Hidden Test
```

Builder AI 不应在开发阶段看到：

```text
Hidden Inputs
Hidden Expected
完整 Hidden Case 数量
```

---

# 13. Hidden Test 最小要求

当前 MVP 阶段不需要复杂基础设施。

第二个 FB 建议：

```text
2~3 个 Hidden Cases
```

即可。

可以由：

```text
用户
独立 AI 会话
另一个 Agent
```

设计，但前提是：

> 设计 Expected 时不依赖当前 FB 实现。

---

# 14. Hidden Test 验收

最终只报告：

```text
Hidden Cases:
3 total
3 PASS
0 FAIL
```

正式报告中可以隐藏具体输入与 Expected，避免后续开发过程污染。

如果需要调试失败：

```text
先给失败类别
再逐步开放必要信息
```

避免直接把完整答案泄露给 Builder。

---

# 15. Property / Invariant Testing

复杂 FB 不一定所有输入都容易得到精确 Expected。

此时必须增加“不依赖具体答案”的性质测试。

例如：

```text
输出必须处于合法范围
Reset 后必须回初态
触发条件未满足前绝不能置位
输入不变时状态不能无故跳变
非法输入不能产生非法输出
某两个输出不能同时为 true
```

这些称为：

```text
Property
Invariant
```

---

# 16. Metamorphic Testing

如果某个输入的具体输出难以人工计算，可以验证“输入发生某种变化后，输出关系必须满足什么”。

例如：

```text
Input A 增加
→ Output 不允许下降
```

或：

```text
同样输入重复执行
→ 无状态 FB 输出必须一致
```

或：

```text
Reset 后重新输入相同序列
→ 输出序列必须与第一次一致
```

这种方式不要求知道每一个绝对答案，但可以抓大量错误。

---

# 17. Test Oracle 与 DUT 必须尽量独立

禁止形成：

```text
DUT实现
↓
AI阅读DUT
↓
生成Expected
↓
用Expected验证DUT
```

这属于循环证明。

正确路线优先是：

```text
业务规则 / 规格 / 独立模型
↓
Expected
```

与：

```text
真实 FB 实现
↓
Actual
```

最后比较：

```text
Expected vs Actual
```

Oracle 与 DUT 越独立，测试可信度越高。

---

# 18. AI 使用规则

允许 AI：

```text
根据规格设计 Case
生成测试代码
执行测试
分析 FAIL
生成 Mutation 候选
总结覆盖缺口
```

但如果 AI 已经阅读当前 FB 实现，则：

> 它不能仅凭该实现生成正式 Expected 并把这些 Expected 当作正确性 Oracle。

如果无法避免同一 AI 阅读实现，至少必须通过：

```text
Mutation
Hidden Test
Property Test
```

补偿 Oracle 污染风险。

---

# 19. 第二个 FB 的最小可信验收包

当前第二个稍复杂 FB 建议最低完成：

```text
A. 5~10 个正式行为 Case
B. 每个 Expected 有来源标签
C. 至少 3 个 Mutation
D. 至少 2 条 Property / Invariant
E. 2~3 个 Hidden Cases
F. 正确 DUT 全部正式测试 PASS
G. 代表性 Mutation 大部分被 KILL
```

第一版不要求 Mutation Score 极高。

但如果：

```text
3 个 Mutation
0 个 KILLED
```

则不能认为测试具备可信抓错能力。

---

# 20. 当前建议的 MVP 验收状态

最终状态使用：

```text
TEST_HARNESS_VALIDATED
TEST_HARNESS_PARTIALLY_VALIDATED
TEST_HARNESS_NOT_VALIDATED
```

## TEST_HARNESS_VALIDATED

至少满足：

```text
[ ] Expected 来源可解释
[ ] 没有以当前实现输出作为主要 Oracle
[ ] 正确 FB PASS
[ ] 故意错误 Expected 能 FAIL
[ ] 至少多个有代表性 Mutation 被 KILL
[ ] Hidden Tests PASS
[ ] Property Tests PASS
```

## TEST_HARNESS_PARTIALLY_VALIDATED

例如：

```text
基本行为 PASS
Mutation 有部分 SURVIVED
Hidden Test 尚未完成
```

## TEST_HARNESS_NOT_VALIDATED

例如：

```text
Expected 主要来自当前实现
没有 Mutation Test
Mutation 全部 SURVIVED
错误 DUT 仍全部 PASS
```

---

# 21. Mutation Score 仅作为辅助指标

可以计算：

```text
Mutation Score
=
KILLED / (KILLED + SURVIVED)
```

例如：

```text
4 KILLED
1 SURVIVED

Mutation Score = 80%
```

但当前阶段不要机械追求 100%。

更重要的是：

> 关键业务错误类型是否能被抓住。

一个“核心 Reset 错误” SURVIVED，可能比十个无关 Mutation KILLED 更严重。

---

# 22. 防止 Mutation 本身无意义

Mutation 必须满足：

```text
1. 能构建 / 加载
2. 能进入真实 Runtime
3. 确实改变业务语义
4. 在当前 FB 场景下是合理可能出现的错误
```

以下不算高价值 Mutation：

```text
故意删掉整个类导致编译失败
故意制造 XML 语法错误
故意删除所有 Port
```

因为这种错误太容易被基础检查抓到，不能证明行为测试有效。

---

# 23. 测试冻结点

在 Mutation / Hidden Test 正式验真前，建立：

```text
TEST_FREEZE_COMMIT
```

记录：

```text
Test Runner Commit:
Test Cases Commit:
Expected Data Hash:
Target FB Baseline Commit:
```

Mutation 阶段不得偷偷改测试。

如果修改：

```text
必须重新建立 Freeze
```

---

# 24. 推荐执行顺序

第二个 FB 正确顺序：

```text
1. 确认真实 Runtime 路径
2. 写正式基础 Case
3. 记录 Expected 来源
4. 运行原始 FB → PASS
5. 冻结测试
6. 做 Mutation #1/#2/#3...
7. 运行冻结测试
8. 统计 KILLED / SURVIVED
9. 分析 SURVIVED 测试缺口
10. 补 Property
11. 执行 Hidden Tests
12. 最终判定 Harness 可信度
```

---

# 25. 最终报告模板

```text
FB_TEST_TRUST_REPORT

Target FB:
...

Runtime Authenticity:
PASS / FAIL

Formal Test Cases:
Total:
Pass:
Fail:

Expected Source Summary:
S1:
S2:
S3:
S4:
S5:
I1:

Mutation Results:
MUT-001: KILLED
MUT-002: KILLED
MUT-003: SURVIVED
...

Mutation Score:
...

Critical Mutations Survived:
...

Properties:
Total:
Pass:
Fail:

Hidden Tests:
Total:
Pass:
Fail:

Implementation-Derived Oracle Exists:
YES / NO

Known Oracle Contamination Risk:
...

Final Trust Status:
TEST_HARNESS_VALIDATED
/
TEST_HARNESS_PARTIALLY_VALIDATED
/
TEST_HARNESS_NOT_VALIDATED

Reason:
...
```

---

# 26. 一票否决条件

出现以下任意情况，不允许宣称“FB 测试已可信”：

```text
1. Expected 主要通过读取当前实现生成
2. 无法说明 Expected 来源
3. Mutation 后重新修改 Expected
4. 故意改坏 DUT 后测试仍全部 PASS，且未说明原因
5. Hidden Test 实际已提前泄露给 Builder
6. 测试只验证 Runner 会 ASSERT，不验证 DUT 错误能被抓住
7. 用当前 DUT 输出自动生成 Golden，再立即用该 Golden 证明 DUT 正确
```

---

# 27. 对当前项目最重要的区分

前一阶段已经证明的是：

```text
错误 Expected
→ 测试能够 FAIL
```

这证明：

> ASSERT 链是真的。

现在第二阶段必须证明：

```text
错误 DUT
→ 测试能够 FAIL
```

这才证明：

> 测试本身具有发现业务错误的能力。

两者不能混为一谈。

---

# 28. 最终原则

真正可信的 FB 测试不是：

```text
当前 FB
→ 当前测试
→ 全绿
```

而是：

```text
正确 FB
→ PASS

代表性错误 FB
→ FAIL

未知输入 / Hidden Case
→ 仍能正确判断

业务不变量
→ 始终成立
```

因此以后正式结论不要写：

> “FB 测试通过，所以 FB 正确。”

而应写：

> **“该 FB 在独立 Oracle、Mutation、Property 和 Hidden Test 的联合验证下通过；当前测试已证明具备一定的真实抓错能力。”**

这才是本项目中“FB 自动行为测试可信”的最低含义。
