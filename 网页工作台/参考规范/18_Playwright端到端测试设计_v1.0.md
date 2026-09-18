> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Playwright 端到端测试设计

## 1. 定位

Playwright负责 **Web Workbench** 的真实浏览器验证，不负责操作原生 Java BEH GUI。

利用：

- Locator自动等待；
-可重试断言；
-真实点击/拖动；
-DOM/SVG结构检查；
-截图回归；
-Console监听。

## 2. Locator契约

所有核心对象必须提供稳定定位属性：

```text
data-testid
data-native-id
data-kind
data-task-id
data-step-no
```

优先使用用户可见角色和稳定显式契约，不依赖CSS层级或随机类名。

## 3. 全局Smoke

每次CI：

1. 页面URL/标题正确；
2.不是空白壳；
3.无框架错误Overlay；
4.Console无未处理error；
5.Workspace页面可交互；
6.至少一个Golden场景显示。

## 4. 阶段1 E2E

### 工作区

```text
创建工作区
→ 校验路径
→ 保存
→ 重新打开
```

### 画布

```text
选择POU
→ scene.svg出现
→ Node/Relation数量符合Fixture
→ Fit
→ Zoom
→ Pan
```

### 点击

```text
点击Node
→ 选择详情显示同一native_id

点击Relation
→ 显示同一relation_id
```

### 面板

```text
右侧折叠/展开
底部折叠/展开
拖动尺寸
纯画布模式
刷新后恢复
```

### 圈选

- 矩形；
-椭圆；
-Lasso；
-CONTAIN/INTERSECT；
-Relation tolerance；
-边界分类；
-清除选择。

### 标注

- Arrow；
-Text；
-Freehand保存；
-缩放后不漂移。

### 导出

```text
生成Task
→ 目录存在
→ manifest/schema正确
→ UI状态显示“已准备”
```

## 5. 阶段2 E2E

将固定Result Bundle放入任务输出：

```text
Web检测结果
→ 展开分析结果
→ 点击Step 3
→ Node和Relation高亮
→ 其他对象淡化
→ 证据页显示
→ 代码引用跳转
```

验证右侧名称是“分析结果”，不出现内置API调用状态。

## 6. 阶段4 E2E

```text
指定Compose区域
→ 输入文字
→ 导出Compose Task
→ 注入Proposal结果
→ Proposal层出现
→ 接受/拒绝单个Operation
→ 正式层未变化
```

## 7. 视觉回归

只对稳定环境做截图Baseline：

- 固定浏览器版本；
-固定字体；
-固定viewport；
-固定DPI/系统；
-禁用随机动画；
-固定Golden场景。

视觉比较是第二层。第一层必须先检查：

```text
Native ID
对象数量
路径数据
状态
```

## 8. 失败证据

每个失败保存：

- screenshot；
-trace；
-console；
-network；
-DOM snapshot；
-task/result fixture；
-浏览器版本。

## 9. 反脆弱规则

- 不使用固定sleep；
-使用Locator和auto-retrying assertion；
-每个测试独立工作区；
-不依赖执行顺序；
-可并行的才并行；
-外部模型不进入普通E2E；
-模型结果用固定Fixture。

## 10. 最小CI集

每个PR：

```text
smoke
workspace
native-scene
selection
panel-collapse
task-export
result-linking
console-health
```

Nightly增加：

```text
visual
large-scene
long-running
multiple-browsers
```
