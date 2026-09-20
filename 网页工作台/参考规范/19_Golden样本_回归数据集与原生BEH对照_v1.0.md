> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Golden 样本、回归数据集与原生 BEH 对照

## 1. 目标

让系统修复一次后不再反复犯同类错误。

Golden 是带来源与用途的回归基线。原工具结构/显示兼容样本、实现行为快照和独立业务正确性断言分别管理；不是所有 Golden 都具有独立真值资格。

## 2. Golden层级

### Native Scene Golden

来源：

- 原始JAR Headless输出；
-原生BEH人工对照；
-固定JAR/XML Hash。

记录：

- Node；
-Port；
-Relation；
-Path；
-Arrow；
-Display Text；
-Properties。

### Selection Golden

给定圈选几何，固定命中：

- selected；
-boundary；
-external。

### Analysis Golden

固定Task输入与人工审核的期望结果：

-步骤；
-focus refs；
-evidence；
-允许UNKNOWN。

### Code Binding Golden

小型可编译C/C++仓：

-唯一符号；
-同名符号；
-宏；
-调用；
-def-use。

### Proposal Golden

固定Intent，检查Operation Schema和约束，不要求模型每次文字完全相同。

## 3. 必备场景

1. 两Node一Relation；
2. 一Node多出边；
3. 多入边；
4. 同一A/B之间不同Port多线；
5. 不同relation映射相同粗拓扑；
6. Continuation/Connector；
7. 相同显示名称不同ID；
8. 跨Scope；
9. 画布边界输入输出；
10.未知对象；
11.无代码绑定；
12.同名C变量；
13.宏条件；
14.大POU。

## 4. 真值来源

每个Golden记录：

```text
truth_source
verified_by
verification_date
jar_hash
xml_hash
repo_commit
notes
```

用户观察可作为带来源的证据，记录可重复步骤、版本及其证明范围；不得转化为具体 ID 硬编码规则。原始 JAR 与同源 Headless/GUI 的一致不等于独立业务正确性验证。每份样本补充用途、预期依据、已知缺陷、观测时刻/模式及适用范围；按[BEH 已知问题](../../工具接入与共享能力/BEH原生能力/BEH已知问题与观测适用边界.md)处理受影响观测。

## 5. 回归要求

修改Relation/Selection/Binding逻辑时：

- 当前失败样本；
-同结构正例；
-相似反例；
-全部历史Golden；

必须通过。

## 6. 防止自证循环

生成器和验证器不能共享同一核心规则作为唯一业务正确性依据。下面来源按所证明的事实选择并标记相关性；同源的 JAR 与 GUI 不是独立证据。已知缺陷可保留为缺陷回归样本，不作为业务正确标准：

-原始JAR；
-原生BEH人工对照；
-独立Fixture；
-手工标注；
-不同实现交叉检查。

## 7. 差异审查

Golden变化必须生成Diff：

-新增/删除对象；
-ID变化；
-路径变化；
-文本变化；
-选择变化；
-解释Focus变化。

未经批准不得自动更新Baseline。
