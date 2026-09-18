> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../../README.md)。资料归档不代表产品功能或实机验证已经完成。

# 阶段0：原生 Headless 场景底座固化

## 1. 已知前提

- JRE + JAR 可 Headless 运行；
- POU XML 可解析；
- Headless Full Scene 完全可行；
- JCanvas实例化不可行；
- JCanvas交互、选择、Hit Test不适用。

本阶段不再验证“可不可行”，而是把可行能力产品化。

## 2. MVP目标

提供稳定接口：

```text
listCanvases(workspace)
renderScene(canvasId)
getObject(nativeId)
getProperties(nativeIds)
validateScene(canvasId)
```

输出：

```text
NativeSceneBundle
```

## 3. 必须包含

- 完整 `scene.svg`；
- Node/Port/Relation/Arrow；
- 显示名称和内部名称；
- Native ID；
-路径和几何；
- hit shape；
-原生属性引用；
-诊断；
-版本和Hash。

## 4. 不允许

- Web补画缺失Edge；
- AI推导Relation；
- 使用CFR源码重编译替代原JAR；
- 以坐标最近规则绑定Native ID；
- diagnostics为空时静默忽略未渲染对象。

## 5. Hit Map

因为JCanvas Hit Test不可用，Exporter必须输出足够几何：

- Node bounds/path；
- Port中心和半径；
- Relation path和点击容差；
- Label bounds；
- z-order。

Web选择逻辑必须独立测试。

## 6. 缓存键

```text
JAR_SHA256
XML_SHA256
Canvas_ID
Exporter_Version
Render_Profile
```

## 7. Golden样本

至少：

1. 两节点一线；
2. 一输出多分支；
3. 多输入；
4. Connector/Continuation；
5. 折线和箭头；
6. 多个相同显示符号但不同Native ID；
7. 大画布。

## 8. 测试

- Schema Contract Test；
- 原生对象计数；
- ID唯一性；
- Relation端点；
- Arrow方向；
- SVG data-native-id；
- Scene JSON与SVG对象一致；
- Headless重复输出确定性；
- 无GUI环境运行；
- Cache命中/失效。

## 9. 完成门禁

```text
[ ] 所有Golden样本PASS
[ ] scene.svg / scene.json / hit-map一致
[ ] 不依赖JCanvas
[ ] 诊断可用
[ ] 100次重复输出无随机漂移
[ ] 大POU不会OOM
```
