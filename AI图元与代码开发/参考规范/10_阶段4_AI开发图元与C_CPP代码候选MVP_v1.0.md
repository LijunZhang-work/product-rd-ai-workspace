> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 阶段4：AI 开发图元与 C/C++ 代码候选 MVP

## 1. 前提

必须先通过：

- Explain MVP；
-代码关联准确性；
-Graph/Code Evidence；
-Proposal Schema；
-阶段测试门禁。

## 2. 目标

用户通过：

```text
指定区域
+
自然语言
+
结构化箭头/文字
+
可选自由草图
```

获得：

```text
ProposalGraphOperations
+
CodePatchProposal
+
ImpactReport
+
ValidationPlan
```

不直接改正式工程。

## 3. 首个MVP只支持

- 创建少量已验证图元类型；
-设置基础参数；
-连接明确Port；
-移动候选；
-修改少量C/C++文件；
-展示diff；
-静态验证。

不支持：

- 任意未知图元；
-直接生成Relation ID；
-修改隐藏字段；
-自动提交；
-大规模重构；
-复杂自由草图自动解释。

## 4. 生成顺序

```text
理解Intent
→ 查询可用Component Registry
→ 查询当前Scope和附近Port
→ 生成Graph Operations
→ Graph静态验证
→ 生成CodePatch
→ 编译/测试计划
→ 输出Proposal
```

## 5. UI

Proposal单独一层：

-半透明；
-虚线；
-明确“未应用”；
-可逐项接受/拒绝；
-展示影响的圈外对象和代码文件。

## 6. 安全门禁

- 只使用Verified Component；
-未知Port禁止连接；
-新增Edge必须有来源/目标；
-代码补丁不得越出工作区；
-没有构建验证不得标“可提交”；
-模型不得直接写任务外文件。

## 7. 验收

最小闭环：

```text
Compare → TON → Output
+
对应一处C/C++逻辑
```

能够生成Proposal、通过Schema、展示Diff、运行静态检查，但不正式应用。
