> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 阶段2：AI 解释 MVP（外置 Skill）

## 1. 目标

在 Web 不调用模型 API 的前提下，完成：

```text
Web生成Task
→ 人在Harness运行Skill
→ Skill写Result
→ Web显示Result
```

## 2. MVP解释范围

对圈选区域输出：

1. 一句话作用；
2. 输入；
3. 按数据流排序的步骤；
4.每个图元做了什么；
5.输出；
6.与圈外对象的Incoming/Outgoing/Implicit联系；
7.基础代码引用；
8.专业版；
9.小白版；
10.不确定项和证据。

## 3. 不允许的表述

Web右侧叫：

```text
分析结果
数据流
代码关联
证据
```

不得叫：

```text
AI聊天
在线AI助手
问AI
```

因为Web只读取结果包。

## 4. Skill流程

```text
validate task
→ load selected scene
→ inspect boundary
→ query native properties
→ query code symbols
→ build ordered data flow
→ generate professional explanation
→ generate beginner explanation
→ attach focus_refs/evidence
→ validate result schema
```

## 5. Explain步骤

每一步必须有：

- `step_no`；
-相关Node IDs；
-相关Relation IDs；
-代码引用；
-输入；
-操作；
-输出；
-专业解释；
-小白解释；
-证据；
-置信度。

## 6. Web联动

点击分析步骤：

- 自动聚焦相关图元；
-高亮Relation；
-其他图元淡化；
-右侧显示证据；
-底部若有代码则跳转。

反向点击图元，也能定位相关步骤。

## 7. MVP代码关联

阶段2允许使用：

- 明确原生绑定；
-唯一符号名；
-基础文本搜索；
-局部代码上下文。

必须显示精度等级。深层跨函数数据流留给阶段3。

## 8. 验收样本

至少10个：

-简单链路；
-分支；
-有边界输入；
-有边界输出；
-Continuation；
-找不到代码；
-代码名字重复；
-存在UNKNOWN。

## 9. 质量门禁

- Result Schema 100%通过；
-每步至少一个 `focus_ref`；
-事实和推断分开；
-不引用未查询的代码；
-小白版不改变技术事实；
-没有Evidence的结论标UNKNOWN。
