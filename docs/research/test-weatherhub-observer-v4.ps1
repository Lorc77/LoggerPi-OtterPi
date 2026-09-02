Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$decoderPath = Join-Path $PSScriptRoot 'decode-weatherhub-v2.ps1'

if (-not (Test-Path $decoderPath)) {
    throw "Decoder nicht gefunden: $decoderPath"
}

Write-Host "=== WeatherHub Observer Baseline Test v4 ==="
Write-Host ""

Write-Host "Lade Decoder:"
Write-Host "  $decoderPath"

. $decoderPath

if (-not (Get-Command Convert-WeatherHubBase64 -ErrorAction SilentlyContinue)) {
    throw "Convert-WeatherHubBase64 wurde nach dem Laden des Decoders nicht gefunden."
}

Write-Host "Decoder: OK"
Write-Host ""

# Credentials niemals im Skript speichern.
$credential = Get-Credential

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# ------------------------------------------------------------
# Login
# ------------------------------------------------------------

$body = @{
    Username = $credential.UserName
    Password = $credential.GetNetworkCredential().Password
    Lang     = 'en'
}

Write-Host "Login ..."

$login = Invoke-WebRequest `
    -UseBasicParsing `
    -Uri "https://www.wh-observer.de/Account/LogOn" `
    -Method POST `
    -WebSession $session `
    -ContentType "application/x-www-form-urlencoded" `
    -Body $body

Write-Host "Login HTTP: $($login.StatusCode)"
Write-Host "Login URL : $($login.BaseResponse.ResponseUri)"
Write-Host ""

# ------------------------------------------------------------
# Devices
# ------------------------------------------------------------

Write-Host "Lese /Devices ..."

$devices = Invoke-WebRequest `
    -UseBasicParsing `
    -Uri "https://www.wh-observer.de/Devices" `
    -Method GET `
    -WebSession $session

Write-Host "Devices HTTP: $($devices.StatusCode)"
Write-Host "Devices URL : $($devices.BaseResponse.ResponseUri)"

if ($devices.Content -match '<title>WeatherHub-Observer \| Sign in</title>') {
    throw "Session ist NICHT authentifiziert."
}

Write-Host "Authentication: OK"
Write-Host ""

# ------------------------------------------------------------
# Device Discovery
# ------------------------------------------------------------

Write-Host "=== Device Discovery ==="
Write-Host ""

$devicePattern = '<div\s+data-deviceid="([^"]+)"[^>]*>'

$deviceMatches = [regex]::Matches(
    $devices.Content,
    $devicePattern,
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)

$foundDevices = @()

foreach ($match in $deviceMatches) {
    $deviceId = $match.Groups[1].Value

    # Gesamten HTML-Block dieses Devices bis zum nächsten
    # data-deviceid erfassen.
    $start = $match.Index

    $next = $devices.Content.IndexOf(
        'data-deviceid="',
        $start + $match.Length,
        [System.StringComparison]::OrdinalIgnoreCase
    )

    if ($next -lt 0) {
        $block = $devices.Content.Substring($start)
    }
    else {
        $block = $devices.Content.Substring(
            $start,
            $next - $start
        )
    }

    # Anzeigename aus <h4>...</h4> lesen.
    $nameMatch = [regex]::Match(
        $block,
        '<h4[^>]*>\s*(.*?)\s*</h4>',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase `
        -bor [System.Text.RegularExpressions.RegexOptions]::Singleline
    )

    if ($nameMatch.Success) {
        $name = $nameMatch.Groups[1].Value
    }
    else {
        $name = ''
    }

    # HTML und Whitespace bereinigen.
    $name = [System.Net.WebUtility]::HtmlDecode($name)
    $name = [regex]::Replace($name, '<[^>]+>', '')
    $name = [regex]::Replace($name, '\s+', ' ').Trim()

    $foundDevices += [PSCustomObject]@{
        DeviceId = $deviceId
        Name     = $name
    }
}

if ($foundDevices.Count -eq 0) {
    throw "Keine Devices in /Devices gefunden."
}

Write-Host "Devices gefunden: $($foundDevices.Count)"
Write-Host ""

$foundDevices |
    Format-Table DeviceId, Name -AutoSize

Write-Host ""

# Für den Baseline-Test automatisch das erste gefundene
# Device verwenden.
$device = $foundDevices | Select-Object -First 1

$deviceId = $device.DeviceId

Write-Host "Verwende für Sparkline-Test:"
Write-Host "  Device ID: $($device.DeviceId)"
Write-Host "  Name      : $($device.Name)"
Write-Host ""

# ------------------------------------------------------------
# Sparkline
# ------------------------------------------------------------

Write-Host "Teste Sparkline:"
Write-Host "  Device ID: $deviceId"
Write-Host "  Name      : $($device.Name)"
Write-Host ""

$response = Invoke-WebRequest `
    -UseBasicParsing `
    -Uri "https://www.wh-observer.de/Devices/SparkLineChartData" `
    -Method POST `
    -WebSession $session `
    -ContentType "application/json; charset=utf-8" `
    -Body (@{
        deviceID = $deviceId
    } | ConvertTo-Json -Compress)

Write-Host "Sparkline HTTP: $($response.StatusCode)"
Write-Host "Response type : $($response.Content.GetType().FullName)"
Write-Host "Response bytes: $($response.Content.Length)"
Write-Host ""

# ------------------------------------------------------------
# Base64
# ------------------------------------------------------------

$b64 = [System.Text.Encoding]::UTF8.GetString($response.Content)

if ($b64 -notmatch '^[A-Za-z0-9+/]*={0,2}$') {
    throw "Sparkline-Response ist keine gültige Base64-Payload."
}

Write-Host "Base64: OK"
Write-Host "Length: $($b64.Length)"
Write-Host "Prefix: $($b64.Substring(0, [Math]::Min(80, $b64.Length)))"
Write-Host ""

# ------------------------------------------------------------
# Decode
# ------------------------------------------------------------

$chart = Convert-WeatherHubBase64 $b64

if ($null -eq $chart) {
    throw "Decoder lieferte NULL."
}

Write-Host "Decoder: OK"
Write-Host "Chart type  : $($chart.GetType().FullName)"
Write-Host "Series count: $($chart.Series.Count)"
Write-Host ""

# ------------------------------------------------------------
# Ausgabe
# ------------------------------------------------------------

foreach ($series in $chart.Series) {
    Write-Host "=== $($series.SeriesID) ==="
    Write-Host "Datasets : $($series.Datasets.Count)"
    Write-Host "Timestamp: $($series.FormattedTimestamp)"
    Write-Host "Measure  : $($series.FormattedMeasurement)"
    Write-Host ""

    $series.Datasets |
        Select-Object -First 5 |
        ForEach-Object {
            Write-Host "  Timestamp=$($_.Timestamp) Value=$($_.Value)"
        }

    Write-Host ""
}

Write-Host "=== TEST ERFOLGREICH ==="
