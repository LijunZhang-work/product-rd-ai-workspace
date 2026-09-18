# 阶段2：Relation 结构化 Review 与原生 BEH 核验

## 1. 阶段目标

阶段1让图“能看、能解释”。

阶段2解决：

> **这张图到底可信不可信？**

特别关注：

```text
拓扑对
但relation_id错
```

这种隐藏错误。

---

# 2. 三层正确性

一条线必须分别审：

## Level A：视觉拓扑

```text
A → B
```

是否对。

## Level B：Port / Direction

```text
A.OUT1 → B.IN2
```

是否对。

## Level C：BEH Relation Identity

是否真来自：

```text
relation_2
```

而不是：

```text
relation_10
```

---

# 3. 人工Review不逐条双击relation

人工主要看：

```text
节点邻域
IN / OUT数量
人眼可见邻居名称
```

而不是逐条 relation_id。

---

# 4. Neighborhood Review

点 Node：

```text
整图变暗
↓
只显示当前Node和1跳关系
```

右侧：

```text
BEH显示：+
内部名：test-3

IN 2
- M_FlagA
- M_FlagB

OUT 1
- TON_2
```

人可以快速对照 BEH。

---

# 5. Relation Identity机器审计

内部必须保存：

```text
Graph Edge ID
BEH relation_id
XML path
Source/Target
Port
Scope
Parser Rule
Evidence
```

日常视觉默认不铺完整 relation 名。

提供：

```text
显示Relation身份
```

小徽标：

```text
[r2]
```

---

# 6. 必测异常

## A. 同一relation重复生成Edge

报警：

```text
DUPLICATE_ORIGIN
```

## B. 不同relation映射到同一语义Edge

报警：

```text
DUPLICATE_SEMANTIC_EDGE
```

## C. 跨Scope

报警：

```text
CROSS_SCOPE
```

## D. Port缺失

```text
PORT_AMBIGUOUS
```

## E. Relation family未知

```text
UNKNOWN_RELATION_FAMILY
```

---

# 7. Suspicious Queue

系统自动生成：

```text
suspicious_relations.json
```

优先：

- relation identity冲突；
- 低置信；
- continuation；
- 不同network；
- degree异常；
- source/target歧义；
- 同一relation多解释；
- 多relation同Edge。

---

# 8. 原生BEH核验为什么放在这里

有些关系仅靠私有 XML 很难最终证明。

此时 BEH 自己的属性弹窗是重要真值源。

目标：

```text
可疑Edge
↓
原生BEH双击
↓
读取relation_id / name / property
↓
和Graph IR比较
```

---

# 9. 先做固定工具，不先做AI Agent

先开发：

```text
capture_window
capture_region
double_click
send_keys
read_clipboard
read_dialog_by_UIA_or_JAB
close_dialog
compare_exact
record_verification
```

这些工具应当：

> 无 AI 也能被手工脚本调用。

---

# 10. Node核验

Graph IR：

```text
Node N173
expected_internal_name=test-3
geometry=...
```

程序：

```text
定位
→ 双击
→ 读属性
→ exact compare
```

---

# 11. Relation核验

Graph IR：

```text
Edge E17
source=A
target=B
expected_relation=relation_2
```

程序：

```text
定位A/B
→ 预测线区域
→ 双击候选线
→ 读取弹窗
→ compare
```

---

# 12. 读取属性优先级

```text
1. UIA / Java Access Bridge
2. Ctrl+A / Ctrl+C / Clipboard
3. Keyboard navigation
4. Vision OCR /视觉读取
```

视觉放最后。

---

# 13. 验证状态

固定三态：

```text
PASS
MISMATCH
UNRESOLVED
```

禁止模型自己创造模糊“差不多”。

---

# 14. Verification Result

```json
{
  "edge_id": "E17",
  "expected_relation_id": "relation_2",
  "actual_relation_id": "relation_10",
  "result": "MISMATCH",
  "evidence": {
    "popup_screenshot": "...",
    "copied_text": "relation_10"
  }
}
```

---

# 15. 并行：BEH自动化能力检测器

阶段2可并行运行旧的能力检测器：

```text
UIA
JAB
Canvas visibility
Palette
Property Panel
```

结果决定阶段3到底能做到：

```text
结构化操作
还是
视觉+坐标操作
```

---

# 16. 阶段2验收

至少：

1. 一个簇可以快速人工拓扑Review；
2. relation identity可机器审；
3. Suspicious Queue可用；
4. Node原生核验可用；
5. 至少简单线可以双击读到relation名称；
6. 失败可返回UNRESOLVED；
7. 原生核验结果可以写回 Verified Dataset。

---

# 17. 本阶段的关键原则

> **relation_id不是人工每条核对的主界面信息，但它必须是机器证据链中的一等公民。**
