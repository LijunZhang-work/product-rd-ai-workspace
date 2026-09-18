# WSL与磁盘现状只读探查：AI任务书

版本：v1.0，2026-09-18。执行位置：用户本机Windows、对应WSL发行版，以及已经在运行且与任务有关的容器。本文是执行指南，不是已经完成的本机探查报告。

配套图解：[04_WSL与Docker关系图解.md](04_WSL与Docker关系图解.md)。先按图理解层级、源码与容器挂载、三组独立产物；图中的路径和D盘位置都是示例，实际以本机证据为准。

## 1. 先读：本次到底要解决什么

用户目前知道Windows和WSL中各有代码，WSL中可能有两个编译镜像、两个代码仓，但不清楚完整目录、是否有重复副本、镜像与仓库如何挂载。公司使用定制版VS Code，Windows上还有AI工具；不能默认支持标准VS Code的所有远程扩展。现有WSL整理方案尚未落实。

本次必须回答：

1. 电脑有哪些卷和物理磁盘，C、D是否同一块磁盘，分别是SSD、HDD还是尚不能判断？
2. WSL、各Ubuntu数据、Docker数据、源码、编译产物、交换文件和备份分别占用哪个盘？不能只回答“WSL在D盘”。
3. 每个重要目录是谁创建/使用的、是什么用途、是否是副本、链接、挂载或空目录？
4. 镜像、容器、代码仓、产品目标和实际编译入口之间有哪些已证实的对应关系？
5. 哪些现状已符合“按仓组织源码、按编译组合隔离配置和产物”，哪些仍需整理？

先保留现状，依据证据解释，再使用配套《02_多仓多镜像目标部署与迁移实施指南.md》制定方案。

## 2. 执行边界与记录方式

“只读探查”指不改变被调查的源码、配置、挂载、镜像和目录组织；允许在单独结果目录写报告。查询可能产生访问时间、程序日志等正常副作用，不宣称位级零变化。

- 不删除、移动、覆盖目录，不启动同步，不运行清理、压缩、磁盘基准写入测试或迁移。
- 不执行未知构建脚本、未知仓库初始化脚本，不运行镜像中的默认入口来猜用途。
- 不自动启动已停止的容器或新的Docker引擎。运行WSL内部命令会启动对应发行版和服务；先记录原运行状态，再在现有任务授权范围内决定是否启动，并记下这一变化。
- 没有权限就记录“未能读取”；不修改ACL、所有者、Docker socket权限或服务配置来绕过。
- 不将整个环境变量、凭据文件、SSH私钥或Docker认证配置写进报告。容器命令行、挂载路径、远程地址也可能含敏感信息，外发时脱敏；本地保留必要原始证据。
- 大仓先收集元数据，再做限定范围内容比对；不直接对所有盘、所有容器层和/proc进行递归全文扫描。
- 不将“目录名像build”“文件夹为空”“容器已停止”当成可删除证据。

为每条证据记录：编号、时间及时区、执行环境、完整命令/路径、退出码、输出、覆盖范围、权限或截断问题。结论使用“已证实／有线索待核对／未能检查”，不能把未知写成不存在。

结果输出目录由本地AI先选择现有可写且空间足够的位置，记明完整路径。建议结果文件：现状总报告.md、磁盘与占用.csv、目录用途.csv、仓库身份与差异.csv、编译关系.csv、待确认项.md和raw/。这些是执行后生成的结果，不是本文已经提供的实测材料。

## 3. Windows：查清C、D究竟是什么盘

以下命令在Windows PowerShell运行，不在Ubuntu bash中运行。缺少Storage模块或权限时保存报错，补用Windows磁盘管理和任务管理器的磁盘页面；不要安装不明工具替代。

```powershell
Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, Size, SizeRemaining, HealthStatus
Get-Partition | Select-Object DiskNumber, PartitionNumber, DriveLetter, AccessPaths, Size
Get-Disk | Select-Object Number, FriendlyName, SerialNumber, UniqueId, BusType, Size, PartitionStyle, HealthStatus
Get-PhysicalDisk | Select-Object FriendlyName, SerialNumber, UniqueId, MediaType, BusType, Size, HealthStatus
```

具体核对C、D的分区到磁盘关联：

```powershell
Get-Partition -DriveLetter C | Get-Disk
Get-Partition -DriveLetter D | Get-Disk
```

D不存在、不是普通本地卷或命令不适用时如实记录。不要凭Get-PhysicalDisk输出顺序或DeviceId猜盘符；应通过分区到Get-Disk的关联，再结合UniqueId/序列号/型号核对物理设备。

判断规则：

- 普通直接连接磁盘中，C、D映射到同一DiskNumber，通常是同一磁盘的不同分区，不代表两倍物理容量。
- Storage Spaces、RAID、虚拟磁盘和其他抽象设备需要继续查询对应存储层；不要把逻辑磁盘号当作底层物理盘的最终证明。
- MediaType为Unspecified、RAID或虚拟设备遮蔽信息时，标为未知。BusType为SATA并不能单独判断SSD/HDD；不要凭C、D盘符判断速度。
- 查硬件类型只能支持性能判断，不能得出“实际编译快多少”。本轮不跑大量写入压测；后续需要时用相同工程和缓存条件做代表性实测。

## 4. Windows：WSL发行版与数据文件位置

```powershell
wsl --version
wsl --status
wsl --list --verbose
wsl --help
Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' |
ForEach-Object {
    [PSCustomObject]@{
        Distribution = $_.GetValue('DistributionName')
        BasePath = $_.GetValue('BasePath')
        VhdFileName = $_.GetValue('VhdFileName')
        WslVersion = $_.GetValue('Version')
    }
} | Format-List
```

注册表项只读取。VhdFileName可能缺失；在实际BasePath下限定查看顶层文件，核对真实VHDX名称，不把猜出的ext4.vhdx当实测结果。`\\?\D:\...`仍表示D盘。WSL 1与WSL 2分别说明，不能给WSL 1强套VHDX模型。

还要检查：

| 对象 | 探查入口 | 解释要求 |
| --- | --- | --- |
| Ubuntu根文件系统 | 注册BasePath＋实际VHDX＋发行版挂载表 | 代码如果确实在该根文件系统内，增长占用此VHDX所在卷 |
| WSL组件/Ubuntu启动器 | Windows应用安装信息，必要时Get-AppxPackage的Name、InstallLocation | 程序安装位置与发行版数据位置分别记录 |
| WSL交换文件 | 用户配置文件 `.wslconfig` 的相关项，以及实际存在的交换文件路径 | 配置值与实际文件分别留证；不能仅凭默认路径声称已存在 |
| Docker Desktop | 当前设置的Disk image location及实际数据文件 | 不假定随Ubuntu一起存放，也不把默认位置当事实 |
| Windows源码副本 | 用户提供路径、编辑器最近工作区、现有同步配置 | 只查相关范围，记所在卷 |
| 导出的Ubuntu备份、镜像tar和旧VHDX | 已知工作目录、备份目录和相关配置 | 注册中的正在用的数据与离线备份分开 |
| 日志、缓存、临时文件 | 已确认的WSL/Docker/工具配置位置 | 单独列出仍留在C盘的项目 |

读取用户配置时，在PowerShell使用系统已有的USERPROFILE等路径只读定位，不改变这些环境变量。仅提取 `.wslconfig` 的磁盘/交换/资源相关项，不整份转储无关配置。

在已确认路径下用 `Get-Item -LiteralPath '实际路径'` 查询文件长度和属性。注意：VHDX文件Length、NTFS实际占用空间、Ubuntu内df/du用量是不同口径。稀疏文件可用资源管理器“占用空间”或适用的系统工具补证；未量到实际分配字节就标明仅为文件逻辑长度。不能把Ubuntu内部目录大小再加到VHDX大小里算作额外占用。

## 5. Ubuntu：目录、挂载与真实代码位置

对每个相关发行版分别记录名称、运行状态、用户和根挂载。不要把某个Ubuntu的结果套到另一个发行版。以下为Ubuntu shell命令：

```bash
cat /etc/os-release
id
pwd
ls -ld /home /root /workspace /work /opt /srv /mnt
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS
 df -hT
```

不存在的目录或某版本不支持的lsblk列保留说明，按本机帮助替换。不要隐藏错误之后宣布目录齐全。

从用户已知路径、容器Mounts、构建入口和编辑器配置出发建立候选目录清单。对每个候选实际路径检查：

```bash
ls -ld -- '/实际候选目录'
readlink -f -- '/实际候选目录'
findmnt -T '/实际候选目录'
stat -c '%d:%i %U:%G %a %n' -- '/实际候选目录'
```

确认用途后，按需执行 `du -x -h --max-depth=1 -- '/实际候选目录'`。这可能很慢；限定范围、设定执行预算，并保存未扫描区域，不为了总数随意跟随软链接或重复扫描挂载别名。

每个路径最终必须回答：

1. 是Ubuntu普通目录、Windows挂载路径、软链接、绑定挂载、命名卷，还是容器内部路径？
2. 最终落到哪个文件系统和哪份Windows磁盘数据？追踪到C/D，追不到则标为未知。
3. 所有者和可写性是什么？`/home/仓名`并不必然错误，也不应未经核对移动到用户home。
4. 空目录是否真为空，是否有隐藏文件、读取失败、断开的链接、当前没有挂载、被挂载遮住的旧内容？

容器内的设备号/ inode不能简单跨命名空间比较。优先以Mounts和两侧路径内容证据确定关系。

## 6. Docker：先找引擎，再查镜像和容器

Windows与Ubuntu中的docker命令可能连接不同引擎。同一个镜像名也可能出现在不同引擎。先在已有环境分别查询：

```text
docker context show
docker context ls
docker version
docker info --format '{{json .DockerRootDir}}'
docker image ls --digests --no-trunc
docker ps -a --no-trunc
docker system df -v
docker volume ls
```

只对实际当前/相关context检查其Endpoint；不要为了查询切换全局context。记录DOCKER_HOST、DOCKER_CONTEXT是否设置及脱敏后的有效连接目标，综合context、环境覆盖和daemon身份判断。引擎不可达就是受阻，不等于无镜像。

对已发现的相关容器ID，定向提取：

```text
docker inspect --format '{{json .Mounts}}' 实际容器ID
docker inspect --format '{{.Image}}' 实际容器ID
docker inspect --format '{{json .Config.Image}}' 实际容器ID
docker inspect --format '{{json .Config.WorkingDir}}' 实际容器ID
docker inspect --format '{{json .Config.Entrypoint}}' 实际容器ID
docker inspect --format '{{json .Config.Cmd}}' 实际容器ID
docker inspect --format '{{json .State.Status}}' 实际容器ID
```

命令参数先审阅脱敏，不直接转储全部Config.Env。需要查Compose来源时，定向读取其project/service/config路径标签，不能据标签存在就认为文件仍在或内容未变。

区分三种存储：

- bind：Source对应引擎能访问的宿主目录，Destination是容器入口；不是自动复制。远程引擎的Source属于远程主机，不能在本机同名目录寻找；Docker Desktop还有路径转译，需核对到真实Windows/WSL位置。
- volume：通过volume inspect查看Mountpoint与驱动，再确认所属引擎数据盘；不能自动当作Ubuntu用户目录。外部驱动可能在其他存储上。
- 无对应挂载的写入路径：可能在容器可写层内，记录持久化风险；不要为查看它自动启动或删除容器。

若已经在运行的容器需要补查，可使用只读的pwd/findmnt/stat等命令；执行docker exec本身会启动辅助进程，明确记录，不运行业务入口。

Docker Desktop与Ubuntu内原生Docker都可能存在；这轮只记录有效连接与遗留配置，不擅自卸载任何一套。DockerRootDir中的Linux路径不直接证明数据位于用户Ubuntu，要先确定引擎归属。

镜像共享层不可重复求和，多个tag可能指向同一镜像ID。Docker逻辑用量不能与承载它的VHDX用量相加后声称为磁盘总占用。

## 7. 代码仓身份与Windows／WSL差异

对确认的仓库分别记录：根路径、仓库类型、HEAD、分支、子模块/子仓、未提交修改、未跟踪文件、git-dir/common-dir、LFS/外部二进制依赖、现有同步方式。

```bash
git --no-optional-locks -C '/实际仓库' rev-parse --show-toplevel
git --no-optional-locks -C '/实际仓库' rev-parse HEAD
git --no-optional-locks -C '/实际仓库' rev-parse --git-dir --git-common-dir
git --no-optional-locks -C '/实际仓库' status --porcelain=v1 -uall
git --no-optional-locks -C '/实际仓库' submodule status --recursive
```

大型仓库先估算未跟踪文件规模；需要完整清单时再运行-uall并记录耗时。未运行完整清单就明确覆盖缺口。无Git元数据可能只是同步工作树，不直接判为坏仓。Git失败也可能来自权限/safe.directory，不修改全局Git安全设置来掩盖问题。

两个同名目录分类为：同一挂载对象、链接、Git worktree、独立clone、普通同步副本、未知。相同HEAD不证明工作区相同；同名、相同大小/mtime也不证明文件内容相同。

正式双向同步前需要差异清单：相对路径、仅左/仅右、内容不同、类型/权限/软链接差异、大小写冲突。先只读枚举两侧，再对需要精确核验的文件比较字节摘要；保存算法、范围、排除项和两侧变化检测。源码正在改动时不能把一次比对称为一致快照；安排短暂静止窗口或标记不稳定文件重查。机器上已有成熟只读目录对比工具可复用；不要把Mutagen启动同步当作差异预览。

调查现有同步脚本、计划任务和配置的明确相关项，判断复制、增量、双向还是挂载。Windows工具能读WSL路径，不等于其Git、插件或AI命令执行也支持WSL；本轮先盘点支持情况，实际写入测试留到02。

## 8. 找到真实编译入口与产物

读取相关Compose、构建脚本、IDE task、镜像启动脚本和历史成功构建日志，不能只凭仓名猜产品目标。

每条组合记录：仓ID、产品/目标ID、代码版本、镜像tag和不可变ID/digest、引擎context、容器ID、构建入口、工作目录、源码挂载、build/log/package实际路径、权限、是否会向源码树写入。同仓可对应多个产品；同镜像可供多个仓使用；“能创建容器”不等于组合能够成功编译。

重点找编译中间文件、最终包、ELF/map、分析数据库、缓存在哪里。产物如果在容器内却没有挂载，明确标出；当前未见产物，不能编造曾经的输出位置。

## 9. 输出与验收

### 9.1 用户能看懂的现状摘要

先用一页中文回答：C盘主要有哪些相关数据、D盘有哪些；C/D是什么磁盘关系；Ubuntu真实代码在哪儿；哪些同名目录是同一份；每个容器如何使用仓库和产物；当前最大空间/路径问题是什么。

### 9.2 必须交付的表

| 表 | 最低字段 |
| --- | --- |
| 磁盘与占用 | 卷、底层设备、介质判断、总/剩余容量、对象路径、对象归属、大小口径、是否与其他项重复计量、证据 |
| 目录用途 | 完整路径、所在环境、规范路径、文件系统、C/D归属、用途、所有者、关系类型、活跃使用证据、未知项 |
| 仓库身份与差异 | 仓ID、各侧路径、HEAD/修改、Git元数据、关系分类、差异覆盖、同步工具与状态 |
| 编译关系 | 仓、产品目标、引擎、镜像ID、容器、真实挂载、构建入口、产物位置、证明程度 |

### 9.3 图

分别输出“现状位置图”和“目标建议图”，不能混画。沿用用户已理解的Windows→WSL→Ubuntu嵌套表达，多个容器逐个画，源码与产物放到真实所属位置；实际为Docker Desktop时单独画引擎归属。每条关键连接关联证据编号。不能把构想里的/home/dev/workspace当作现存目录。

### 9.4 完成条件

能解释每个已知仓、镜像、容器；能解释C/D相关占用及测量缺口；能区分真实副本与挂载；形成可执行的下一阶段建议。保留无法检查项及解决条件，不用“全部正常”替代证据。

## 10. 直接交给本地AI的执行指令

> 请按本任务书调查我的Windows＋WSL＋Ubuntu＋Docker现状。先只读盘点，允许在独立结果目录保存报告，暂不迁移、清理、同步或运行产品构建。确认C、D卷到磁盘的关联、介质与容量；逐项确认发行版VHDX、Docker数据、源码、产物、交换和备份的位置及占用口径。查清每个相关目录的真实含义，辨认副本、链接、worktree与挂载；核对仓、产品目标、镜像、容器和构建入口。先完成能完成的调查，再集中列出必须补充的信息。输出带证据的现状报告、表格和嵌套关系图，最后依据02写出针对本机的实施清单；本轮不实际执行迁移。

## 官方依据

- [WSL磁盘与VHDX定位](https://learn.microsoft.com/en-us/windows/wsl/disk-space)：目录、虚拟磁盘与用量的不同层次。
- [WSL基本命令](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)、[WSL配置](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)：本机版本仍以help和实际配置为准。
- [Get-PhysicalDisk](https://learn.microsoft.com/en-us/powershell/module/storage/get-physicaldisk)、[Get-Partition](https://learn.microsoft.com/en-us/powershell/module/storage/get-partition)：硬件信息与分区关联。
- [Docker Desktop WSL后端](https://docs.docker.com/desktop/features/wsl/)：引擎、发行版集成和独立数据位置。
- [Docker绑定挂载](https://docs.docker.com/engine/storage/bind-mounts/)：宿主与容器路径、远程引擎及挂载遮蔽。

本文中的命令未在用户Windows/WSL机器执行；应保存实际运行结果，不将文档示例当成检测通过。
