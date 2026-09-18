# 阶段4：Compose 人机共创与 AI 写图源

## 1. 进入本阶段的前提

只有“读图”已经比较可信后，才能写图。

必须具备：

- Graph IR；
- Relation Review；
- Verified Dataset；
- Proposal Layer；
- 至少一批 Verified Component。

---

# 2. Compose目标

让用户可以：

```text
圈一个区域
+
自然语言
+
可选草图
+
可选人工拖图元
```

让 AI生成：

```text
Proposal Graph
```

---

# 3. 第一子阶段：区域 + 自然语言

用户：

```text
圈出区域
“这里增加低频持续2秒后告警。”
```

AI输出：

```text
Graph Operations Proposal
```

例如：

```text
Create Compare
Create TON
Create Alarm
Connect ...
```

---

# 4. 第二子阶段：草图

Annotation支持：

```text
Freehand
Sketch Arrow
Text Note
```

草图只表示：

```text
Layout Hint
Flow Hint
Intent Hint
```

不直接成为正式Node/Edge。

---

# 5. 第三子阶段：Palette + AI补全

用户人工拖：

```text
Frequency
Compare
Alarm
```

再说：

```text
“中间补2秒确认。”
```

AI只补缺失部分。

---

# 6. AI输入 Intent Pack

```json
{
  "target_region": {},
  "existing_context": {},
  "text_intent": "",
  "sketch": [],
  "nearby_ports": [],
  "constraints": {}
}
```

---

# 7. AI输出不是XML

旧 V4 Flash只能输出：

```text
Canonical Graph Operations
```

例如：

```json
{
  "operations": [
    {"op":"CREATE_NODE","type":"TON","temp_id":"P1"},
    {"op":"SET_PARAMETER","node":"P1","name":"delay","value":"2s"},
    {"op":"CONNECT","source":"N17.OUT","target":"P1.IN"}
  ]
}
```

---

# 8. Proposal Graph

Operations先应用到：

```text
Proposal Graph
```

显示为：

```text
半透明节点
虚线Edge
```

不直接改正式工程。

---

# 9. Compose Review

Review：

```text
Node类型是否合法
Port是否匹配
Edge是否重复
Scope是否合理
是否覆盖原图
参数是否完整
是否使用Verified Component
```

---

# 10. Verified Component Registry

每种可生成图元记录：

```text
BEH视觉名
内部类型
Ports
参数
默认值
原生XML样本
隐藏字段
代码附件
验证级别
```

只允许：

```text
VERIFIED
```

图元进入自动生成主路径。

---

# 11. 写BEH的两条路径

## 路径A：Native BEH Driver

优先：

```text
AI Graph Operation
↓
BEH Driver
↓
原生BEH自己创建
```

优点：

- 隐藏字段由BEH维护；
- relation_id由BEH生成；
- 附属代码由BEH生成。

---

## 路径B：BEH Writer

用于原生Driver做不到的部分。

必须：

```text
Native Template
+
Minimal Patch
```

不要完全重写工程。

---

# 12. Round-trip

任何自动生成都必须：

```text
Proposal Graph A
↓
写入BEH
↓
BEH保存
↓
重新解析
↓
Graph B
↓
Semantic Compare
```

只有：

```text
A ≈ B
```

才算成功。

---

# 13. V4 Flash在写图阶段的角色

只负责：

```text
意图理解
选择组件
生成Graph Operations候选
解释Proposal
```

不负责：

```text
生成relation_id
生成随机内部ID
维护vendor hidden field
exact XML patch
```

---

# 14. 小视觉模型角色

Compose早期甚至可以不用视觉模型。

草图阶段再用于：

```text
粗略草图识别
布局关系识别
箭头意图识别
```

但结果只能作为 Hint。

---

# 15. 阶段4验收

从最小闭环开始：

```text
1个已验证Compare
+
1个已验证TON
+
1个已验证Output
```

用户文字生成 Proposal。

通过 Review。

最终：

```text
Native Driver / Writer
→ BEH
→ Save
→ Parse Back
→ PASS
```

再扩大。
