# 河小智 · 本地启动脚本（Windows PowerShell）
# 用法：双击 start.bat，或在终端执行 .\start.ps1
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$Root = $PSScriptRoot
Set-Location -LiteralPath $Root
$Port = 8501
$Url = "http://localhost:$Port"
$HealthUrl = "http://127.0.0.1:$Port/_stcore/health"

Write-Host ""
Write-Host "  ============================================" -ForegroundColor DarkCyan
Write-Host "   河小智 · 河南大学 AI 智慧校园服务平台" -ForegroundColor Cyan
Write-Host "   HENAN UNIVERSITY  ·  AI CAMPUS" -ForegroundColor DarkGray
Write-Host "  ============================================" -ForegroundColor DarkCyan
Write-Host ""

# 1) 检测 Python
#    .deps 内的二进制扩展（numpy / pyarrow / pandas 等）均为 cp312 编译，
#    必须用 Python 3.12 运行；优先锁定 3.12，避免误用 PATH 里排在前面的其他版本。
$PythonExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        $py312 = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
        if (($LASTEXITCODE -eq 0) -and $py312 -and (Test-Path -LiteralPath $py312.Trim())) {
            $PythonExe = $py312.Trim()
        }
    } catch { }
}
if (-not $PythonExe) {
    if (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = "python" }
    elseif (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = "py" }
}
if (-not $PythonExe) {
    Write-Host "  [!!] 未找到 Python。请先安装 Python 3.10+，并勾选 Add to PATH。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "  [OK] Python: $(& $PythonExe --version 2>&1)" -ForegroundColor DarkGray

# 2) 优先使用项目内置依赖（离线可复现）
$Deps = Join-Path $Root ".deps"
if (Test-Path -LiteralPath (Join-Path $Deps "streamlit")) {
    $env:PYTHONPATH = $Deps
    Write-Host "  [OK] 已加载项目内置依赖 .deps" -ForegroundColor Green
} else {
    $hasStreamlit = $false
    try {
        & $PythonExe -c "import streamlit" 2>$null
        $hasStreamlit = ($LASTEXITCODE -eq 0)
    } catch { $hasStreamlit = $false }

    if (-not $hasStreamlit) {
        Write-Host "  [..] 未检测到 Streamlit，首次运行正在安装依赖（约 1-3 分钟）" -ForegroundColor Yellow
        & $PythonExe -m pip install --disable-pip-version-check --target "$Deps" -r "$Root\requirements.txt"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [!!] 依赖安装失败。请确认 Python 3.10+ 可用并联网后重试。" -ForegroundColor Red
            Read-Host "按回车退出"
            exit 1
        }
        $env:PYTHONPATH = $Deps
        Write-Host "  [OK] 依赖安装完成" -ForegroundColor Green
    }
}

# 3) 如果河小智已经在 8501 运行，直接打开浏览器，不重复启动
$alreadyRunning = $false
try {
    $health = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $HealthUrl).Content
    $alreadyRunning = ($health.Trim() -eq "ok")
} catch { $alreadyRunning = $false }

if ($alreadyRunning) {
    Write-Host "  [OK] 检测到河小智已在 $Url 运行，直接打开浏览器" -ForegroundColor Green
    Start-Process $Url
    Start-Sleep -Seconds 1
    exit 0
}

$occupied = $null
try {
    $occupied = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
} catch { $occupied = $null }
# 部分精简版 Windows 没有 Get-NetTCPConnection，用 netstat 兜底
if (-not $occupied) {
    $occupied = [bool](netstat -ano | Select-String "127.0.0.1:$Port\s+0.0.0.0:0\s+LISTENING")
}
if ($occupied) {
    Write-Host "  [!!] 端口 $Port 已被其他程序占用。" -ForegroundColor Red
    Write-Host "       请关闭占用 8501 的程序后重新运行 start.bat，或修改 start.ps1 中的端口设置。" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

# 4) 启动浏览器：后台轮询健康检查，服务就绪后精确打开一次
try {
    Start-Process powershell -WindowStyle Hidden -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", "$Root\open_browser.ps1",
        "-Url", $Url,
        "-HealthUrl", $HealthUrl
    ) | Out-Null
} catch {
    # 即使浏览器自动打开失败，也不影响服务启动
}

Write-Host "  [>>] 服务启动中：$Url" -ForegroundColor Cyan
Write-Host "  [i]  浏览器会在服务就绪后自动打开；关闭本窗口即可停止服务" -ForegroundColor DarkGray
Write-Host ""

# 5) 启动 Streamlit（固定 8501，符合项目运行约定）
$StreamlitArgs = @(
    "-m", "streamlit", "run", "$Root\app.py",
    "--server.address", "127.0.0.1",
    "--server.port", "$Port",
    "--server.headless", "true",
    "--global.developmentMode", "false",
    "--browser.gatherUsageStats", "false"
)
& $PythonExe @StreamlitArgs
