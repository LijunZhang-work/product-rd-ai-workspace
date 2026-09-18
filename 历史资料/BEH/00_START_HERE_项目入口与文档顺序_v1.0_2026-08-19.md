# BEH 图源与代码分析工作台：项目入口与文档顺序

**版本：** v1.0  
**日期：** 2026-08-19  
**状态：** 当前权威入口

## 1. 项目一句话定义

本项目使用 **BEH 原始 JRE + JAR 的 Headless Full Scene 能力**作为图形事实源，在本地 Web 工作台中提供画布查看、矩形/椭圆/自由套索圈选、手绘标注、任务导出、分析结果查看和代码联动；初期由外置 DeepSeek Harness Skill 完成 AI 分析，后期再接入一体化运行。

## 2. 已确认的事实

1. BEH 的 JRE + JAR 可以在无 GUI 环境运行。
2. 可以解析 POU XML。
3. Headless Full Scene 可行。
4. JCanvas 无法作为 Headless 组件实例化。
5. JCanvas 原生交互、选择和 Hit Test 不作为本项目依赖。
6. Web 端根据 Headless 导出的 `scene.svg + scene.json + hit-map.json` 实现点击、圈选和手绘。
7. BEH XML 主要按厂商私有格式处理；IEC 61131-3 只作为 PLC 语义参考。
8. Web 在前期 **不调用任何模型 API**。右侧区域是“分析结果查看器”，不是 AI 聊天窗口。

## 3. 主线顺序

必须按以下顺序推进：

```text
阶段0：固化原生 Headless 场景契约
↓
阶段1：完成 Web 查看、圈选、导出 MVP
↓
阶段2：完成外置 Skill 的 AI 解释 MVP
↓
阶段3：提升代码仓关联和解释准确性
↓
阶段4：生成图元与 C/C++ 修改候选
↓
阶段5：安全应用到原生 BEH 并做 Round-trip
↓
阶段6：再把 Workbench 与 DeepSeek Harness 一体化
↓
最后：精雕细琢、复杂草图理解、语义视图和高级体验
```

不得在 Explain MVP 尚未通过时提前投入正式图元写入。

## 4. 文件夹说明

- `00_Current/`：当前权威产品与阶段文档。
- `10_Contracts/`：跨模块数据契约；实现不得私自改字段含义。
- `20_Testing/`：测试策略、Playwright、Golden 数据和性能门禁。
- `30_Model_and_Skill/`：模型、Harness、Skill 和证据规范。
- `40_UI/`：Web 画布、折叠面板和交互设计。
- `90_Later_Polish/`：明确后置的精雕细琢工作。
- `99_Archive/`：失效文档归档；不得作为当前开发依据。

## 5. 推荐阅读顺序

开发模型第一次进入项目时：

```text
本文件
→ PROJECT_INSTRUCTIONS
→ 00_Current/01 项目章程
→ 00_Current/02 术语与事实源
→ 00_Current/02A 按事实域划分的证据可信度矩阵
→ 00_Current/03 总体架构
→ 00_Current/05 总路线图
→ 30_Model_and_Skill/24 证据优先原则
→ 30_Model_and_Skill/25 模型任务SOP与输出Schema
→ 当前阶段文档
→ 对应测试文档
```

## 6. 完成的定义

“代码已写”“构建通过”“文档已生成”都不等于阶段完成。阶段完成必须同时具备：

- 可运行产物；
- 自动测试；
- Playwright 运行态验证（涉及 Web 时）；
- 实际截图或结构证据；
- 明确的 PASS/FAIL 表；
- 已知限制；
- 下一阶段进入条件全部满足。

## 7. 证据冲突处理：禁止使用单一全局排行榜

任何证据冲突，必须先回答：

> **当前究竟在证明哪一类事实？**

固定流程：

```text
Claim
↓
识别 Fact Domain
↓
核对版本 / Hash / Build Profile
↓
按该事实域内部的证据优先级排序
↓
FACT / INFERENCE / HYPOTHESIS / UNKNOWN / CONFLICT
```

主要事实域：

```text
A. BEH 运行、模型与图形事实
B. C/C++ 代码与构建语义事实
C. BEH 图元 ↔ C/C++ 代码绑定事实
D. 用户圈选、标注与手绘意图
E. Web / Workbench 运行与交互事实
```

具体矩阵以：

```text
00_Current/02A_按事实域划分的证据可信度矩阵_v1.0.md
```

为权威细则。

### 7.1 总体底线

- BEH 行为问题：原始 JAR 的实际运行行为优先于 CFR / AI 推理。
- C/C++ 源码问题：当前真实代码仓源码与对应构建上下文优先于工具摘要和 AI 推理。
- 图元与代码绑定：优先原生直接绑定和生成映射，不得只凭同名字符串确认。
- 用户选择：矩形/椭圆/Lasso 的确定性命中优先于模型视觉猜测。
- 自由笔语义：没有用户文字或视觉证据时允许 UNKNOWN。
- Web 是否真的可用：实际页面行为与 Playwright 证据优先于 build/typecheck 和 AI 判断。

### 7.2 CFR 的位置

```text
Original JAR / bytecode
= 运行与 class 事实

CFR Output
= Recovered Java Reference，仅供理解和定位
```

不得称 CFR 输出为“原始源码”，不得以重新编译 CFR 输出替代原始 JAR。

## 8. 当前最重要的红线

- 不重新实现第二套“权威 BEH Renderer”。
- 不让 Web 或 AI 猜 Relation、Port、箭头和显示名称。
- 不把用户观察直接硬编码成规则。
- 不静默去重、静默删线或为通过样本修改 expected。
- 不把几十 MB XML 或整个代码仓直接塞进模型上下文。
- 不在 MVP 前投入高级动画、主题精修和复杂草图识别。
- 不跨事实域错误套用证据优先级。
- 不把 CFR、clangd、Tree-sitter、ripgrep、AI 推理统称为同一可信等级的“工具结果”。
