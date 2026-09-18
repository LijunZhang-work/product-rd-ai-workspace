# Mutagen：Windows与WSL双向同步详细使用指南

版本：v1.1，2026-09-18。所属目录：Windows与WSL开发环境。

适用对象：Windows上使用公司定制版VS Code、Git及AI工具，WSL Ubuntu中保存另一份工作树，用于产品编译、代码分析和测试；需要两边修改能够增量传递。

本文负责Windows↔WSL同步场景的路径选择、同步配置、冲突处理、Git配合和性能实测；工具盘点、下载安装、通用调用、版本变更和工具验收统一由[工具统一管理与使用指南](../工具接入与共享能力/工具统一管理与使用指南.md)维护。先读取[工具状态与验收报告](../工具接入与共享能力/工具状态与验收报告.md)，确认其中记录对应本机和本次实际执行环境；不能把一台机器上的验证结果套用到另一台机器。

环境依据来自同目录的[01_WSL与磁盘现状只读探查_AI任务书.md](01_WSL与磁盘现状只读探查_AI任务书.md)所产生的**实际盘点结果**，路径、容器与产物组织依据[02_多仓多镜像目标部署与迁移实施指南.md](02_多仓多镜像目标部署与迁移实施指南.md)的实际执行记录。已有结果仍有效时直接继承，只补查缺项或发生变化的部分，不重新执行整套盘点或迁移。本文与这些指南本身都不是已完成的执行报告。

下文保留的是**同步任务配方**。配方中的会话名称、端点、SSH配置和示例目录需要按本机记录替换；通用工具规则发生更新时，以统一指南为准。任务产生的配置、日志和内容校验结果保存在本次同步任务的证据目录中，并从统一报告引用；不在本文件另建一套工具安装台账。

## 1. 先用大白话说清楚

Mutagen不寻找你的仓库。创建同步会话时，给它两端的具体目录，它才知道要管理哪一对文件夹。一端叫alpha，另一端叫beta，只是标识；采用two-way-safe时两边都可以传递变化。

本指南选择Windows主程序＋Ubuntu SSH代理：Windows侧直接访问Windows目录，Linux代理直接访问Ubuntu目录，两端通过SSH通信。代理由Mutagen在首次连接时部署。SSH连接到Ubuntu，不是连进产品容器；容器继续挂载Ubuntu里的代码。这种方式保持公司编辑器和Windows AI的日常入口。

| 角色 | 本指南的职责 | 示例位置，不是已确认的实际路径 |
| --- | --- | --- |
| Windows代码工作树 | 公司编辑器、Windows AI读写；本例在此管理Git | D:\repos\repo1 |
| Mutagen主程序和后台进程 | 保存会话、协调同步 | D:\Tools\Mutagen\v0.18.1 |
| Windows同步配置/记录 | 保存路径对应、参数、验收和操作记录 | D:\DevEnv\sync |
| Windows同步状态数据库 | 保存同步历史等运行状态 | D:\DevEnv\mutagen-state |
| Ubuntu代码工作树 | Linux AI、构建和分析使用 | /home/dev/workspace/repos/repo1 |
| Ubuntu SSH服务 | 接收本机Windows连接，启动代理 | 本例127.0.0.1:2222，必须实测 |
| Ubuntu产物 | build、日志、产品包 | /home/dev/workspace/artifacts/... |

数据盘归属以01的实际盘点为准。Ubuntu的/home路径不透露其VHDX在C盘还是D盘。Mutagen状态和临时数据也可能增长，要纳入容量清单。

## 2. 使用前先确定这五件事

1. 两端确实是独立目录。不要将Windows目录与WSL中指向同一目录的/mnt/d别名互相同步，也不要将已挂载的同一份代码当作两份。
2. 仓库身份、版本和未提交修改已核对。两个目录的同名文件不同，可能是不同产品或分支，不能一律合并。
3. 只有一个同步工具负责这对工作树；旧复制脚本、计划任务、IDE同步扩展需先识别，切换时停止相关写入，不能多套工具来回覆盖。
4. Git操作端明确。本指南默认Windows负责提交/切分支，WSL是同步工作树；特殊情况见第10节。
5. 源码范围与产物范围明确。需要的生成代码、XML、EMAP依赖不能因为在.gitignore里就全部忽略；日志、build、CodeQL数据库等通常放到工作树外。

仅阅读文档不会改变电脑。后面的安装、服务配置、创建/恢复会话会实际改变环境或文件，应由本地AI根据用户已授权的实施范围执行；前置检查和试验目录可以先完成，不要求用户反复确认已经授权的步骤。

## 3. 读取统一工具准备结果

先按统一指南的[现有工具盘点](../工具接入与共享能力/工具统一管理与使用指南.md#inventory)和[Mutagen与SSH](../工具接入与共享能力/工具统一管理与使用指南.md#mutagen)章节读取或补齐本次准备。缺失工具才进入[安装流程](../工具接入与共享能力/工具统一管理与使用指南.md#install)，本文件不再维护安装命令或指定下载版本。

回到本同步任务前，须能从统一报告定位这些实际值：

| 任务需要的输入 | 如何用于下文配方 |
| --- | --- |
| Windows上的Mutagen完整发行目录和可执行路径 | 在当前PowerShell按统一指南设置`$MutagenExe`；配套代理文件不能缺失 |
| 选定的一套OpenSSH客户端 | 统一指南设置`$SyncSshDir`、`$SyncSshExe`、`$SyncScpExe`；手工验证、AI与daemon使用同一套 |
| 同一Windows用户的Mutagen状态目录及SSH路径环境 | 继承经核验的`MUTAGEN_DATA_DIRECTORY`和`MUTAGEN_SSH_PATH`；已有会话先核对，不擅自换状态目录 |
| 目标Ubuntu及SSH服务、用户、公钥认证准备 | 已有入口可用则直接复用；没有时按第4节完成此场景的入口配置 |
| 当前版本对配方所用参数的支持记录 | 核对`create/list/flush`等实际帮助输出；不能忽略未知参数继续执行 |
| 报告版本或摘要、相关工具实例与原始验收证据 | 写入本次任务记录，供后续确认这次究竟用了哪套工具 |

报告只显示“已下载”或“已安装”时，不能直接判定同步已经可用。按统一指南补齐相应执行环境验证后，仍需完成下文的双向同步场景试验。报告尚未盘点时如实填写待查，不能把表中的示例路径当成用户的实际安装路径。

## 4. 配好Windows到Ubuntu的SSH

### 4.1 先检查已有环境

Windows PowerShell：

```powershell
wsl --list --verbose
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in 22, 2222 } |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

进入**实际目标Ubuntu**终端：

```bash
id
cat /etc/os-release
command -v sshd
ss -ltn
ps -p 1 -o comm=
```

若有已配置好的SSH服务，复用其用户、端口和公钥认证；先核对连接到的是正确Ubuntu，不要误连Windows SSH服务或另一个发行版。下面专用端口方式只是在没有可复用入口时的示例，不要求更改已有服务。

### 4.2 复用服务与认证准备结果

OpenSSH服务的缺项安装、客户端选择、专用密钥生成与公钥配置统一按[Mutagen与SSH准备](../工具接入与共享能力/工具统一管理与使用指南.md#mutagen)执行；已完成且仍有效时直接继承，不重装、不重复生成密钥、不重复添加公钥。下文的`$SyncKey`及SSH客户端变量取自该步骤。

本任务需要确认的是：公钥已经对应到**这一个Ubuntu中的这一个用户**，现有服务实际监听何处，以及是否能复用该入口。安装可能启用发行版默认SSH服务；先记录实际监听，不自动停止已有服务。Ubuntu的SSH可能由服务或套接字管理，以有效配置和实际监听为准，不能只改Port就假定生效。只有没有可复用入口时，才使用下一节的独立入口配方。

### 4.3 一个便于首次验证的独立SSH入口

若已有入口可用，跳过本节。以下示例通过独立配置和进程使用2222端口，便于初次试通时不改原ssh.service/socket。选择前确认端口空闲；dev替换为Ubuntu实际普通用户。

新建 `/etc/ssh/sshd_config_mutagen`，不要覆盖同名已有文件：

```text
Port 2222
ListenAddress 127.0.0.1
PidFile /run/sshd-mutagen.pid
HostKey /etc/ssh/ssh_host_ed25519_key
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
AllowUsers dev
UsePAM yes
Subsystem sftp internal-sftp
```

此配置需要已安装OpenSSH、存在对应主机密钥且公钥已放入正确用户账户。主机密钥缺失时按Ubuntu安装流程补齐，不随意替换已有主机密钥。

Ubuntu中先校验，再前台启动；这是实际启动服务：

```bash
sudo install -d -m 0755 /run/sshd
sudo /usr/sbin/sshd -t -f /etc/ssh/sshd_config_mutagen
sudo /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config_mutagen
```

只有校验成功才执行最后一条。最后的终端会保持运行，是正常现象。它适合首次验证；关闭该进程后不能建立新SSH连接，也不应指望同步持续可靠可用。长期运行可在验证后交给systemd管理，见第12节。

此处使用本机回环连接，不需要为了同机同步开放局域网端口。WSL NAT的localhost转发或镜像网络是否可用，仍需实测；连接失败先核对端口、网络模式、服务和公司策略，不直接关闭防火墙或改成任意地址监听。[WSL网络说明](https://learn.microsoft.com/en-us/windows/wsl/networking)、[OpenSSH配置说明](https://man.openbsd.org/sshd_config)

### 4.4 Windows保存一个稳定连接别名

在选定SSH客户端实际读取的用户 `.ssh/config` 中增加下列块，保留原文件其他内容；dev、私钥路径和端口均替换为实际值：

```sshconfig
Host wsl-sync-ubuntu
    HostName 127.0.0.1
    Port 2222
    User dev
    IdentityFile ~/.ssh/id_ed25519_wsl_sync
    IdentitiesOnly yes
    ServerAliveInterval 15
    ServerAliveCountMax 3
```

用同一客户端检查配置和连接：

```powershell
& $SyncSshExe -G wsl-sync-ubuntu
& $SyncSshExe wsl-sync-ubuntu 'id'
& $SyncSshExe wsl-sync-ubuntu 'cat /etc/os-release'
& $SyncSshExe wsl-sync-ubuntu 'command -v scp'
```

首次主机指纹提示，应与Ubuntu中 `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` 输出核对后接受。这里验证的是服务主机密钥，不能和Windows用户公钥混淆。

确认连接正确后再测无交互认证：

```powershell
& $SyncSshExe -o BatchMode=yes wsl-sync-ubuntu 'true'
```

要求退出码为0。若密钥有口令，使用与此SSH实现匹配的凭据代理，并确认Mutagen后台进程能继承该代理访问方式；“在一个终端输过口令”不代表后台能无人值守重连。不要把口令写进脚本。

服务变动、WSL换发行版、端口调整后先重新验证别名。若改用WSL IP，需要匹配服务监听地址，并处理WSL重启后IP变化；本机127.0.0.1方式验证通过后通常更便于日常使用。

## 5. 接真实仓前：先看清楚两端差异

Mutagen记录差异是为了同步，并不提供本指南所需的“完整只读差异审阅流程”。**创建普通会话会开始同步；--paused只创建暂停配置，也不会自动生成完整差异报告。**不能把创建会话当作目录比对。

已有两份工作树，先在停止相关写入的时间窗口，用成熟目录比对工具列出：仅Windows有、仅Ubuntu有、内容不同、类型/链接不同，以及Git身份和文件系统差异。不要只根据大小/修改时间判内容一致。

一个可用的只读内容比对办法是在Ubuntu运行已有rsync，读取Windows挂载目录与Linux目录。下列路径和排除项只是模板，先核对实际范围：

```bash
rsync -rlcn --delete --itemize-changes \
  --out-format='%i|%n%L' \
  --exclude='.git' \
  --exclude='/build/' \
  --exclude='/logs/' \
  --exclude='/artifacts/' \
  '/mnt/d/repos/repo1/' \
  '/home/dev/workspace/repos/repo1/'
```

- `-n`表示演练、不修改文件；不要移除此选项来“顺便修复”。此处--delete仅用于在演练输出标记目标端多余项。
- `-c`按内容校验，首次会读取大量数据，跨文件系统扫描慢是可能的；本步骤用于建立可靠基线，不是日常实时同步路径。
- source末尾的/表示比较目录内部。source是Windows，destination是Ubuntu；目标独有文件可能显示为拟删除项，这只是差异，不代表应该删除它。
- 该命令没有试图完整比较Windows ACL、全部Linux元数据或Git历史。软链接、执行位、大小写、LFS等还需专门核验。
- 退出0只说明命令正常完成，有差异也可以退出0。输出与错误信息要保存；文件在扫描期间变化、读取失败或超时都不能宣称比对完整。

rsync缺失时按统一指南的[工具盘点与选用](../工具接入与共享能力/工具统一管理与使用指南.md#inventory)确认可复用的目录比对工具；确需补装时走统一安装流程。此命令仅作为单次只读差异发现；不用“正向rsync一次、反向再一次”冒充能识别共同历史的双向同步。

对不同项做明确取舍并备份双方独有修改。若两端历史混乱，优先保留旧Ubuntu目录，选择新空的同步工作树路径，合入必须保留的变更后再切换。初次会话没有过去的共同基线，无法知道“另一边缺少文件”究竟是未复制还是过去主动删除，因此不能替你恢复历史意图。

## 6. 先用专用试验目录跑通

以下目录仅放测试文本，不能替换成现有仓库后直接全段运行。

### 6.1 建立全新目录

Windows PowerShell：

```powershell
$LabWin = 'D:\DevEnv\sync-lab\repo-demo'
if (Test-Path -LiteralPath $LabWin) { throw '试验路径已存在，请换一个新路径。' }
New-Item -ItemType Directory -Path $LabWin
[IO.File]::WriteAllText((Join-Path $LabWin 'from-windows.txt'), 'windows-v1', [Text.UTF8Encoding]::new($false))
```

Ubuntu终端（选定用户）：

```bash
# 只有此目录不存在时才创建；已存在则换一个新路径。
test ! -e /home/dev/workspace/sync-lab/repo-demo
mkdir -p /home/dev/workspace/sync-lab/repo-demo
```

两条命令分开执行并检查第一条退出码；不能忽略存在性检查继续复用未知目录。其父目录也需可写。

### 6.2 创建暂停会话，然后人工检查端点

在已设置Mutagen/SSH变量的Windows PowerShell中：

```powershell
$LabCreateArgs = @(
    'sync', 'create',
    '--name=repo-demo',
    '--paused',
    '--mode=two-way-safe',
    '--no-global-configuration',
    '--ignore-vcs',
    '--ignore=.git',
    '--stage-mode=neighboring',
    $LabWin,
    'wsl-sync-ubuntu:/home/dev/workspace/sync-lab/repo-demo'
)
& $MutagenExe @LabCreateArgs
& $MutagenExe sync list --long repo-demo
```

创建前先确认没有同名会话。核对Alpha、Beta、模式、暂停状态和过滤项；保存新生成的会话ID。会话名方便记忆，后续自动化优先用唯一ID，避免同名选中多个会话。

这里--stage-mode=neighboring让临时接收文件靠近同步目录，减少Windows源码在D盘却先写入C盘临时区域的跨卷复制；需要两端父目录可写。如果不满足，调整专用父目录或采用实际验证过的暂存策略，不修改整个磁盘权限。[暂存机制](https://mutagen.io/documentation/synchronization/staging/)

--ignore-vcs用于忽略版本控制元数据，另显式忽略.git名称，用于覆盖子模块/worktree的.git文件情形。需要核验实际过滤效果；不要忽略.gitignore和.gitmodules。

### 6.3 恢复并观察实际同步

```powershell
& $MutagenExe sync resume repo-demo
& $MutagenExe sync flush repo-demo
& $MutagenExe sync list --long repo-demo
& $MutagenExe sync monitor repo-demo
```

检查每条命令退出码。首次连接可能部署代理并做文件系统能力探测、扫描和传输；此后即使主命令退出，后台仍可运行。monitor是实时查看，Ctrl+C退出查看不等于暂停同步。

在Ubuntu确认from-windows.txt为windows-v1，然后在Ubuntu新建from-wsl.txt，回到Windows确认其内容。可以用Get-FileHash与sha256sum交叉核对同一测试文件。不要只看Connected；还要检查扫描/应用问题、冲突及文件本身。

### 6.4 必须完成的最小试验

| 操作 | 预期与验证 |
| --- | --- |
| Windows新增、修改文件 | Ubuntu收到相同字节 |
| Ubuntu新增、修改文件 | Windows收到相同字节；另测低频修改的旧文件 |
| 正常删除一个测试文件 | 已同步过的对应文件在另一端被删除 |
| 重命名测试文件 | 新旧路径最终正确；不要求工具显示为原子rename |
| 暂停，双方把同一测试文件改成不同内容，再恢复 | two-way-safe留下冲突；确认双方修改可取回 |
| 单侧连接中断后重新连上 | 离线修改正确处理，冲突仍可识别 |
| 代码范围外的测试产物 | 按已设范围保持不参与同步 |
| Linux脚本、软链接、大小写边界 | 如工程实际包含，必须单独通过，不能只验普通txt |

试验失败就修正配置并重测相关项；不要直接在真仓换成two-way-resolved掩盖失败。测试结束可暂停会话。若要删除测试目录，先终止该测试会话并确认，再清理明确的测试数据。

## 7. 为正式仓建立一份明确配置

每个仓一对路径，一般一个同步会话；同仓两个产品共用Ubuntu工作树时，不要因为有两个容器就建两个会话同时写同一目录。不同分支/独立工作树则分别配对，不跨接。

示例参数对应表应保存到 `D:\DevEnv\sync\repo1-连接说明.md`，记录：

| 字段 | 示例 |
| --- | --- |
| Windows真实路径 | D:\repos\repo1 |
| Ubuntu发行版/用户 | Ubuntu／dev，实际待替换 |
| Ubuntu真实路径 | /home/dev/workspace/repos/repo1 |
| SSH别名 | wsl-sync-ubuntu |
| Git管理端 | Windows |
| 会话名 | repo1-code |
| 会话ID | 创建后填实际值 |
| 工具依据 | 统一工具报告的版本或摘要、工具实例及其路径/版本快照，不另建安装台账 |
| 排除范围及理由 | 经核对的build/logs等，不照抄未知目录 |
| 两侧内容基线 | 比对时间、版本、摘要、未提交修改与备份位置 |
| 容器挂载 | Ubuntu源路径到各实际容器内路径 |

为该仓新建 `D:\DevEnv\sync\repo1-defaults.yml`，以下为示例：

```yaml
sync:
  defaults:
    mode: two-way-safe
    stageMode: neighboring
    symlink:
      mode: portable
    watch:
      mode: portable
      pollingInterval: 10
    ignore:
      vcs: true
      paths:
        - '.git'
        - '/build'
        - '/logs'
        - '/artifacts'
```

这是Mutagen附加配置文件，不是Docker配置。过滤语法按当前Mutagen模式解释；该文件不自动读取仓里的.gitignore或.dockerignore。根部/build排除不等于所有名为build的子目录都排除；需要哪个范围应依据实测列表补充。不要无依据排除全部.a/.so、生成XML或其他构建输入。[忽略规则](https://mutagen.io/documentation/synchronization/ignores/)

在正式建会话前，暂停旧同步工具并确认两边目录的当前内容基线。随后在Windows创建暂停会话：

```powershell
$RepoCreateArgs = @(
    'sync', 'create',
    '--name=repo1-code',
    '--paused',
    '--no-global-configuration',
    '--configuration-file=D:\DevEnv\sync\repo1-defaults.yml',
    'D:\repos\repo1',
    'wsl-sync-ubuntu:/home/dev/workspace/repos/repo1'
)
& $MutagenExe @RepoCreateArgs
& $MutagenExe sync list --long repo1-code
```

端点和配置核对完成后再resume。正式同步确实会增删改文件，不能一边宣布“只读盘点”，一边运行resume。

配置在创建时锁入会话。后续修改YAML文件不会自动改变已有会话；也不要假设存在可动态更新全部参数的update命令。修改路径/排除项需按第13节重建，避免无意间丢失历史判断。[配置规则](https://mutagen.io/documentation/introduction/configuration/)

## 8. 日常怎么用

`list`、`monitor`、`flush`、`pause`、`resume`、`terminate`的通用调用和注意事项统一见[Mutagen会话操作](../工具接入与共享能力/工具统一管理与使用指南.md#mutagen)。执行时使用第3节取得的真实可执行路径、同一Windows用户、同一状态目录及实际会话ID。

下面只规定本开发场景的操作顺序。`flush`完成一轮同步并不等于锁住工作树；状态输出和文件内容需要一起核对。只有连接成功或命令退出0，不能证明零冲突或构建输入已固定。

### 一次正常的“修改→编译→提交”

1. 在Windows公司编辑器修改，或在Ubuntu由Linux AI修改；避免两边同时改同一文件。
2. 保存文件，停止本次构建输入上的写入，执行flush并检查状态、冲突和必要摘要。
3. 需要稳定输入时暂停同步并冻结编辑，或者从已核验工作树创建明确版本的构建快照；容器使用该份代码。
4. 使用02里的对应镜像、组合和独立输出目录编译。同步状态不代替构建结果验证。
5. 若Ubuntu侧产生需要提交的源码改动，恢复/完成同步并审阅Windows diff，最后在Windows提交/推送。

暂停同步只阻止同步进程更新文件，不能阻止Ubuntu AI或构建脚本直接改源码。真正固定构建输入，需要两端写入约束或独立快照。

## 9. 遇到冲突如何处理

普通单端修改可以自动传递；两端改同一文件但内容不同会产生冲突。two-way-safe的“安全”意味着保留无法安全调和的差异，不是永远不传播删除。修改与删除冲突可能按规则保留修改，使文件重新出现。

标准处理步骤：

1. 用list --long确定实际冲突路径，暂停该会话，并停止相关文件写入。
2. 将两端版本分别复制到**同步根之外**的冲突备份目录，记录路径与摘要。不要在同步目录中创建含业务扩展名的副本让编译自动捡到。
3. 用公司现有diff/merge工具比较；决定保留Windows、保留Ubuntu，或者合成一个新的正确版本。
4. 对普通文件冲突，把经审阅的最终内容分别写到两端同一路径，确认字节一致，再resume与flush，确认冲突消失。
5. 若决定删除，先完成双方备份，再在两端删除对应文件；目录/类型冲突要核对其全部子内容后处理。

不要把reset当作通用修复按钮：它会清除同步历史，下一次以新会话语义重新协调，可能让你预期删除的文件复活。two-way-resolved会让alpha胜出，包括可能覆盖beta修改；本指南不把它用于日常源码同步。[同步模式](https://mutagen.io/documentation/synchronization/)

工具对根目录删除等情况的保护是尽力检测，不能替代备份；批量删除过程中可能已经传播一部分。误删时先暂停所有相关会话，再查看双方和独立备份，不继续同步赌另一边仍完整。[保护机制](https://mutagen.io/documentation/synchronization/safety-mechanisms/)

## 10. Git、子仓与产品构建怎么配合

### 推荐基本形态

Windows保存正式Git仓和.git，负责commit、push、pull、checkout、rebase及子模块版本管理。Ubuntu保存被同步的工作树；在Ubuntu改源码后，变更回到Windows供Git提交。

持续同步.git会涉及索引、对象库和锁，容易产生不一致；本指南明确排除。两边分别有独立.git但只同步工作树也会出现“文件相同、HEAD不同”，不能把两边Git status直接当成同一状态。[官方Git配合建议](https://mutagen.io/documentation/synchronization/version-control-systems/)

### 当前Ubuntu已经是Git仓怎么办

不要直接删.git。先备份双方独有提交、未提交/未跟踪内容、子模块和相关配置。选择新的普通同步工作树路径，或制定保留独立clone的Git交换方案。若两端都必须独立提交，应使用Git的commit/push/fetch/merge或patch管理版本，不让实时工作树同步同时介入切分支等操作。

### 构建依赖Git怎么办

很多脚本会git describe、读取子模块或通过artget拉依赖。先查真实行为，再决定：通过构建参数/旁路manifest提供已核验版本；或者使用独立构建clone，在明确步骤中同步版本和应用工作区改动。不能复制一个孤立HEAD文件假装拥有正确仓库，也不默认照搬部分.git同步作为通用解法。

切分支/pull/rebase前：先把Ubuntu修改同步回来并审阅、等待同步完成，暂停会话，停止构建和Ubuntu写入；在Git端完成操作后，核对新目标与未提交变化，再恢复同步并等待稳定。大量分支变化会产生扫描负担，不应一切换就立刻编译。

### 大仓特别项

- 子模块和嵌套仓：.git可能是文件；过滤Git元数据不应过滤实际子仓源码。.gitmodules等项目文件按需要同步。
- Git LFS：确认工作树里是需要的实际内容还是pointer；Mutagen传当前文件，不替你运行LFS下载。
- 行尾/编码：同步不自动转换CRLF/LF。Windows编辑器、.gitattributes和Linux脚本需一致；若现有仓两侧行尾已不同，先解决，不让同步反复拉扯。
- 可执行位：工具会处理一定的POSIX可执行性，但Windows源端不能凭普通文件内容推断全新shell脚本的执行权限；按工程清单验证，必要时通过显式构建适配处理，不chmod全部文件。
- 权限/所有者：不能要求Windows ACL与Linux uid/gid逐项相同。默认新文件权限可能较严格，容器用不同UID访问时要验证；需要时按现有组权限规则设置端点默认权限，不直接777。[权限模型](https://mutagen.io/documentation/synchronization/permissions/)
- 软链接：portable模式有限制；跨同步根的链接、Windows创建链接权限、Git把链接检出成文本都需要处理。不能用ignore掩盖构建必需链接缺失，也不能在Windows端强用仅POSIX支持的posix-raw。[链接说明](https://mutagen.io/documentation/synchronization/symbolic-links/)

## 11. 速度：怎么测、怎么优化

第一次要扫描和建立历史；日常按变化同步。总耗时由发现变化、扫描/摘要、传输、落盘和排队组成，不只取决于MB/s。

Mutagen的Linux端使用轮询结合有限原生监听，默认轮询间隔在官方说明中为10秒；Windows端有原生递归监听。某些Ubuntu文件改动可能等到轮询才被发现，因此不能承诺两个方向都随时亚秒同步。编译前用flush触发确认，不靠睡固定秒数猜测完成。[监听说明](https://mutagen.io/documentation/synchronization/watching/)

优化顺序：

1. 同步根只包含所需工作树，产物、缓存、数据库尽量位于根外；过滤前核对用途。
2. Windows端本地访问NTFS，Ubuntu代理本地访问Linux文件系统；不要将两端都绕到/mnt/d或UNC后再指望同等扫描性能。
3. 大量小文件先看扫描CPU/磁盘、进程和实际排除效果；先定位瓶颈，不盲目降低轮询间隔或提高并发。
4. 检查暂存和源码是否同卷，容量是否充足。neighboring是本方案的候选，仍需确认实际临时目录及权限。
5. 先用默认portable监听和现有扫描配置；必要时比较轮询或扫描模式，保存每次参数及结果，不凭一次快的结果宣布长期稳定。[扫描机制](https://mutagen.io/documentation/synchronization/probing-and-scanning/)
6. 公司安全软件可能影响文件I/O；用测量确认后按公司既有流程处理，不关闭防护来获取漂亮数字。

建议验收记录表：

| 场景 | 文件数/字节 | Windows→WSL耗时 | WSL→Windows耗时 | 内容校验 | 冲突/问题 |
| --- | --- | --- | --- | --- | --- |
| 首次完整同步 | 实测 | 实测 | 若测试则记 | 覆盖范围明确 | 实测 |
| 改10个普通源码 | 实测 | 实测 | 实测 | 摘要一致 | 实测 |
| 修改低频旧文件 | 实测 | 实测 | 实测 | 摘要一致 | 实测 |
| 大批量分支变更 | 实测 | 实测 | 不适用或实测 | 相对路径集合及摘要 | 实测 |
| 中断后恢复 | 实测 | 实测 | 实测 | 无漏项 | 实测 |

可用PowerShell计时一次主动同步，但它只测flush这一段，不代表保存到远端可见的完整延迟：

```powershell
$SyncTimer = [Diagnostics.Stopwatch]::StartNew()
& $MutagenExe sync flush repo1-code
$SyncExitCode = $LASTEXITCODE
$SyncTimer.Stop()
[PSCustomObject]@{ Seconds = $SyncTimer.Elapsed.TotalSeconds; ExitCode = $SyncExitCode }
& $MutagenExe sync list --long repo1-code
```

要测自动检测延迟，记录一次已知文件修改的时刻，再观察另一端出现同一内容摘要的时刻；取多个代表样本。机器忙闲、缓存、工具版本和过滤范围都写进记录。

## 12. 重启后如何恢复，怎么长期运行

### 最初采用手动、可观察的启动顺序

1. 启动正确Ubuntu，确认专用SSH服务已运行；前台试验模式需重新运行第4节的sshd命令。
2. 打开含相同Mutagen路径、数据目录和SSH配置的Windows环境。
3. 启动daemon，检查已有会话；不要每次开机都create相同会话。
4. 对需要运行的会话resume，flush后检查问题；刻意暂停的会话不要自动全部恢复。

```powershell
& $MutagenExe daemon start
& $MutagenExe sync list --long
& $MutagenExe sync resume repo1-code
& $MutagenExe sync flush repo1-code
```

Windows关闭终端不一定关闭Mutagen后台；关机/WSL停止会影响连接。WSL启动后的服务状态要实际检查，不能假定每台机器都能自动恢复。

### 验证后再做自启动

Ubuntu若使用systemd，可为第4节独立sshd配置创建专用服务；用 `systemctl cat` 确认同名服务未存在，保留既有ssh服务，避免复用或覆盖。建议单元模板如下，需核对本机路径：

```ini
[Unit]
Description=SSH endpoint for local Windows WSL synchronization
After=network.target

[Service]
Type=simple
ExecStartPre=/usr/bin/install -d -m 0755 /run/sshd
ExecStartPre=/usr/sbin/sshd -t -f /etc/ssh/sshd_config_mutagen
ExecStart=/usr/sbin/sshd -D -e -f /etc/ssh/sshd_config_mutagen
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

将其作为新建的 `/etc/systemd/system/mutagen-sshd.service`，校验后停止本指南前台试验进程，再 `systemctl daemon-reload` 和 `systemctl enable --now mutagen-sshd.service`。检查实际监听和日志；WSL仍需处于运行状态。无systemd时，继续手动方式，或让本地AI依据现有WSL启动机制提供等价管理，不为同步先重构整个系统。

Windows计划任务可在用户登录后启动一个专用脚本：明确相同exe、两项环境变量、目标发行版、SSH连通检查和daemon start，再按明确策略恢复特定会话。要使用同一Windows用户；不以SYSTEM运行导致另一份状态/凭据。失败记录日志，不后台无限创建会话。

Mutagen的daemon register自动登录启动在官方文档中标为实验性，不把它当作本指南默认成熟部署路径。带口令密钥在重启后是否能无人值守使用，需与公司允许的凭据管理方式一起验收。

## 13. 改路径、加仓、升级和退出

### 增加仓2

完成仓2身份与差异审查，复制一份配置说明，使用新的Windows/Ubuntu根路径和唯一会话名创建暂停会话，核对后恢复。不要同步总的workspace或整个home，把状态、产物、缓存和其他仓一起包进去。

### 路径或过滤配置变了

1. 停止写入，flush并审阅冲突，暂停旧会话，备份实际内容和旧配置/ID。
2. 确认新路径是迁移后的同一工作树，且排除项不会造成应保留文件消失或旧文件重新出现。
3. 终止旧会话后，按新参数创建暂停会话；不要让两个会话重叠写同一组目录。
4. 重新核对内容基线再恢复。新会话没有旧同步历史；旧状态不能靠同名会话自动继承。

只迁Ubuntu的VHDX到D盘、Linux路径和SSH身份保持不变时，未必需要重建会话。先暂停并停止写入，迁移完成后验证连接、路径身份及内容，再恢复原会话。

### 升级工具

按统一指南的[Mutagen版本变更与状态继承](../工具接入与共享能力/工具统一管理与使用指南.md#mutagen)执行，并更新统一报告。升级后，本任务要补做受到影响的连接、双向同步和代表性冲突试验；旧版本的场景证据不能自动算作新版本已通过。不要通过创建同路径新会话掩盖状态目录或代理兼容问题。

### 暂时停用或彻底不用

暂停适合以后继续；terminate只删除同步会话，不会清除两端源码，也不会卸载SSH服务。停用后若两边各自继续改，未来接回要重新审查差异。卸载仅移除本次明确安装的工具/专用服务，不动公司共有SSH、Git或其他会话。

## 14. 常见故障：先看哪儿

| 现象 | 优先核对 | 不应直接做的事 |
| --- | --- | --- |
| SSH连接拒绝/超时 | 正确发行版、sshd进程、2222监听、localhost转发、端口是否被Windows占用 | 关闭防火墙、任意开放全网 |
| 手动SSH成功，Mutagen失败 | 实际SSH exe、daemon继承的MUTAGEN_SSH_PATH、配置与密钥代理环境、scp传输 | 反复换密码或重建仓 |
| 找不到代理或代理部署失败 | 发行包是否完整、Ubuntu home可写、scp可用、执行权限/挂载选项、登录脚本干扰 | 只复制一个exe、chmod整个系统 |
| 看不到旧会话 | Windows用户、MUTAGEN_DATA_DIRECTORY、daemon版本是否相同 | 立刻创建同路径第二条会话 |
| Connected但文件没到 | 是否paused、实际路径、过滤、扫描/暂存/应用错误、冲突、端点只读 | 仅凭连接状态判完成 |
| Ubuntu改了要等几秒才到 | Linux轮询/有限监听、文件是否低频、扫描耗时 | 宣称工具漏同步或强设零轮询 |
| 文件不断来回变化 | 双方AI/格式化器并发写、旧同步任务、行尾规则、生成代码写回 | 改成强制alpha覆盖 |
| 容器读不到新文件 | 容器挂载是否指向这份Ubuntu工作树、UID/GID和文件权限 | 重新复制到容器里掩盖映射错误 |
| C盘突然增长 | Windows状态目录、暂存策略、Ubuntu/Docker数据盘实际位置 | 直接删除.mutagen或VHDX |
| 根目录消失/大批冲突 | 暂停，查挂载、目录迁移、双方数据和独立备份 | 把reset当作自动修复 |
| 出现软链接/大小写问题 | Windows文件系统行为、链接权限、工程要求和模式限制 | 静默忽略构建必需文件 |
| 修改YAML后行为没变 | 已有会话配置在创建时锁定 | 以为重启daemon会自动加载新会话参数 |

## 15. 本地AI的完成标准和交付

本指南给出场景配方，通用工具准备与验收按唯一指南执行。完整Windows↔WSL链路仍需本地实测；统一报告证明工具具备何种能力，本任务证据证明这一对工作树的同步是否正确，二者不能互相代替。按统一指南的[真实执行证据](../工具接入与共享能力/工具统一管理与使用指南.md#evidence)留存记录，并依[报告维护规则](../工具接入与共享能力/工具统一管理与使用指南.md#report)更新或引用结果。本地AI应交付：

- 已核对的两端路径、所属卷、发行版/用户；所用统一工具报告的版本或摘要与工具实例；实际会话ID和参数文件。
- 初始差异报告及合并/保留决策，Git操作端、子模块/LFS/生成依赖处理方式。
- 双向新增修改删除、冲突、中断恢复、性能与容器访问验证记录。
- 日常启动/暂停/恢复说明，自启动若未验证明确标出，不能用“已设置任务”代替重启验收。
- 已知不支持项、需要继续适配的构建元数据，以及停用/回退步骤。

可直接给AI的任务：

> 请依本指南为我的Windows与目标Ubuntu建立可验证的Mutagen同步方案。先读取“工具统一管理与使用指南.md”和“工具状态与验收报告.md”，只补查失效或缺失项，工具安装与通用调用只按该唯一指南执行。复用“Windows与WSL开发环境”已有的实际盘点和部署结果，确认真实路径和现有两端修改，先在专用试验目录验证，不把正式仓当试验数据。保留公司版编辑器和Windows AI入口，明确Git管理端及WSL构建对Git元数据的需求。使用固定的Mutagen/SSH实现和状态目录，配置two-way-safe、明确排除范围；先创建暂停会话，核对端点后按已有授权启用。完成双向、冲突、中断恢复及本机性能测量，保存真实命令、配置、会话ID、所用工具报告版本和验证结果，将任务证据挂接到统一报告。遇到失败先定位原因，不静默改成强制覆盖、删除旧代码或重建同步历史。

## 16. 资料与验证范围

本文的同步配方沿用已核对的Mutagen官方同步、监听、配置和生命周期资料，以及v0.18.1的create/flush/list命令定义；这不是指定必须安装该版本。工具安装和通用验收资料由唯一指南集中维护；SSH服务片段按OpenSSH配置规则编写。官方资料可能早于所装工具，具体选项和平台行为以所装版本help及测试为准。

可复核来源：

- [Mutagen安装](https://mutagen.io/documentation/introduction/installation/)、[正式发行包](https://github.com/mutagen-io/mutagen/releases)
- [SSH传输](https://mutagen.io/documentation/transports/ssh/)、[daemon及状态目录](https://mutagen.io/documentation/introduction/daemon/)
- [配置](https://mutagen.io/documentation/introduction/configuration/)、[忽略规则](https://mutagen.io/documentation/synchronization/ignores/)
- [同步模式](https://mutagen.io/documentation/synchronization/)、[命令操作](https://mutagen.io/documentation/introduction/getting-started/)
- [监听](https://mutagen.io/documentation/synchronization/watching/)、[扫描](https://mutagen.io/documentation/synchronization/probing-and-scanning/)、[暂存](https://mutagen.io/documentation/synchronization/staging/)
- [Git](https://mutagen.io/documentation/synchronization/version-control-systems/)、[权限](https://mutagen.io/documentation/synchronization/permissions/)、[软链接](https://mutagen.io/documentation/synchronization/symbolic-links/)、[异常保护](https://mutagen.io/documentation/synchronization/safety-mechanisms/)
- [OpenSSH服务配置](https://man.openbsd.org/sshd_config)、[微软WSL网络](https://learn.microsoft.com/en-us/windows/wsl/networking)
- [v0.18.1 create命令源码](https://github.com/mutagen-io/mutagen/blob/v0.18.1/cmd/mutagen/sync/create.go)、[flush命令源码](https://github.com/mutagen-io/mutagen/blob/v0.18.1/cmd/mutagen/sync/flush.go)

本文没有在用户电脑执行安装、同步或性能测试，也未声称所有文件系统特性可无差别迁移。它提供的是可由本地AI逐步执行和验收的方案。
