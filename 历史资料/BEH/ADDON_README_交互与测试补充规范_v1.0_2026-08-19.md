# BEH 交互与测试补充规范包

**版本：** v1.0  
**日期：** 2026-08-19  
**性质：** 只新增，不修改既有文档

## 1. 使用方式

本补充包用于解决近期真实人工测试暴露出的 Web 交互与原生视觉保真问题。

本包不替代已有项目文档，也不要求重新阅读全部项目资料。

开发模型在继续阶段1相关 Web 开发前，应额外读取本包中的新增文档。

## 2. 当前已暴露的典型问题

1. Playwright 全绿，但矩形框选行为与真实用户预期不一致；
2. Dock 可以收起，但没有完整展开路径；
3. 画布缺少 Pan / Zoom，简单图与复杂图显示比例失控；
4. 原生 BEH 明确存在 Arrow，但当前 Web 中看不到；
5. 现有测试更像 Feature Checklist，缺少连续交互轨迹、状态机闭环和 Human Acceptance Golden。

## 3. 新增文档

```text
40_UI/28_Web画布交互行为契约_v1.0.md

20_Testing/29_HumanAcceptanceGolden与TestOracle规范_v1.0.md
20_Testing/30_Playwright连续交互_状态机与Viewport测试规范_v1.0.md
20_Testing/31_NativeScene视觉保真与Arrow_Port_Relation验收规范_v1.0.md
20_Testing/32_当前交互缺陷_HumanGolden验收案例_v1.0.md
```

## 4. 推荐阅读顺序

```text
28
↓
29
↓
30
↓
31
↓
32
```

## 5. 最高原则

> 不再只测试“功能有没有”，而要测试“用户真实怎么操作、过程怎么变化、最终是否符合人类确认的行为”。

对于当前阶段，Human Acceptance Golden 是后续自动化测试的 Oracle 来源之一。
