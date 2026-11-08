# 河小智 · 浏览器就绪后自动打开
param(
    [string]$Url = "http://localhost:8501",
    [string]$HealthUrl = "http://127.0.0.1:8501/_stcore/health"
)

for ($i = 0; $i -lt 60; $i++) {
    try {
        $health = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 $HealthUrl).Content
        if ($health.Trim() -eq "ok") {
            Start-Process $Url
            exit 0
        }
    } catch { }
    Start-Sleep -Milliseconds 500
}

# 兜底：即使健康检查超时，也尝试打开一次，用户可手动刷新
Start-Process $Url
exit 0
