# BEH 交互与测试补充规范包

**版本：** v1.1  
**日期：** 2026-08-19  
**性质：** 只新增，不修改既有文档  
**当前策略：** 自动化优先，当前阶段不引入人工验收流程

## 1. 使用方式

本补充包用于解决近期真实运行中暴露出的 Web 交互与原生视觉保真问题。

本包不替代已有项目文档，也不修改已有项目文档。

当前阶段的正确性来源于：

```text
明确的交互行为契约
+
确定性 Golden Fixture
+
结构化 Test Oracle
+
Playwright 真实浏览器验证
+
Native Scene / SVG / HitMap 一致性验证
```

不把人工确认作为阶段门禁。

## 2. 当前重点问题

1. Playwright 显示通过，但矩形框选行为不满足交互契约；
2. Dock 可以收起，但缺少完整展开路径；
3. 画布缺少 Pan / Zoom，导致不同复杂度场景显示比例失控；
4. 原生 BEH 存在 Arrow，但当前 Web 中未显示；
5. 现有测试偏 Feature Checklist，需要升级为连续交互、状态机和确定性 Golden 回归。

## 3. 新增文档

```text
40_UI/28_Web画布交互行为契约_v1.0.md

20_Testing/29_确定性AcceptanceGolden与TestOracle规范_v1.1.md
20_Testing/30_Playwright连续交互_状态机与Viewport测试规范_v1.0.md
20_Testing/31_NativeScene视觉保真与Arrow_Port_Relation验收规范_v1.1.md
20_Testing/32_当前交互缺陷_自动化Golden回归案例_v1.1.md
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

> 不再只测试“功能有没有”，而要通过明确行为契约和确定性 Oracle，验证用户真实操作轨迹与最终结果。

当前阶段不依赖人工验收；如果自动化测试缺少可靠 Oracle，应先补充契约或 Fixture，而不是让实现自行定义 expected。
