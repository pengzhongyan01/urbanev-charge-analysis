<#
====================================================================
 start.ps1 —— UrbanEV 后端一键启动 / 停止（D14 交付物）
====================================================================
 作者：杨姗姗（D 岗）
 用途：在任意一台 Windows 机器上启动后端，并自检是否真的起来了。
       不使用任何绝对路径，脚本放在 backend 同级目录即可。

 用法：
   .\start.ps1                        # 默认 8080 端口启动
   .\start.ps1 -Port 18080            # 指定端口
   .\start.ps1 -Stop                  # 停止已启动的实例（按端口找）
   .\start.ps1 -DbPassword "xxx"      # 指定数据库密码（覆盖配置里的默认值）
   .\start.ps1 -Check                 # 只做环境自检，不启动

 说明：
   - 优先用 JAVA_HOME 下的 java，其次用 PATH 里的 java
   - 启动成功后轮询 /api/health，最多等 60 秒
   - 找不到 JDK 17 / jar 不存在 / 端口被占用，都会给出中文提示并退出
====================================================================
#>
[CmdletBinding()]
param(
    [int]$Port = 8080,
    [string]$DbHost = "127.0.0.1",
    [int]$DbPort = 3306,
    [string]$DbName = "uev_charge",
    [string]$DbUser = "root",
    [string]$DbPassword = "",
    [string]$JarPath = "",
    [string]$CacheType = "auto",
    [switch]$Stop,
    [switch]$Check
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host "  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Write-Warn2($msg){ Write-Host "  [WARN] $msg" -ForegroundColor Yellow }
function Write-Err2($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "==================================================" -ForegroundColor White
Write-Host " UrbanEV 后端一键启动  ·  D14" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor White

# ---------------------------------------------------------------- 0. 停止模式
if ($Stop) {
    Write-Step "查找占用 $Port 端口的 java 进程..."
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) { Write-Warn2 "端口 $Port 上没有监听进程，可能已经停了"; exit 0 }
    foreach ($c in $conns) {
        try {
            Stop-Process -Id $c.OwningProcess -Force
            Write-Ok "已停止进程 PID=$($c.OwningProcess)"
        } catch {
            Write-Err2 "停止失败：$($_.Exception.Message)"
        }
    }
    exit 0
}

# ---------------------------------------------------------------- 1. 找 JDK
Write-Step "[1/6] 检查 Java 环境..."
$javaExe = $null
if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME "bin\java.exe"))) {
    $javaExe = Join-Path $env:JAVA_HOME "bin\java.exe"
} else {
    $cmd = Get-Command java -ErrorAction SilentlyContinue
    if ($cmd) { $javaExe = $cmd.Source }
}
if (-not $javaExe) {
    Write-Err2 "没找到 java。请安装 JDK 17 并配置 JAVA_HOME。"
    exit 1
}

# 解析版本号（java -version 输出到 stderr）
$verOut = & $javaExe -version 2>&1 | Out-String
if ($verOut -match '"(\d+)') {
    $major = [int]$Matches[1]
    if ($major -lt 17) {
        Write-Err2 "当前 JDK 版本为 $major，本项目需要 17 及以上（Spring Boot 3.x 不支持 8）。"
        Write-Warn2 "请设置 JAVA_HOME 指向 JDK 17，例如：`$env:JAVA_HOME='C:\devtools\jdk\jdk-17'"
        exit 1
    }
    Write-Ok "JDK 版本 $major（$javaExe）"
} else {
    Write-Warn2 "无法解析 JDK 版本，继续尝试启动"
}

# ---------------------------------------------------------------- 2. 找 jar
Write-Step "[2/6] 定位 jar 包..."
if (-not $JarPath) {
    $candidates = @(
        (Join-Path $scriptDir "target\uev-charge-analysis.jar"),
        (Join-Path $scriptDir "backend\target\uev-charge-analysis.jar"),
        (Join-Path (Split-Path -Parent $scriptDir) "backend\target\uev-charge-analysis.jar")
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $JarPath = $c; break } }
}
if (-not $JarPath -or -not (Test-Path $JarPath)) {
    Write-Err2 "没找到 jar 包。请先执行：mvn -DskipTests package"
    Write-Warn2 "期望位置：backend\target\uev-charge-analysis.jar"
    exit 1
}
Write-Ok "jar：$JarPath（$([math]::Round((Get-Item $JarPath).Length/1MB,1)) MB）"

# ---------------------------------------------------------------- 3. 端口占用
Write-Step "[3/6] 检查端口 $Port ..."
$busy = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    Write-Err2 "端口 $Port 已被占用（PID=$($busy.OwningProcess)）。"
    Write-Warn2 "换个端口： .\start.ps1 -Port 18080    或者先停掉： .\start.ps1 -Stop -Port $Port"
    exit 1
}
Write-Ok "端口 $Port 空闲"

# ---------------------------------------------------------------- 4. 数据库连通性
Write-Step "[4/6] 检查 MySQL $DbHost`:$DbPort ..."
$tcp = Test-NetConnection -ComputerName $DbHost -Port $DbPort -WarningAction SilentlyContinue
if ($tcp.TcpTestSucceeded) {
    Write-Ok "MySQL 端口可达"
} else {
    Write-Warn2 "MySQL $DbHost`:$DbPort 不可达 —— 应用仍会启动，但查询接口会返回 503（降级模式）"
}

if ($Check) { Write-Host ""; Write-Ok "自检完成（未启动）"; exit 0 }

# ---------------------------------------------------------------- 5. 启动
Write-Step "[5/6] 启动应用..."
# 注意：变量名不能用 $args —— 它是 PowerShell 的自动变量，赋值会报只读错误
$javaArgs = @(
    "-Dfile.encoding=UTF-8",
    "-jar", "`"$JarPath`"",
    "--server.port=$Port",
    "--spring.datasource.url=jdbc:mysql://$DbHost`:$DbPort/$DbName`?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true",
    "--spring.datasource.username=$DbUser",
    "--spring.datasource.password=$DbPassword",
    "--uev.cache.type=$CacheType"
)
$logFile = Join-Path $scriptDir "run_$Port.log"
Write-Step "日志：$logFile"
$proc = Start-Process -FilePath $javaExe -ArgumentList $javaArgs -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" -PassThru -NoNewWindow
Write-Ok "已启动，PID=$($proc.Id)"

# ---------------------------------------------------------------- 6. 等健康检查
Write-Step "[6/6] 等待 /api/health 就绪（最多 60 秒）..."
$deadline = (Get-Date).AddSeconds(60)
$ready = $false
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 1500
    if ($proc.HasExited) {
        Write-Err2 "进程已退出（退出码 $($proc.ExitCode)），请查看日志：$logFile"
        Get-Content $logFile -Tail 20 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        exit 1
    }
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 3
        if ($r.code -eq 200) {
            $ready = $true
            $comp = $r.data.components
            Write-Ok "健康检查通过：status=$($r.data.status)  mysql=$($comp.mysql)  redis=$($comp.redis)  regionCount=$($r.data.regionCount)"
            break
        }
    } catch { }
    Write-Host "    ...等待中" -ForegroundColor DarkGray
}

if (-not $ready) {
    Write-Err2 "60 秒内未通过健康检查，请查看日志：$logFile"
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " 启动成功" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host " 接口地址 : http://127.0.0.1:$Port/api"
Write-Host " 健康检查 : http://127.0.0.1:$Port/api/health"
Write-Host " 停止服务 : .\start.ps1 -Stop -Port $Port"
Write-Host " 进程 PID : $($proc.Id)"
Write-Host ""
Write-Host " 下一步自测（新开一个窗口）：" -ForegroundColor Cyan
Write-Host "   .\scripts\smoke_test.ps1 -Base http://127.0.0.1:$Port/api"
Write-Host ""
