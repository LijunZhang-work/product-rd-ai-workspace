> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../../README.md)。资料归档不代表产品功能或实机验证已经完成。

# NativeSceneBundle 与 HitMap 数据契约

## 1. 目的

定义 Headless Native Scene Service 与 Web/Gateway 之间唯一场景接口。任何前端、Skill、测试和缓存都不得绕过本契约重新解释 XML。

## 2. Bundle结构

```text
NativeSceneBundle/
├── manifest.json
├── scene.svg
├── scene.json
├── hit-map.json
├── native-properties.json
├── source-bindings.json
└── diagnostics.json
```

## 3. `manifest.json`

必填：

```json
{
  "schema_version": "native-scene/1.0",
  "workspace_id": "WS-001",
  "canvas_id": "POU-001",
  "jar_sha256": "...",
  "entry_xml_sha256": "...",
  "canvas_source_sha256": "...",
  "exporter_version": "1.0.0",
  "coordinate_space": "BEH_WORLD",
  "generated_at": "2026-08-19T00:00:00Z"
}
```

## 4. `scene.svg`

要求：

- 完整显示Node、Port、Relation、Arrow和Label；
-每个可交互对象具有稳定属性：

```xml
data-native-id
data-kind
data-scene-version
```

- 不执行脚本；
-不包含外部网络资源；
-避免不受控 `<foreignObject>`；
-文本和几何必须与scene.json对应。

## 5. `scene.json`

顶层：

```json
{
  "schema_version": "scene/1.0",
  "viewport": {},
  "nodes": [],
  "ports": [],
  "relations": [],
  "labels": [],
  "groups": []
}
```

### Node

```json
{
  "native_id": "test-3",
  "kind": "NODE",
  "native_type": "private-type",
  "display_name": "+",
  "internal_name": "test-3",
  "bounds": {"x":100,"y":200,"width":60,"height":40},
  "z_index": 10,
  "property_ref": "PROP-test-3",
  "source_binding_refs": []
}
```

### Port

```json
{
  "native_id": "port-17",
  "kind": "PORT",
  "owner_id": "test-3",
  "direction": "IN|OUT|INOUT|UNKNOWN",
  "position": {"x":100,"y":220},
  "bounds": {},
  "property_ref": "PROP-port-17"
}
```

### Relation

```json
{
  "native_id": "relation-2",
  "kind": "RELATION",
  "source_node_id": "A",
  "source_port_id": "A.OUT",
  "target_node_id": "B",
  "target_port_id": "B.IN",
  "path_points": [{"x":1,"y":2}],
  "arrow": {
    "direction": "SOURCE_TO_TARGET|TARGET_TO_SOURCE|BIDIRECTIONAL|NONE|UNKNOWN",
    "position": "SOURCE|TARGET|BOTH|NONE|UNKNOWN"
  },
  "style": {},
  "property_ref": "PROP-relation-2"
}
```

## 6. `hit-map.json`

### 选择策略

```json
{
  "selection_defaults": {
    "node_mode": "INTERSECT",
    "relation_tolerance_world": 6,
    "port_tolerance_world": 6
  }
}
```

### Node Hit Shape

支持：

```text
BOUNDS
POLYGON
PATH
```

### Relation Hit Shape

```json
{
  "native_id": "relation-2",
  "shape_type": "STROKED_PATH",
  "path_points": [],
  "tolerance": 6,
  "z_index": 2
}
```

`tolerance` 仅用于点击，不改变正式视觉。

## 7. `native-properties.json`

采用引用方式，避免scene.json过大：

```json
{
  "PROP-test-3": {
    "native_id": "test-3",
    "fields": [
      {"name":"Name","value":"test-3","type":"string"}
    ]
  }
}
```

## 8. `source-bindings.json`

仅包含原生明确绑定或Exporter可证明绑定。推断绑定属于Code Intelligence，不应写成原生事实。

## 9. `diagnostics.json`

必须包含：

```json
{
  "severity_counts": {},
  "unrendered_native_ids": [],
  "unknown_ports": [],
  "unknown_relations": [],
  "duplicate_ids": [],
  "missing_properties": [],
  "warnings": [],
  "errors": []
}
```

不得静默清空异常。

## 10. 一致性约束

- SVG中每个`data-native-id`必须在scene/hit-map中存在；
- scene中每个可见对象必须能在SVG中找到，除非diagnostics解释；
- relation端点必须存在或标UNKNOWN；
- native_id在canvas范围内唯一；
-所有坐标使用BEH世界坐标；
-JSON数值不得偷偷使用屏幕像素。

## 11. 版本策略

破坏性字段变更升级主版本。读取方必须拒绝未知主版本，不得猜测兼容。
