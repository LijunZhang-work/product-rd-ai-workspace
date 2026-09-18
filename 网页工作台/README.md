# 网页工作台

需要 CodeQL、Clang、Bear、源码索引或运行观测等共享工具时，统一读取[工具指南](../工具接入与共享能力/工具统一管理与使用指南.md)和[当前状态报告](../工具接入与共享能力/工具状态与验收报告.md)。本模块只补充任务场景与结果要求；已有有效环境可复用，本次执行仍需留证。项目随附 README 和历史实测资料保留其版本复现用途，不作为另一份当前机器工具台账。

统一网页交互、圈选、过程回看及开发审核入口。

这里维护我们自己的网页入口、画布和交互。工作台自身的 Playwright 验收与被测产品网页的人工路径测试分别报告。Trace 作为网页证据入口，跨设备记录通过任务索引关联。

## 已归档资料

- [00_网页工作台_模块入口.md](00_网页工作台_模块入口.md)
- [历史参考图/BEH分析器动态数据流仪表盘.png](历史参考图/BEH分析器动态数据流仪表盘.png)
- [历史参考图/BEH AI 工坊：车辆控制数据流联动.png](历史参考图/BEH%20AI%20工坊：车辆控制数据流联动.png)
- [历史参考图/BEH人机协同平台架构总览.png](历史参考图/BEH人机协同平台架构总览.png)
- [参考规范/32_当前交互缺陷_HumanGolden验收案例_v1.0.md](参考规范/32_当前交互缺陷_HumanGolden验收案例_v1.0.md)
- [参考规范/31_NativeScene视觉保真与Arrow_Port_Relation验收规范_v1.0.md](参考规范/31_NativeScene视觉保真与Arrow_Port_Relation验收规范_v1.0.md)
- [参考规范/30_Playwright连续交互_状态机与Viewport测试规范_v1.0.md](参考规范/30_Playwright连续交互_状态机与Viewport测试规范_v1.0.md)
- [参考规范/29_HumanAcceptanceGolden与TestOracle规范_v1.0.md](参考规范/29_HumanAcceptanceGolden与TestOracle规范_v1.0.md)
- [参考规范/28_Web画布交互行为契约_v1.0.md](参考规范/28_Web画布交互行为契约_v1.0.md)
- [参考规范/26_Web信息架构与画布优先交互设计_v1.0.md](参考规范/26_Web信息架构与画布优先交互设计_v1.0.md)
- [参考规范/19_Golden样本_回归数据集与原生BEH对照_v1.0.md](参考规范/19_Golden样本_回归数据集与原生BEH对照_v1.0.md)
- [参考规范/18_Playwright端到端测试设计_v1.0.md](参考规范/18_Playwright端到端测试设计_v1.0.md)
- [参考规范/14_Selection_Annotation_Intent数据契约_v1.0.md](参考规范/14_Selection_Annotation_Intent数据契约_v1.0.md)
- [参考规范/07_阶段1_Web查看圈选与任务导出MVP_v1.0.md](参考规范/07_阶段1_Web查看圈选与任务导出MVP_v1.0.md)

[返回工作区入口](../README.md)

## 验收策略的版本区别

上面的 v1.0 Human Golden 文档保留为人工验收参考。[自动化验收补充 v1.1](参考规范/自动化验收补充_v1.1/ADDON_README.md) 已从原包展开，使用确定性 Fixture、Oracle 与自动化验证，其自身声明“只新增”。两套策略不相互冒充；按实际任务约定选择，引用时标明版本。文件名版本更高不代表自动覆盖全部原方案。
