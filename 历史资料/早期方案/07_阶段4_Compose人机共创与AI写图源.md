# 阶段4：Compose 人机共创与 AI 写图源

## 1. 前提

进入本阶段前必须已有：

```text
Graph IR
Relation Review
Verified Dataset
Proposal Layer
Verified Component Registry
```

---

## 2. Compose 输入方式

### A. 区域 + 自然语言

```text
圈出一块
“这里增加低频持续2秒后告警。”
```

### B. 区域 + 草图

草图只作为 Hint。

### C. 区域 + 文字 + 草图

结合：

```text
空间约束
业务意图
布局提示
```

### D. 人工拖图元 + AI补全

用户放基础节点，AI补缺失关系和组件。

---

## 3. Intent Pack

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

## 4. AI输出 Graph Operations

不直接输出 BEH XML：

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

## 5. Proposal First

Operations 先进入：

```text
Proposal Graph
```

显示：

```text
半透明Node
虚线Edge
```

---

## 6. Verified Component Registry

每种可生成组件记录：

```text
BEH显示
内部type
ports
参数
默认值
原生样本
隐藏字段
附属代码
验证级别
```

自动生成主路径只允许 VERIFIED。

---

## 7. 写入路径

### Native BEH Driver

优先让 BEH 自己创建，以保留隐藏数据。

### BEH Writer

只在需要时使用：

```text
Native Template
+
Minimal Patch
```

禁止全量重写未知私有工程。

---

## 8. Round-trip

任何自动生成：

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

才成功。

---

## 9. DeepSeek V4 Flash角色

只负责：

```text
意图理解
组件选择
Graph Operations候选
Proposal解释
```

不负责：

```text
relation_id生成
隐藏字段
exact XML patch
```

---

## 10. 小视觉模型角色

草图阶段才需要：

```text
粗略草图识别
箭头意图
布局关系
```

只能作为 Hint。

---

## 11. 验收

从最小闭环开始：

```text
Compare
+
TON
+
Output
```

生成 Proposal，Review，通过 Writer / Driver 落地，再 Parse Back 验证。
