<#!
  smoke_test.ps1 —— D 岗端到端体检脚本（Windows）

  兼容 Windows 自带 PowerShell 5.1 与 PowerShell 7：
    powershell -ExecutionPolicy Bypass -File .\smoke_test.ps1
    pwsh -File .\smoke_test.ps1 -Base http://127.0.0.1:18099/api

  作用：15 个接口逐个打一遍，打印 HTTP 状态 + body 里的 code，
        最后给出"通过 N / 失败 M"，失败时退出码为 1。
  说明：不使用 -SkipHttpErrorCheck（PS5.1 没有该参数），
        非 2xx 时自行从异常里取响应体，保证两个版本结果一致。
#>
param(
    [string]$Base = "http://localhost:8080/api"
)

$pass = 0
$fail = 0

function Invoke-Api($url, $method = "GET", $body = $null) {
    $req = @{ Uri = $url; UseBasicParsing = $true; TimeoutSec = 20 }
    if ($method -eq "POST") {
        $req.Method = "Post"
        $req.ContentType = "application/json"
        $req.Body = if ($body) { $body } else { "{}" }
    }
    try {
        $r = Invoke-WebRequest @req
        return @{ Status = [int]$r.StatusCode; Content = [string]$r.Content }
    } catch {
        $ex = $_.Exception
        # PS7：错误详情在 ErrorDetails.Message
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            return @{ Status = 0; Content = [string]$_.ErrorDetails.Message }
        }
        # PS5.1：HttpWebResponse 提供状态码与响应流
        if ($ex.Response -and $ex.Response.GetResponseStream) {
            $sr = New-Object System.IO.StreamReader($ex.Response.GetResponseStream())
            $txt = $sr.ReadToEnd()
            $sr.Close()
            return @{ Status = [int]$ex.Response.StatusCode; Content = $txt }
        }
        throw
    }
}

function Assert-Ok($name, $url, $method = "GET", $body = $null) {
    try {
        $r = Invoke-Api $url $method $body
        $json = $null
        try { $json = $r.Content | ConvertFrom-Json } catch { }
        if ($json -and $json.code -eq 200) {
            Write-Host ("  [PASS] " + $name.PadRight(34) + " http=" + $r.Status + " code=200")
            $script:pass++
        } elseif ($json) {
            Write-Host ("  [FAIL] " + $name.PadRight(34) + " http=" + $r.Status + " code=" + $json.code + " " + $json.message)
            $script:fail++
        } else {
            Write-Host ("  [FAIL] " + $name.PadRight(34) + " http=" + $r.Status + " body 非 JSON：" + $r.Content.Substring(0, [Math]::Min(60, $r.Content.Length)))
            $script:fail++
        }
    } catch {
        Write-Host ("  [FAIL] " + $name.PadRight(34) + " 异常：" + $_.Exception.Message)
        $script:fail++
    }
}

Write-Host "===== UrbanEV 后端冒烟测试 ====="
Write-Host ("目标：" + $Base)
Write-Host ("PowerShell 版本：" + $PSVersionTable.PSVersion.ToString())

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
