# 阶段4：DeepSeek Harness + 小视觉模型的多模型验图 Agent

## 1. 阶段目标

在阶段3已经存在“固定验图工具”的基础上，再接入：

```text
DeepSeek V4 Flash
+
Harness
+
小型视觉模型
```

形成：

> 规划大脑 + 视觉眼睛 + 固定工具双手

不要让任何单一模型承担全部任务。

---

# 2. 总体分工

```text
DeepSeek V4 Flash
        │
        │ 任务规划 / 状态判断
        ▼
      Harness
        │
        ├── Graph IR查询工具
        ├── 截图工具
        ├── 视觉定位工具
        ├── 鼠标/键盘工具
        ├── 弹窗读取工具
        └── 固定比较器
```

小视觉模型只负责窄任务：

```text
这张局部截图中“+”在哪里？
A和B之间候选线段在哪？
当前弹窗是不是Relation属性窗口？
Name输入框大概在哪里？
```

不要让它理解整个 PLC 图。

---

# 3. Agent职责

大模型负责：

1. 读取待验证任务；
2. 获取 source / target / expected relation；
3. 决定下一步调用哪个工具；
4. 发现点击错误后决定是否重试；
5. 判断什么时候转为 UNRESOLVED；
6. 汇总验证结果。

---

# 4. 固定工具职责

固定程序负责：

```text
截图
鼠标点击 / 双击
键盘输入
剪贴板读取
UIA / JAB读取
expected vs actual比较
任务队列
日志
截图存档
```

尽量不要把确定性工作交给模型。

---

# 5. 视觉模型职责

视觉模型只处理：

```text
localize
classify
confirm
```

例如：

```text
输入：
裁剪后的 500x400 局部图

问题：
“找到从左侧+图元到右侧TON图元之间最可能的线段中部坐标。”
```

而不是：

```text
“请理解整个BEH图并检查所有relation。”
```

---

# 6. 任务闭环

```text
Task E17
↓
读取 Graph IR
↓
知道 source=A / target=B / expected=r2
↓
截图 BEH
↓
裁剪 A-B 局部
↓
视觉模型定位候选线
↓
固定程序双击
↓
读取弹窗
↓
固定比较 expected/actual
↓
PASS
```

若弹窗不符：

```text
反馈给Harness
↓
选择第二候选线段
↓
重试
```

超过阈值：

```text
UNRESOLVED
```

---

# 7. 工具接口建议

至少：

```text
get_verification_task()
get_node_geometry(node_id)
get_edge_expected(edge_id)

capture_window()
capture_region(rect)

vision_locate(query, image)

double_click(x, y)
send_keys(keys)
read_clipboard()

read_accessible_dialog()
close_dialog()

compare_exact(expected, actual)
record_result()
```

---

# 8. AI上下文必须小

不要把：

```text
几十MB XML
```

交给 Agent。

每个任务只给：

```text
Edge E17
Source A
Target B
Expected relation r2
Source/Target Geometry
Relevant Graph IR
最近一次截图
```

---

# 9. Harness边界

Harness 只作为：

> 多步工具调用 / Agent编排层

不要让项目核心数据模型依赖 Harness。

核心仍然是：

```text
Graph IR
Verification Task
Verification Result
```

以后换模型或换 Agent 框架，也不需要推翻阶段1～3。

---

# 10. 弱视觉模型的容错设计

必须允许视觉模型犯错。

利用：

```text
动作后反馈
```

自校验：

```text
点了一条线
↓
弹窗显示 relation_99
↓
不是 expected r2
↓
说明点错
↓
关闭并尝试下一候选
```

这比要求视觉模型第一次定位100%正确现实得多。

---

# 11. 风险控制

Agent默认只允许：

```text
查看
双击
打开属性
复制
关闭
缩放/平移
```

禁止：

```text
修改字段
保存
删除
创建
确认有副作用的弹窗
```

这是只读验图 Agent。

---

# 12. 阶段4验收

选一批对象：

```text
20 Nodes
30 Relations
```

要求：

1. Agent能自动完成大部分核验；
2. PASS/MISMATCH结果与人工一致；
3. 视觉模型点错时能通过弹窗反馈纠正；
4. 不能确认时返回 UNRESOLVED；
5. 不发生工程修改；
6. 有完整轨迹日志；
7. 模型更换时固定工具仍可复用。

完成后进入阶段5。
