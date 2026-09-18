# Project Instructions：BEH 图源与代码分析工作台

## 1. 项目目标

先做成一个准确、可测试、不会在大工程中卡死的 **图源解释工作台**；在解释能力稳定后，再做 AI 开发图元和 C/C++ 代码的能力。

## 2. 当前权威架构

```text
原始 BEH JRE + JAR
→ Headless Full Scene Service
→ NativeSceneBundle
→ 本地 Web Workbench
→ AnalysisTaskBundle
→ 外置 Harness Skill
→ AnalysisResultBundle
→ Web 结果查看与联动
```

前期 Web 不直接接模型 API。

## 3. 进入任务前必须做

1. 读取 `00_START_HERE`。
2. 读取 `00_Current/02_术语_事实源与信任边界_v1.0.md`。
3. 读取 `00_Current/02A_按事实域划分的证据可信度矩阵_v1.0.md`。
4. 读取当前阶段文档。
5. 读取与本任务相关的数据契约。
6. 读取对应测试计划。
7. 查看当前代码、运行脚本、现有测试和实际页面。
8. 明确本轮只修改哪一层，禁止无边界跨层重构。

## 4. 开发顺序

```text
解释
→ 解释准确性
→ 图元/代码候选开发
→ 原生应用
→ Harness一体化
→ 精雕细琢
```

不得倒序。

## 5. UI 完成标准

涉及 Web 的任何功能，必须：

- 启动实际页面；
- 检查页面不是空壳；
- 检查 Console；
- 使用 Playwright 操作真实控件；
- 验证操作前后状态；
- 保存截图或 DOM/SVG 证据。

仅 `build/typecheck/unit test` 通过不得宣称 UI 完成。

## 6. 模型使用规则

DeepSeek V4 Flash、GLM-5.2 和小视觉模型的能力以公司环境实测为准。

- 模型不读完整大 XML；通过工具查询。
- 模型不做精确 ID 比较；固定程序比较。
- 模型不直接改正式 Graph；只能生成 Proposal。
- 模型结论必须标注 `FACT / INFERENCE / HYPOTHESIS / UNKNOWN / CONFLICT`。
- 小视觉模型只处理局部草图或局部定位，不负责理解完整 PLC 图。
- 模型不得把低等级证据包装成高等级事实。
- 证据版本不一致时必须先标记 `VERSION_MISMATCH`，不得直接覆盖。

## 7. 证据规则

### 7.1 先判断事实域

任何最终 Edge、代码绑定、分析步骤和 Proposal 必须带 Evidence 引用。

发生冲突时禁止直接套一个全局排行榜。必须先写出：

```text
Claim
Fact Domain
Evidence
Version Context
Conclusion Status
```

事实域至少包括：

```text
BEH_RUNTIME_GRAPHICS
CPP_SOURCE_BUILD
SCENE_CODE_BINDING
USER_SELECTION_INTENT
WEB_RUNTIME_INTERACTION
```

具体优先级遵守：

```text
00_Current/02A_按事实域划分的证据可信度矩阵_v1.0.md
```

### 7.2 Evidence 分类

每个关键 Evidence 应尽量标记：

```text
evidence_class:
RAW_SOURCE
DETERMINISTIC_DERIVED
STATIC_INFERENCE
HEURISTIC
MODEL_INFERENCE
```

### 7.3 不同事实域的核心底线

- BEH 运行/图形事实：原始 JAR 实际行为优先于 CFR 和模型推理。
- C/C++ 代码事实：真实源码 + 对应构建上下文优先于分析工具摘要和模型推理。
- Scene-Code Binding：直接原生绑定/生成映射优先于名称匹配和数据流推断。
- 用户圈选：稳定 hit-map 的几何命中属于确定性事实；自由笔语义可为 UNKNOWN。
- Web 运行事实：真实页面 + Playwright 优先于 build/typecheck。

没有足够证据的关系不得升级为 VERIFIED。

## 8. CFR / 反编译代码规则

CFR 等反编译输出统一称为：

```text
Recovered Java Reference
```

用途是理解、定位和设计 Bridge。

禁止：

- 称为原始 Java 源码；
- 重新编译后替代原始 JAR 作为权威运行物；
- 当 CFR 与原始 JAR 实际行为冲突时，以 CFR 覆盖运行事实。

关键反编译结论存在疑问时，应升级验证到：

```text
javap / ASM / bytecode
或
原始 JAR 可复现实验
```

## 9. 禁止行为

- 根据用户一句观察直接添加特殊 `if`。
- 因为输出“多一根线”就静默去重。
- 让 Renderer 自己补线。
- 为了让测试通过而修改测试真值。
- 将 CFR 反编译结果称为原始源码。
- 将公开 PLC 标准强行套到 BEH 私有 XML。
- 在阶段入口条件未满足时提前开发后续功能。
- 将不同事实域的证据错误地放入同一优先级比较。
- 将 Clang、Tree-sitter、ripgrep、CFR 和 AI 输出全部笼统视为同级“工具结果”。

## 10. 每轮交付格式

必须报告：

1. 本轮目标；
2. 修改范围；
3. 根因或设计依据；
4. 涉及的 Fact Domain；
5. 关键 Evidence 与等级；
6. 文件清单；
7. 测试清单；
8. Playwright 结果（若涉及 Web）；
9. 已知限制；
10. 当前阶段是否真正通过；
11. 下一步唯一建议。

## 11. 失败处理

失败不是隐藏或模糊表述。使用：

```text
PASS
FAIL
BLOCKED
UNRESOLVED
NOT_TESTED
CONFLICT
VERSION_MISMATCH
```

并附证据。
