> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 阶段5：原生应用、Round-trip 与安全提交

## 1. 目标

把阶段4的Proposal安全应用到真实工程，并证明：

```text
预期模型
≈
BEH保存后重新加载的模型
```

## 2. 应用优先级

### 首选：原生 BEH Operation/Writer

复用原始JAR：

-创建Node；
-设置参数；
-连接；
-分配ID；
-维护隐藏字段；
-保存；
-生成附属代码。

### 兜底：Native Template + Minimal Patch

只有原生操作无法覆盖时使用。禁止全量重写未知XML。

## 3. 事务流程

```text
create transaction
→ apply proposal to shadow/native model
→ validate
→ render preview
→ user approve
→ commit
→ save
→ reload
→ export scene/model
→ compare
```

任一步失败必须回滚。

## 4. Round-trip比较

至少比较：

- Node identity/type；
-Port；
-Relation identity；
-端点；
-参数；
-Geometry；
-显示文本；
-附属代码；
-诊断；
-代码构建结果。

## 5. C/C++代码提交

代码补丁须：

-限制文件范围；
-应用到临时worktree；
-格式检查；
-静态检查；
-编译；
-单元/集成测试；
-展示diff；
-人工确认。

## 6. 结果

```text
PASS
MISMATCH
ROLLED_BACK
UNRESOLVED
```

不得用“看起来一样”作为通过依据。
