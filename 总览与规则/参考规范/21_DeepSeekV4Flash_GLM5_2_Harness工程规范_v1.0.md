> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# DeepSeek V4 Flash、GLM-5.2 与 DeepSeek Harness 工程规范

## 1. 目标

让项目在公司实际可用模型能力下稳定工作，而不是假设模型能够：

- 直接理解几十 MB XML；
- 浏览完整代码仓；
- 精确比较ID；
- 自动操作正式工程；
- 一次性长期自主完成所有阶段。

## 2. 模型定位

### DeepSeek V4 Flash / GLM-5.2

作为：

- 结构化上下文理解器；
- 工具调用规划器；
- 代码解释与候选生成器；
-有限步骤Agent。

不作为：

- 数据库；
-图算法引擎；
-精确验证器；
-正式修改器；
-复杂画布视觉真值源。

### 小视觉模型

仅用于：

- 自由草图局部理解；
-局部视觉定位；
-无法从结构数据得到的图形提示。

正式BEH图元无需视觉模型识别，因为Native Scene提供ID和结构。

## 3. Harness定位

DeepSeek Harness作为可替换Agent运行层：

- Plugin；
-Tool；
-Service；
-Session；
-任务编排。

项目核心不能存于Harness内部。Harness仍应通过 `AnalysisGateway/HarnessAdapter` 接入。

## 4. Tool-first

模型需要事实时调用工具：

```text
get_selection_context
get_native_object
get_neighbors
get_boundary_context
find_symbol
get_code_range
get_callers
trace_data_flow
```

不得把全部数据预塞入Prompt。

## 5. Tool设计

- 单一职责；
-参数少；
-使用ID/枚举；
-输出固定JSON；
-明确错误码；
-可取消；
-默认只读；
-返回Evidence ID；
-限制响应大小。

禁止巨型工具：

```text
analyze_and_fix_everything
```

## 6. Agent状态机

Explain：

```text
VALIDATE_TASK
→ LOAD_SELECTION
→ INSPECT_BOUNDARY
→ QUERY_PROPERTIES
→ QUERY_CODE
→ BUILD_FLOW
→ WRITE_RESULT
→ VALIDATE_RESULT
```

Compose：

```text
VALIDATE_INTENT
→ LOAD_CONTEXT
→ QUERY_COMPONENTS
→ PROPOSE_GRAPH
→ VALIDATE_GRAPH
→ PROPOSE_CODE
→ VALIDATE_PATCH
→ WRITE_PROPOSAL
```

模型不得跳过关键阶段。

## 7. 输出约束

所有机器消费输出必须JSON Schema验证。自然语言报告从结构化结果渲染。

## 8. Claim状态

```text
FACT
INFERENCE
HYPOTHESIS
UNKNOWN
```

不得把“模型看起来认为”写成事实。

## 9. 上下文控制

每个请求只给当前选择和相关代码证据。即使模型支持长上下文，也不将长上下文作为索引器替代品。

## 10. 重试与停止

每任务设置：

- max steps；
-max tool calls；
-timeout；
-max evidence bytes；
-max retries。

超过返回PARTIAL/UNRESOLVED，不无限循环。

## 11. 模型可替换

Skill和Tool契约不出现特定模型字段。模型配置属于运行环境。相同Task应能用V4 Flash或GLM-5.2执行并产生同Schema结果。

## 12. 回归

记录：

```text
model
provider
prompt_version
skill_version
tool_versions
task_hash
result_hash
```

对模型/Prompt升级运行Golden分析集。

## 13. Harness兼容风险

Harness更新可能发生不兼容变化。要求：

-锁定验证版本；
-Adapter隔离；
-升级前跑契约测试；
-保留FileBundleAdapter；
-业务服务可脱离Harness单独测试。
