# AI 人工路径测试自动化 · Human Path Testing

这是一个可运行的 Python/Playwright MVP。用户描述操作流程；能看图的助手通过受限动作探路；路线整理成参数化数据后，由固定程序重放，保存截图、断言、Trace 和结果。

**当前实现的是固定 Runner 的 UI 操作与证据闭环。它不认证整个电脑已隔离，也不等于覆盖全部人工测试。**模型接口可接兼容 Chat Completions 的服务，或通过 `--stdio` 复用能看图的现有助手。

## 1. 安装

需要 Python 3.12，以及能运行 Chromium 的 Windows、macOS 或 Linux。下面命令在解压后的项目根目录运行；不要把虚拟环境复制到另一台电脑。

macOS / Linux / WSL：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.lock
python -m pip install --no-deps -e .
python -m playwright install chromium
python -m hpt doctor
```

Windows PowerShell（不要求改变系统脚本执行策略）：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements.lock
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m hpt doctor
```

Windows 后续命令中的 `python` 换为 `.\.venv\Scripts\python.exe` 即可。Linux 如果浏览器报告缺少系统库，依据错误安装 Playwright 所需系统依赖；项目不会自动执行管理员命令。

`requirements.lock` 锁定 Python 包和下载摘要，**不包含浏览器二进制或系统库**。浏览器可通过正式环境变量 `HPT_CHROMIUM_EXECUTABLE` 指定已有可执行文件；其路径与实际浏览器版本会记录在事件里。默认仍使用 Playwright 管理的 Chromium。

已验证的具体运行环境与备用 Chromium 来源见 `docs/03_实际验证报告.md`；当前尚未在真实 Windows/macOS 机器执行安装验收。

## 2. 先跑自带示例

```bash
python -m hpt demo --output artifacts
```

此命令自动启动独立本地示例应用，走“首页→设备管理→新增→填写→选择 PCS→保存→刷新确认”。默认要求视觉检查，因此没有配置视觉模型时，正确结果是：功能 `pass`，视觉 `not_checked`，总结果 `INCOMPLETE`。这不是安装失败。

若只想单独检查固定操作与确定性断言，可显式运行功能专项：

```bash
python -m hpt demo --functional-only --output artifacts
```

它明确排除视觉语义验收，不能拿这个结果冒充完整人工测试。故意让按钮被挡住：

```bash
python -m hpt demo --functional-only --mode overlay --output artifacts
```

应得到 `FAIL`，截图中能看到遮挡，设备不会通过其他通道创建。还支持 `http500`、`no_persist`、`wrong_type`、`duplicate_button`、`delayed_commit`、`keyboard_only`、`invisible`、`cleanup_fail` 等夹具故障。

## 3. 查看结果

每次运行会打印实际目录。将下列占位路径替换为它：

```bash
python -m hpt report artifacts/<run_id>
python -m hpt integrity artifacts/<run_id>
python -m playwright show-trace artifacts/<run_id>/trace.zip
```

`report.md` 显示业务动作和截图；`result.json` 是机器结果；`assertions.jsonl` 保存断言；`events.jsonl` 保存动作；`integrity.json` 发现文件丢失或被改动。查看结果不会重新执行业务。

`overall=PASS` 只表示声明范围内的 UI 检查通过；`certification=INCOMPLETE` 表示尚未认证主机隔离及完整人工等价性。原运行不会因后一次成功被覆盖。

## 4. 接真实页面

```bash
python -m hpt init-demo my-case
python -m hpt validate my-case
python -m hpt run my-case --output artifacts
```

`init-demo` 只生成示例，**不会自动知道你的产品控件**。接真实产品前，由实施助手按用户描述修改 `environment.json`、建立真实探路路线、补充独立预期。用户不需要自己读或写定位器。不要直接把演示控件名当成你的页面结构。

每个用例有四个核心文件：`route.json`、`behavior.json`、`environment.json`、`inputs.json`。必须从明确入口开始；输入数据不得与上次运行混淆；业务流程中的按钮不能用接口代替。

详细步骤见 `docs/01_使用与接入指南.md`。

## 5. 多模态探路与文字接力

API 模式：

```bash
python -m hpt explore --intent intent.md --environment environment.json --parameters parameters.json --inputs inputs.json --model vision-model.json --output explorations
```

现有能看图的桌面助手模式：把 `--model vision-model.json` 换成 `--stdio`。程序每次输出图片位置、摘要和请求文件；宿主助手实际读取图片后，提交绑定该图片的 JSON 动作。不能把“返回了正确图片摘要”当成它已经看过图的独立证明。

探索只生成候选，不产生 PASS。由助手依据业务要求另写 `outcomes.json`，再执行：

```bash
python -m hpt prepare-case explorations/<run_id> --outcomes outcomes.json --destination candidate-case
python -m hpt validate candidate-case
python -m hpt run candidate-case --vision-model vision-model.json --output artifacts
```

文字模型可基于冻结业务契约整理已有路线：

```bash
python -m hpt compile candidate-case --model text-model.json --destination route-v2.json
```

Compiler 不允许删除业务步骤、改目标语义或放宽预期。当前它主要承担文字整理、参数定义维护和新修订生成；大幅产品流程变化需要重新探路和业务契约修订。

## 6. 测试、回归与复用

```bash
python -m pytest -q
python -m hpt regression suite.json --output artifacts
python -m hpt publish my-case --registry registry --runs artifacts/<passed_run_id>
python -m hpt recommend device.create --registry registry --inputs my-case/inputs.json
```

`suite.json` 是用例目录字符串数组，路径相对 suite 文件；测试数据准备仍由各环境负责。发布必须有完全匹配的通过记录，不能覆盖既有版本；更新版本必须重放已收录输入。当前复用索引保守地只对实际验证过的相同输入给 `run`，新输入给 `adapt`，不宣称已证明所有参数组合。

## 7. 文件导航

| 路径 | 内容 |
|---|---|
| `src/hpt/` | 全部执行、探路、模型、视觉、报告、复用模块 |
| `tests/` | 规则、模型协议、命令与真实浏览器故障测试 |
| `examples/authored/` | 10 个预先编写的夹具用例 |
| `examples/explored/` | 本次真实看图探路生成的路线及独立预期 |
| `examples/vision-model.example.json`、`examples/text-model.example.json` | 模型连接配置模板，不含密钥 |
| `schemas/` | 由程序模型生成的 JSON Schema；跨字段规则仍需 validate |
| `docs/` | 使用、实现边界、实际验证、原设计文档 |

源码包不包含 `.venv`、浏览器或秘密凭据。浏览器实测截图、Trace、失败样本和本次真实探路在单独的证据包中。

每次运行还在目录旁保存 `<run_id>.evidence.zip` 完整证据快照。迁移或托管文件同步异常时，解压到新的空目录，再执行 `hpt integrity`；不要修改原清单以通过检查。
