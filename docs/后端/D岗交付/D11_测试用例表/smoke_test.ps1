<#!
  smoke_test.ps1 —— D 岗端到端体检脚本（Windows / PowerShell 7）

  用法：
      pwsh -File scripts/smoke_test.ps1
      pwsh -File scripts/smoke_test.ps1 -Base http://localhost:8080/api

  作用：16 个接口逐个打一遍，打印 HTTP 状态 + body 里的 code，
        最后给出"通过 N / 失败 M"，失败时退出码为 1（可挂进 CI 或组长冒烟脚本）。
#>
param(
    [string]$Base = "http://localhost:8080/api"
)

$pass = 0
$fail = 0

function Assert-Ok($name, $url, $method = "GET", $body = $null) {
    try {
        $req = @{ Uri = $url; UseBasicParsing = $true; SkipHttpErrorCheck = $true; TimeoutSec = 20 }
        if ($method -eq "POST") {
            $req.Method = "Post"
            $req.ContentType = "application/json"
            $req.Body = if ($body) { $body } else { "{}" }
        }
        $resp = Invoke-WebRequest @req
        $json = $resp.Content | ConvertFrom-Json
        if ($json.code -eq 200) {
            Write-Host ("  [PASS] " + $name.PadRight(34) + " code=200")
            $script:pass++
        } else {
            Write-Host ("  [FAIL] " + $name.PadRight(34) + " code=" + $json.code + " " + $json.message)
            $script:fail++
        }
    } catch {
        Write-Host ("  [FAIL] " + $name.PadRight(34) + " 异常：" + $_.Exception.Message)
        $script:fail++
    }
}

Write-Host "===== UrbanEV 后端冒烟测试 ====="
Write-Host ("目标：" + $Base)

Assert-Ok "01 健康检查"            "$Base/health"
Assert-Ok "02 登录"                "$Base/auth/login" "POST" '{"username":"admin","password":"uev123456"}'
Assert-Ok "04 KPI 概览"            "$Base/dashboard/kpi"
Assert-Ok "05 分区清单"            "$Base/zones"
Assert-Ok "06 分区占用率"          "$Base/zones/occupancy"
Assert-Ok "07 分区详情"            "$Base/zones/140"
Assert-Ok "08 24 小时曲线"         "$Base/charts/hourly"
Assert-Ok "09 失衡 TOP10"          "$Base/charts/imbalance?limit=10"
Assert-Ok "10 电价弹性"            "$Base/charts/price-elasticity"
Assert-Ok "11 需求预测"            "$Base/charts/forecast?zoneId=140"
Assert-Ok "12 布点建议"            "$Base/charts/suggestions?limit=10"
Assert-Ok "13 双口径偏差"          "$Base/charts/volume-deviation"
Assert-Ok "14 POI 关联"            "$Base/charts/poi-correlation"
Assert-Ok "15 数据字典"            "$Base/dictionary"
Assert-Ok "16 缓存统计"            "$Base/system/cache-stats"

Write-Host ""
Write-Host ("结果：通过 " + $pass + "　失败 " + $fail)
if ($fail -gt 0) { exit 1 }
