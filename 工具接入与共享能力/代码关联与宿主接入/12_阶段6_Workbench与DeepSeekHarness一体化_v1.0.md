> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 阶段6：Workbench 与 DeepSeek Harness 一体化

## 1. 目标

消除人工：

```text
导出任务
→ 手工输入任务ID
→ 手工刷新结果
```

但保持前面所有数据契约不变。

## 2. 关键抽象

```text
AnalysisGateway
├── FileBundleAdapter
└── HarnessAdapter
```

Web只依赖Gateway，不依赖Harness内部类型。

## 3. 前期与后期映射

### 前期

```text
AnalysisRequest
→ 文件目录
→ 人触发Skill
→ Result文件
```

### 一体化后

```text
AnalysisRequest
→ JSON-RPC / Tool
→ Harness Session
→ Result Event
```

请求/结果Schema不变。

## 4. 集成职责

Harness Adapter负责：

-创建Session；
-提交Task；
-监听状态；
-取消；
-接收结果；
-保存审计日志；
-错误归一化。

Web仍不保存模型密钥；密钥和模型配置属于Harness运行环境。

## 5. 兼容性

DeepSeek Harness处于快速演进阶段，Adapter必须隔离：

-插件内部类型；
-事件协议；
-Session实现；
-模型Provider；
-Tool注册细节。

## 6. 测试

-同一任务在FileAdapter和HarnessAdapter结果Schema一致；
-断线重连；
-取消；
-Harness升级兼容测试；
-重复提交幂等；
-大结果流式/分块；
-权限边界；
-Web刷新后恢复任务状态。

## 7. 进入条件

只有阶段2-5稳定后进入。不得为了“体验像一体化产品”提前耦合。
