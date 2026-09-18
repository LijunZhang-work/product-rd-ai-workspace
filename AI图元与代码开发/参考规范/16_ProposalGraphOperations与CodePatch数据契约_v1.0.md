> 工作区归档说明（2026-09-17）：本文件继承原有技术内容与验证范围；本文可识别的文件引用已适配新目录。当前模块入口见 [模块导航](../README.md)。资料归档不代表产品功能或实机验证已经完成。

# Proposal Graph Operations 与 Code Patch 数据契约

## 1. 目的

让AI只提出可审查候选，不直接修改正式 BEH 或代码仓。

## 2. Proposal Bundle

```text
proposal/
├── manifest.json
├── graph-operations.json
├── code-patches.json
├── impact-report.json
├── validation-plan.json
└── evidence.json
```

## 3. Graph Operation类型

```text
CREATE_NODE
DELETE_NODE
MOVE_NODE
SET_PARAMETER
CONNECT
DISCONNECT
REPLACE_NODE
```

每个操作必须：

```json
{
  "operation_id": "OP-1",
  "op": "CONNECT",
  "target_scope": "POU-001",
  "preconditions": [],
  "payload": {},
  "reason": "",
  "evidence_refs": [],
  "status": "PROPOSED"
}
```

## 4. 禁止字段

AI不得提供或控制：

-最终relation_id；
-最终native_id；
-隐藏字段；
-校验和；
-厂商内部索引；
-不透明代码生成元数据。

这些由原生BEH应用层生成。

## 5. Code Patch

```json
{
  "patch_id": "CP-1",
  "file": "src/x.cpp",
  "base_sha256": "...",
  "patch_format": "UNIFIED_DIFF",
  "patch": "...",
  "related_operation_ids": [],
  "validation": {
    "format": "NOT_RUN",
    "static_analysis": "NOT_RUN",
    "build": "NOT_RUN",
    "tests": "NOT_RUN"
  }
}
```

## 6. Impact Report

必须列出：

-新增/修改/删除Node；
-新增/删除Relation；
-圈外影响；
-修改文件；
-公共接口变化；
-风险；
-未知；
-回滚方式。

## 7. Proposal状态

```text
PROPOSED
VALIDATED
PARTIALLY_ACCEPTED
ACCEPTED
REJECTED
APPLIED
ROLLED_BACK
```

Web不得把PROPOSED显示成已生效。

## 8. 应用门禁

- Schema通过；
-Precondition通过；
-原生模型验证；
-代码补丁基线Hash一致；
-构建/测试满足策略；
-人工确认；
-Round-trip通过。
