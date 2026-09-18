# BEH 图元簇结构化建模与可审计 Review 设计

## 一、设计目标

当前 BEH XML 很大，图元、relation、continuation、connector、引用关系等结构复杂。

现有流程如果是：

```text
XML
↓
解析
↓
直接生成 DOT
↓
发现图画错
↓
再看着 DOT 猜哪里出问题
```

会非常低效。

因为 DOT / SVG 只是最终表现层。真正需要 Review 的，不应该是图片，而应该是：

> **这张图背后的结构化图模型。**

因此建议把流程改成：

```text
BEH XML
↓
原始候选关系
↓
标准化 Graph IR
↓
结构化 Review
↓
Reviewed Graph
↓
Renderer
↓
DOT / SVG / HTML
```

核心原则：

> **先确定“到底有哪些节点、哪些线、每根线从哪来、是否属于当前簇、方向是什么”，Review 通过后才允许画图。**

---

## 二、核心架构原则

### 1. Renderer 不允许自己找 Relation

最终 DOT / SVG Renderer 只允许读取：

```text
reviewed_graph.json
```

它不能：

- 重新扫描 XML；
- 根据坐标猜线；
- 根据名字补线；
- 根据 continuation 自己扩展关系；
- 自己判断 source / target；
- 自己决定某根候选 relation 是否属于当前簇。

Renderer 的职责只有：

```text
节点在哪里
线从谁到谁
怎么排版
怎么画
```

### 2. 图片不是事实源

如果最终图画错，不应该问：

> “看起来为什么多了一根线？”

而应该问：

```text
这根 Edge 在 reviewed_graph.json 里是谁？
```

然后继续查：

```text
它来自哪个 Relation？
为什么被判定为可见线？
端点是谁？
为什么属于当前 Scope？
方向依据是什么？
```

### 3. 每根最终可见 Edge 必须有唯一“出生证明”

任何进入最终图的 Edge，都必须能回答：

```text
我是谁？
从哪里来？
为什么存在？
为什么属于当前簇？
为什么方向是这样？
```

没有这些信息：

```text
禁止进入最终图
```

---

## 三、建议的簇 Graph IR 总结构

每个簇生成一份结构化文件：

```json
{
  "cluster_id": "cluster_001",
  "scope": {},
  "nodes": [],
  "visible_edges": [],
  "boundary_edges": [],
  "implicit_links": [],
  "rejected_edges": [],
  "unknown_relations": [],
  "review": {},
  "render_spec": {}
}
```

各部分职责：

```text
scope
→ 当前簇的边界

nodes
→ 当前簇有哪些图元

visible_edges
→ 真正允许画出来的可见线

boundary_edges
→ 一端在簇内、一端在簇外的关系

implicit_links
→ continuation / connector 等隐式关系

rejected_edges
→ 找到了候选，但明确拒绝画

unknown_relations
→ 目前无法证明是什么

review
→ 自动审查结果

render_spec
→ 最终渲染所需布局信息
```

---

## 四、Scope：先把“当前簇”边界钉死

```json
{
  "scope": {
    "selection_id": "selection_20260814_001",
    "selected_node_ids": ["N100", "N101", "N102"],
    "page_id": "PAGE_03",
    "network_id": "NETWORK_17",
    "selection_bbox": {
      "x1": 1250,
      "y1": 630,
      "x2": 2410,
      "y2": 1430
    }
  }
}
```

所有候选 relation 都必须回答：

```text
source 是否属于当前 Scope？
target 是否属于当前 Scope？
是否同 Page？
是否同 Network？
```

不能因为 XML 里“有关联”，就自动进入当前簇。

---

## 五、Nodes：明确当前簇到底有哪些图元

```json
{
  "node_id": "N100",
  "xml_identity": {
    "element_type": "functionBlock",
    "xml_id": "471982",
    "xml_path": "/project/.../element[1837]"
  },
  "semantic": {
    "normalized_type": "COMPARE",
    "original_type": "XXX_COMPARE",
    "label": "<",
    "confidence": 0.98
  },
  "geometry": {
    "x": 1320,
    "y": 760,
    "width": 120,
    "height": 80
  },
  "ports": [
    {
      "port_id": "N100.P1",
      "role": "IN",
      "evidence": "..."
    },
    {
      "port_id": "N100.P2",
      "role": "OUT",
      "evidence": "..."
    }
  ]
}
```

重点区分：

```text
original_type
→ XML 原始类型

normalized_type
→ 系统统一后的语义类型
```

---

## 六、Visible Edge：最终真正允许画出来的线

每根最终可见线都必须有完整记录：

```json
{
  "edge_id": "E001",
  "source": {
    "node_id": "N100",
    "port_id": "N100.P2"
  },
  "target": {
    "node_id": "N101",
    "port_id": "N101.P1"
  },
  "direction": "SOURCE_TO_TARGET",
  "relation_identity": {
    "relation_id": "R7821",
    "xml_path": "/project/.../relation[288]"
  },
  "scope_check": {
    "source_in_scope": true,
    "target_in_scope": true,
    "same_page": true,
    "same_network": true
  },
  "evidence": [
    {
      "type": "XML_REFERENCE",
      "detail": "R7821 references N100.P2 and N101.P1"
    },
    {
      "type": "PORT_ROLE",
      "detail": "N100.P2=OUT, N101.P1=IN"
    }
  ],
  "confidence": 0.97,
  "review_status": "APPROVED"
}
```

以后用户问：

> “这根线哪里来的？”

系统直接追：

```text
Edge E001
↓
Relation R7821
↓
XML Path
↓
Source Port
↓
Target Port
↓
Scope Check
↓
Direction Evidence
```

---

## 七、候选错误线必须进入 Rejected Edges

如果真实只有：

```text
A → B
```

程序又发现：

```text
A → C
```

不能先画出来再说。

应该放入：

```json
{
  "candidate_edge_id": "CE013",
  "source_candidate": "N100",
  "target_candidate": "N777",
  "found_from": {
    "xml_object": "R9291",
    "xml_path": "/project/.../relation[3991]"
  },
  "reject_reason": [
    "target_not_in_current_network",
    "insufficient_visible_relation_evidence"
  ],
  "review_status": "REJECTED"
}
```

这样可以明确比较：

```text
为什么 E001 被 APPROVED？
为什么 CE013 被 REJECTED？
```

---

## 八、Boundary Edge：簇内和簇外关系单独存

例如：

```text
当前簇：
A → B → C

同时：
C → X
```

其中 C 在当前簇，X 在外部。

这根线应该是：

```json
{
  "edge_id": "BE001",
  "inside_node": "N102",
  "outside_node": "N900",
  "direction": "OUTGOING",
  "relation_id": "R8821",
  "render_in_cluster": false
}
```

默认：

```text
render_in_cluster = false
```

防止外部模块被整片拉进当前簇。

---

## 九、Implicit Link：隐式关系不能混成普通可见线

例如：

```text
Connector
Continuation
Jump / Label
跨页引用
```

单独保存：

```json
{
  "link_id": "IL001",
  "type": "CONNECTOR_CONTINUATION",
  "from_node": "N300",
  "to_node": "N901",
  "signal_name": "C1",
  "visible_line": false,
  "confidence": 0.93,
  "evidence": [
    "same continuation name",
    "standard semantic mapping"
  ]
}
```

重点：

```text
visible_line = false
```

Renderer 默认不得画成普通实线。

---

## 十、Unknown Relations：不知道就明确不知道

```json
{
  "object_id": "X998",
  "related_nodes": ["N100", "N101"],
  "reason": "relation semantics not proven",
  "xml_path": "...",
  "action": "DO_NOT_RENDER"
}
```

默认规则：

```text
UNKNOWN
→ DO_NOT_RENDER
```

绝对禁止：

```text
不知道
↓
感觉像线
↓
先画出来
```

---

## 十一、必须增加 Review 层

在生成最终 DOT / SVG 前，自动执行 Review：

```json
{
  "review": {
    "node_count": 4,
    "visible_edge_count": 3,
    "boundary_edge_count": 1,
    "implicit_link_count": 1,
    "rejected_edge_count": 7,
    "unknown_relation_count": 2,
    "checks": [
      {
        "check": "all_visible_edge_sources_exist",
        "result": "PASS"
      },
      {
        "check": "all_visible_edge_targets_exist",
        "result": "PASS"
      },
      {
        "check": "no_duplicate_relation_id",
        "result": "PASS"
      },
      {
        "check": "all_internal_edges_within_scope",
        "result": "PASS"
      },
      {
        "check": "no_unknown_edge_rendered",
        "result": "PASS"
      }
    ],
    "overall_status": "READY_FOR_RENDER"
  }
}
```

只有：

```text
READY_FOR_RENDER
```

才允许进入 Renderer。

否则：

```text
BLOCK_RENDER
```

---

## 十二、建议的自动 Review 检查项

### Node 检查

```text
所有 Node ID 唯一
所有 Node 都有来源 XML
所有 Node 都属于当前 Scope
Geometry 合法
```

### Edge 检查

```text
source 存在
target 存在
source != target（除非允许自环）
relation identity 唯一
同一个原始 relation 不能重复生成多条 edge
端点数量符合预期
```

### Scope 检查

```text
Internal Edge 两端必须都在 Scope
Boundary Edge 必须只有一端在 Scope
External Edge 禁止进入 Reviewed Graph
```

### Direction 检查

```text
Direction 必须有 Evidence
Unknown 方向不能伪装成确定方向
```

### Relation 类型检查

```text
VisibleEdge 不能来自 ImplicitLink
Unknown Relation 不能进入 VisibleEdge
Rejected Edge 不能进入 Renderer
```

---

## 十三、Renderer 必须变成“傻 Renderer”

以前 Renderer 可能承担：

```text
找 Node
找 Relation
猜方向
判断 Scope
决定是否画
布局
渲染
```

以后必须缩成：

```text
读取 Reviewed Graph
↓
Node → 画节点
VisibleEdge → 画线
ImplicitLink → 根据显示模式决定
↓
布局
↓
输出 DOT / SVG
```

例如：

```json
{
  "visible_edges": [
    {"source": "N1", "target": "N2"},
    {"source": "N2", "target": "N3"}
  ]
}
```

Renderer 只允许输出：

```dot
N1 -> N2;
N2 -> N3;
```

禁止自行增加：

```dot
N1 -> N3;
```

---

## 十四、增加“人类 Review 表”

建议自动生成：

| Edge | From | To | 类型 | 来源 | Scope | 置信度 | 状态 |
|---|---|---|---|---|---|---:|---|
| E001 | N100.OUT | N101.IN | Visible | R7821 | Internal | 0.97 | ✅ APPROVED |
| E002 | N101.OUT | N102.IN | Visible | R7822 | Internal | 0.99 | ✅ APPROVED |
| CE013 | N100 | N777 | Candidate | R9291 | Cross Network | 0.41 | ❌ REJECTED |
| BE001 | N102 | N900 | Boundary | R8821 | External | 0.96 | 不画 |

点击某一行，再展开：

```text
XML来源
Relation ID
Port
Scope
Evidence
Reject Reason
```

---

## 十五、建议四阶段文件产物

每个簇固定保存：

```text
cluster_001/
├── 01_raw_candidates.json
├── 02_normalized_graph.json
├── 03_reviewed_graph.json
├── 04_review_report.html
└── 05_render.dot
```

### 01_raw_candidates.json

记录解析器最开始发现的所有候选：

```text
候选 Node
候选 Relation
候选引用
未知结构
```

### 02_normalized_graph.json

统一为：

```text
Node
Port
VisibleEdgeCandidate
BoundaryCandidate
ImplicitLink
Unknown
```

### 03_reviewed_graph.json

只留下通过 Review 的：

```text
Approved Nodes
Approved VisibleEdges
Approved BoundaryEdges
Approved ImplicitLinks
```

同时保留：

```text
Rejected / Unknown
```

作为审计信息。

### 04_review_report.html

给人看的 Review 页面。

### 05_render.dot

只有 Reviewed Graph 通过后才生成。

---

## 十六、出现错误时如何定位责任层

以后如果最终图错，按以下顺序检查：

```text
最终图错误
↓
05_render.dot 是否已经错？
↓
03_reviewed_graph.json 是否已经错？
↓
02_normalized_graph.json 是否归一化错？
↓
01_raw_candidates.json 是否候选发现阶段就错？
↓
XML原始证据
```

这样可以明确区分：

```text
候选发现错误
归一化错误
Review错误
Renderer错误
```

---

## 十七、推荐 Edge 状态机

每个候选 Edge 必须经过：

```text
DISCOVERED
↓
NORMALIZED
↓
VALIDATED
↓
APPROVED
↓
RENDERED
```

也可能：

```text
DISCOVERED
↓
REJECTED
```

或者：

```text
DISCOVERED
↓
UNKNOWN
```

禁止：

```text
DISCOVERED
↓
直接 RENDERED
```

---

## 十八、推荐 Edge 数据结构

```json
{
  "edge_id": "E001",
  "status": "APPROVED",
  "source": {
    "node_id": "N100",
    "port_id": "P100_2"
  },
  "target": {
    "node_id": "N101",
    "port_id": "P101_1"
  },
  "direction": {
    "value": "SOURCE_TO_TARGET",
    "confidence": 0.97,
    "evidence_ids": ["EV_001", "EV_002"]
  },
  "scope": {
    "classification": "INTERNAL",
    "same_page": true,
    "same_network": true
  },
  "origin": {
    "relation_id": "R7821",
    "xml_path": "...",
    "parser_rule": "RULE_RELATION_X"
  },
  "review": {
    "status": "APPROVED",
    "reviewed_by": "RULE_ENGINE",
    "reasons": []
  }
}
```

---

## 十九、Evidence 建议单独统一管理

```json
{
  "evidence": [
    {
      "evidence_id": "EV_001",
      "type": "XML_REFERENCE",
      "source": "R7821",
      "detail": "..."
    },
    {
      "evidence_id": "EV_002",
      "type": "PORT_ROLE",
      "source": "N100.P2",
      "detail": "OUT"
    }
  ]
}
```

好处：

```text
一条证据可以被多个 Edge 复用
方便 Review
方便后续 AI 分析
方便做统计
```

---

## 二十、同一个真实 Relation 不能被重复解释

必须建立：

```text
Canonical Relation Identity
```

至少包含：

```text
relation_id
xml_path
parent_scope
endpoint references
```

如果两个解析规则都发现同一个 Relation：

```text
合并证据
```

不能：

```text
生成两条 Edge
```

这是防止“一根真实线变成两根”的重要机制。

---

## 二十一、禁止用 source + target 简单去重

例如：

```text
A → B
```

可能存在：

```text
两个不同端口的两条真实线
```

所以不能简单按：

```text
source=A
target=B
```

去重。

至少考虑：

```text
Relation ID
Source Port
Target Port
Scope
```

---

## 二十二、当前阶段开发优先级

### P0
```text
Graph IR schema
```

### P1
```text
Edge provenance
```

### P2
```text
Scope classification
```

### P3
```text
Review rules
```

### P4
```text
Human review table
```

### P5
```text
DOT / SVG renderer
```

---

## 二十三、AI 的使用原则

AI可以参与：

```text
解释 Unknown
比较多个候选 Relation
分析规则异常
帮助总结新规律
```

但最终：

```text
是否进入 Reviewed Graph
```

尽量由：

```text
固定规则 + 明确证据
```

决定。

至少不能让 AI：

```text
“感觉这根线应该存在”
```

然后直接进入最终图。

---

## 二十四、推荐最终流程

```text
几十MB BEH XML
       ↓
Parser
       ↓
Raw Candidates
       ↓
Normalizer
       ↓
Graph IR
       ↓
Scope Classifier
       ↓
Evidence Validator
       ↓
Review Engine
       ↓
Reviewed Graph
       ↓
┌───────────────┬───────────────┐
│               │               │
▼               ▼               ▼
DOT           SVG/GLSP          AI
│               │               │
给人看          人机交互         小白解释
```

---

## 二十五、最重要的项目规则

建议直接写进 Codex 开发规范：

> **任何最终出现在 DOT / SVG 中的 Edge，都必须在 `reviewed_graph.json` 中存在唯一记录，并且必须具有：来源 XML、Relation Identity、Source、Target、Scope、Direction Evidence、Review Status。**

同时：

> **Renderer 禁止创造新 Edge。**

以及：

> **最终图片永远不是 Review 的事实源，Graph IR 才是。**

---

## 二十六、一句话总结

> **不要再“先画出来，再看着图猜为什么错”。正确流程应该是：先把当前簇整理成一份可审计的结构化 Graph IR，把每个 Node、Relation、Edge、Boundary、Continuation、Unknown 的来源和证据全部列清楚；Review 通过以后，DOT / SVG 只负责把这份已经确认的结构画出来。**
