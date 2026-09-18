> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Selection、Annotation 与 Intent 数据契约

## 1. 目的

准确区分：

```text
用户选中了什么
用户明确标注了什么
用户自由画了什么
用户文字要求是什么
```

不得把所有信息混成一张截图交给模型。

## 2. SelectionContext

```json
{
  "schema_version": "selection/1.0",
  "selection_id": "SEL-001",
  "canvas_id": "POU-001",
  "geometry": {
    "type": "RECTANGLE|ELLIPSE|LASSO",
    "coordinate_space": "BEH_WORLD",
    "points": []
  },
  "selection_policy": "INTERSECT|CONTAIN",
  "selected_node_ids": [],
  "selected_port_ids": [],
  "selected_relation_ids": [],
  "boundary_relation_ids": [],
  "external_context_ids": []
}
```

## 3. Boundary分类

每条边界关系标记：

```text
INCOMING
OUTGOING
IMPLICIT
UNKNOWN
```

只选中一端的Relation不得自动把外部Node加入正式选择。

## 4. Structured Annotation

### Arrow

```json
{
  "annotation_id": "ANN-1",
  "type": "ARROW",
  "from": {"point":{}, "near_native_id":"N1"},
  "to": {"point":{}, "near_native_id":"N2"},
  "coordinate_space": "BEH_WORLD"
}
```

### Text

```json
{
  "type": "TEXT_NOTE",
  "text": "这里增加延时",
  "anchor": {"point":{}, "near_native_id":"N2"}
}
```

### Box/Highlight

结构化记录形状和关联对象。

## 5. Freehand

```json
{
  "annotation_id": "ANN-F1",
  "type": "FREEHAND",
  "semantic_status": "UNRESOLVED",
  "strokes": [{"points":[]}],
  "near_native_ids": []
}
```

自由笔不能自动解释为Node或Edge。只有：

-用户文字明确；
-结构化识别工具；
-视觉模型结果；
-人工确认；

才能产生语义候选。

## 6. UserIntent

```json
{
  "schema_version": "intent/1.0",
  "mode": "EXPLAIN|COMPOSE|REVIEW",
  "goal_text": "",
  "constraints": [],
  "must_preserve": [],
  "target_region": {},
  "requested_outputs": []
}
```

## 7. 语义优先级

```text
用户明确文字
>
结构化Annotation
>
确定性Selection
>
视觉模型对Freehand的推断
>
AI自由推测
```

注意：Selection证明“关注对象”，不自动证明“用户想修改对象”。

## 8. 序列化与隐私

- 保存世界坐标；
-不保存不必要屏幕截图；
-可选生成预览PNG，但预览不是事实源；
-文字备注进入任务包前支持敏感信息提醒。
