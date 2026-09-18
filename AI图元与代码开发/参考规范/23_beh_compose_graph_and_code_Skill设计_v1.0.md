> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# `beh-compose-graph-and-code` Skill 设计

## 1. 定位

在解释能力稳定后，根据Intent生成候选方案。只输出Proposal，不直接应用。

## 2. 输入

-当前Scene；
-Selection/Target Region；
-用户文字；
-结构化Annotation；
-自由手绘原始数据及可选视觉解释；
-附近Port；
-Verified Component Registry；
-代码索引；
-必须保持的现有行为。

## 3. 工作流

```text
validate intent
→ identify target behavior
→ inspect current graph
→ inspect code bindings
→ select verified components
→ propose graph ops
→ validate ports/scope
→ propose code patch
→ analyze impact
→ write validation plan
→ validate proposal schema
```

## 4. 组件选择

只能自动使用：

```text
VERIFIED_COMPONENT
```

未知组件只能提出“需要人工选择”，不能自行虚构native type。

## 5. Graph Operations

模型不生成最终ID、relation_id或隐藏字段。使用临时Proposal ID。

## 6. 代码补丁

- 基于当前commit/hash；
-限制文件；
-保留现有风格；
-不要无关重构；
-说明每个改动对应哪个Graph Operation；
-生成测试建议；
-不直接执行提交。

## 7. 草图理解

### 结构化Annotation

可直接使用。

### Freehand

默认只作为区域/强调。若视觉模型输出候选语义，必须标INFERENCE并允许人工确认。

## 8. 影响分析

至少：

-图元；
-Relation；
-圈外输入输出；
-代码文件；
-公共接口；
-测试；
-回滚；
-未知。

## 9. Proposal Review

每项Operation可：

```text
ACCEPT
REJECT
EDIT
```

接受局部操作时必须重新验证依赖。

## 10. 安全

Skill工具默认只读。写Patch只能写入Proposal输出目录，不得直接改repo。

## 11. MVP验收

最小低频告警链：

```text
Compare → TON → Output
```

输出Graph Proposal和C/C++ Patch，Schema/静态校验通过，正式工程保持不变。
