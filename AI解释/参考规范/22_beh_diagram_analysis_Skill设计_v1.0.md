> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# `beh-diagram-analysis` Skill 设计

## 1. 职责

读取 AnalysisTaskBundle，结合 Native Scene 和代码工具，生成可审计的 AnalysisResultBundle。

不负责：

-修改正式Graph；
-修改代码；
-写BEH XML；
-猜未知Relation；
-操作Web UI。

## 2. 输入

- manifest；
-workspace refs；
-selection；
-annotations；
-user intent；
-selected subgraph；
-boundary；
-native properties；
-code access；
-diagnostics。

## 3. 工作流

### Step 1：验证

- Schema；
-Hash；
-路径权限；
-Canvas/ID存在；
-诊断是否允许继续。

### Step 2：理解选择

区分：

-正式选中对象；
-边界对象；
-结构化标注；
-自由笔；
-用户文字。

### Step 3：识别数据流入口

查：

-入边；
-输入Port；
-外部Node；
-变量/函数绑定。

### Step 4：按原生Relation排序

生成候选顺序。遇到分支则输出分支结构，不强行线性化。

### Step 5：逐元素解释

每步回答：

```text
输入是什么
当前元素做什么
参数是什么
输出如何变化
流向哪里
```

### Step 6：代码查询

按需调用：

- definition；
-reference；
-code range；
-callers/callees；
-data-flow。

### Step 7：边界联系

列出：

- incoming；
-outgoing；
-implicit；
-code external calls。

### Step 8：双版本解释

专业版使用准确术语。小白版使用比喻，但必须和专业版共享同一结构化事实。

### Step 9：Evidence和UNKNOWN

任何证据不足结论标UNKNOWN。

### Step 10：Result Schema验证

失败不得写出“成功结果”。

## 4. 输出步骤要求

每步：

- focus refs；
-输入；
-operation；
-output；
-code refs；
-professional；
-beginner；
-evidence；
-claim status；
-confidence。

## 5. 小白版规则

- 先建立直觉；
-不把比喻当科学/工程事实；
-明确“像什么”，不说“就是”；
-保留关键阈值、时间、方向和条件；
-不省略风险/未知。

## 6. 代码工具纪律

-先查定义；
-再查引用；
-只读取必要范围；
-记录工具返回Evidence；
-同名符号必须消歧；
-缺少compile commands时降低等级；
-不得根据文件名猜函数行为。

## 7. 失败模式

```text
INVALID_TASK
MISSING_SCENE_OBJECT
CODE_INDEX_UNAVAILABLE
AMBIGUOUS_BINDING
PARTIAL_ANALYSIS
UNRESOLVED_FLOW
```

## 8. MVP验收

至少10个Golden Task。人工评价：

-对象是否讲对；
-顺序是否讲对；
-边界是否讲对；
-代码是否引用正确；
-小白版是否没有歪曲；
-UNKNOWN是否诚实。
