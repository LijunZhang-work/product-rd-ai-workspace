> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 模型任务 SOP 与输出 Schema 执行规范

## 1. 通用SOP

每个模型任务必须：

```text
Load
→ Validate
→ Plan
→ Query
→ Synthesize
→ Self-check
→ Schema Validate
→ Write
```

## 2. 任务边界

模型收到：

- 当前Task；
-允许的工具；
-预算；
-输出Schema；
-禁止事项。

不得自行扩展工作区或读取未授权目录。

## 3. Tool调用纪律

- 一次解决一个问题；
-先结构查询，后文本读取；
-优先ID定位；
-限制返回数量；
-分页；
-记录Evidence；
-工具失败显式处理。

## 4. 自检清单

Explain：

```text
[ ] 每步有focus refs
[ ] 顺序来自Relation/证据
[ ] 代码引用真实查询
[ ] 专业/小白事实一致
[ ] 边界联系已列
[ ] UNKNOWN保留
```

Compose：

```text
[ ] 只用Verified Component
[ ] 操作不生成最终native ID
[ ] 不直接写repo
[ ] 影响范围完整
[ ] 验证计划存在
```

## 5. Schema失败

最多执行有限次修复。仍失败：

```text
FAILED_SCHEMA
```

不得输出非结构化结果冒充成功。

## 6. 结果长度

长证据存Evidence文件，Result只引用。避免单个JSON过大。

## 7. Prompt版本

```text
BEH_ANALYSIS_SOP_v1
BEH_COMPOSE_SOP_v1
```

版本写入Result。修改Prompt须跑Golden。
