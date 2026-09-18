> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# AnalysisTaskBundle 与 AnalysisResultBundle 数据契约

## 1. 目的

使初期文件传递和后期Harness直连使用同一稳定协议。

## 2. Task Bundle结构

```text
TASK-001/input/
├── manifest.json
├── workspace-ref.json
├── scene-ref.json
├── selection.json
├── annotations.json
├── user-intent.json
├── selected-subgraph.json
├── boundary-context.json
├── native-properties.json
├── code-access.json
├── diagnostics.json
└── preview/
```

## 3. `workspace-ref.json`

只保存路径引用和Hash，不复制整个代码仓：

```json
{
  "repo_root": "...",
  "entry_xml": "...",
  "canvas_id": "POU-001",
  "repo_commit": "...",
  "compile_commands": "...",
  "code_index_id": "IDX-1"
}
```

## 4. `selected-subgraph.json`

只包含所选对象及直接内部关系。边界对象单独放在`boundary-context.json`。

## 5. `code-access.json`

定义Skill允许调用的工具和工作区：

```json
{
  "tools": [
    "find_symbol",
    "find_references",
    "get_code_range",
    "get_callers",
    "get_callees",
    "trace_data_flow"
  ],
  "allowed_root": "...",
  "analysis_precision": "HIGH|DEGRADED|UNKNOWN"
}
```

## 6. Result Bundle结构

```text
TASK-001/output/
├── manifest.json
├── result.json
├── report.md
├── evidence.json
├── diagnostics.json
└── artifacts/
```

## 7. `result.json`

```json
{
  "schema_version": "analysis-result/1.0",
  "task_id": "TASK-001",
  "status": "PASS|PARTIAL|FAILED",
  "summary": {},
  "inputs": [],
  "steps": [],
  "outputs": [],
  "boundary_links": [],
  "code_paths": [],
  "uncertainties": [],
  "evidence_refs": []
}
```

### Step

```json
{
  "step_no": 1,
  "title": "",
  "focus_refs": {
    "node_ids": [],
    "port_ids": [],
    "relation_ids": [],
    "code_refs": []
  },
  "input": {},
  "operation": {},
  "output": {},
  "professional_explanation": "",
  "beginner_explanation": "",
  "claim_status": "FACT|INFERENCE|UNKNOWN",
  "confidence": "HIGH|MEDIUM|LOW|UNKNOWN",
  "evidence_refs": []
}
```

## 8. Evidence

```json
{
  "evidence_id": "EV-1",
  "type": "NATIVE_SCENE|NATIVE_PROPERTY|CODE_AST|CODE_TEXT|CALL_GRAPH|USER_OBSERVATION|MODEL_INFERENCE",
  "source_ref": "",
  "range": {},
  "summary": ""
}
```

模型推理Evidence不能作为HIGH事实的唯一依据。

## 9. 幂等与版本

Task ID唯一；相同Task输入Hash可复用结果。Skill和模型版本写入Result manifest。

## 10. Web显示规则

Web只显示Schema通过的Result。失败或PARTIAL必须展示diagnostics，不得伪装为完整分析。
