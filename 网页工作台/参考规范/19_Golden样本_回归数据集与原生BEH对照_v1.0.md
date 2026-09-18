> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Golden 样本、回归数据集与原生 BEH 对照

## 1. 目标

让系统修复一次后不再反复犯同类错误。

Golden不是“让算法背答案”，而是独立真值和回归门禁。

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

用户观察可成为真值，但必须说明可重复步骤；不得转化为具体ID硬编码规则。

## 5. 回归要求

修改Relation/Selection/Binding逻辑时：

- 当前失败样本；
-同结构正例；
-相似反例；
-全部历史Golden；

必须通过。

## 6. 防止自证循环

生成器和验证器不能共享同一核心规则作为唯一真值。至少保留：

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
