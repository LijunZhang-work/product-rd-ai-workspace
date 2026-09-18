# 阶段2：Relation 结构化 Review 与原生 BEH 核验

## 1. 阶段目标

解决：

> **画面对，不代表底层 Relation 对。**

必须分别验证：

```text
视觉拓扑
Port / Direction
Relation Identity
```

---

## 2. 三层正确性

### A. Topology

```text
A → B
```

### B. Port / Direction

```text
A.OUT1 → B.IN2
```

### C. Origin

是否真的来自：

```text
relation_2
```

---

## 3. Neighborhood Review

点击 Node：

```text
只保留当前节点 + 一跳邻居
```

显示：

```text
BEH显示：+
内部名：test-3

IN 2
OUT 1
```

并列出邻居人眼名称。

---

## 4. Relation Identity

内部必须保存：

```text
edge_id
relation_id
xml_path
source
target
source_port
target_port
scope
parser_rule
evidence
```

Relation ID 默认不大面积铺在线上，但可以切换小徽标。

---

## 5. 自动异常检查

至少：

```text
DUPLICATE_ORIGIN
DUPLICATE_SEMANTIC_EDGE
CROSS_SCOPE
PORT_AMBIGUOUS
UNKNOWN_RELATION_FAMILY
DIRECTION_AMBIGUOUS
```

---

## 6. 禁止“看起来对就去重”

例如：

```text
两条候选都变成 A→B
```

不能因为视觉相同就删除一条。

必须先解释：

```text
为什么两个不同 origin 得到同一语义Edge？
```

---

## 7. Suspicious Queue

输出：

```text
suspicious_relations.json
```

UI：

```text
上一处
下一处
```

自动定位局部。

---

## 8. 原生 BEH 核验

可疑对象进入：

```text
Native Verification Task
```

例如：

```json
{
  "type": "EDGE",
  "edge_id": "E17",
  "expected_relation_id": "relation_2",
  "source_node": "A",
  "target_node": "B"
}
```

---

## 9. 固定工具优先

先实现：

```text
capture_window
capture_region
double_click
send_keys
read_clipboard
read_dialog
close_dialog
compare_exact
record_result
```

这些不依赖 AI。

---

## 10. 属性读取优先级

```text
1. UIA / Java Access Bridge
2. Ctrl+A / Ctrl+C
3. Keyboard navigation
4. 小视觉模型
```

---

## 11. 固定结果

只有：

```text
PASS
MISMATCH
UNRESOLVED
```

---

## 12. 验收

1. 人可快速审一个局部；
2. 机器能审 relation identity；
3. 可疑关系队列可用；
4. Node原生属性可核验；
5. 简单Relation能尝试双击读取；
6. 失败不乱猜，返回UNRESOLVED；
7. 结果进入 Verified Dataset。
