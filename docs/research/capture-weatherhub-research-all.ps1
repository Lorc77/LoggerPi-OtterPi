Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================
# WeatherHub Observer - Research Capture ALL Devices
#
# Zweck:
#   - Login bei WeatherHub Observer
#   - alle Devices aus /Devices ermitteln
#   - für JEDES Device SparklineChartData abrufen
#   - originale Base64-Payload unverändert speichern
#   - Payload direkt mit decode-weatherhub-v2.ps1 dekodieren
#   - Decoder-Ergebnis als JSON speichern
#   - zusätzlich eine kompakte lesbare Zusammenfassung erzeugen
#
# Ausgabe:
#
#   docs\research\weatherhub-dumps\
#       YYYYMMDD-HHMMSS\
#           index.json
#           001-<Sensor>\
#               metadata.json
#               payload.b64
#               decoded.json
#               summary.txt
#
# WICHTIG:
#   Die .b64-Datei ist der originale Datenstrom.
#   Sie wird NICHT verändert oder neu serialisiert.
#
# Credentials werden NICHT im Skript gespeichert.
# ============================================================


# ============================================================
# PATHS
# ============================================================

$decoderPath = Join-Path $PSScriptRoot 'decode-weatherhub-v2.ps1'

$dumpRoot = Join-Path `
    $PSScriptRoot `
    'weatherhub-dumps'

if (-not (Test-Path -LiteralPath $decoderPath)) {
    throw "Decoder nicht gefunden: $decoderPath"
}

if (-not (Test-Path -LiteralPath $dumpRoot)) {
    New-Item `
        -ItemType Directory `
        -Path $dumpRoot `
        -Force |
        Out-Null
}


# ============================================================
# RUN DIRECTORY
# ============================================================

$runTimestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

$runDirectory = Join-Path `
    $dumpRoot `
    $runTimestamp

New-Item `
    -ItemType Directory `
    -Path $runDirectory `
    -Force |
    Out-Null


# ============================================================
# HEADER
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " WeatherHub Observer - Research Capture ALL"
Write-Host "============================================================"
Write-Host ""

Write-Host "Run:"
Write-Host "  $runTimestamp"
Write-Host ""

Write-Host "Dump directory:"
Write-Host "  $runDirectory"
Write-Host ""

Write-Host "Decoder:"
Write-Host "  $decoderPath"
Write-Host ""


# ============================================================
# LOAD DECODER
# ============================================================

Write-Host "Lade Decoder ..."

. $decoderPath

if (-not (Get-Command Convert-WeatherHubBase64 -ErrorAction SilentlyContinue)) {
    throw "Convert-WeatherHubBase64 wurde nach dem Laden des Decoders nicht gefunden."
}

Write-Host "Decoder: OK"
Write-Host ""


# ============================================================
# CREDENTIALS
# ============================================================

# Credentials niemals im Skript speichern.
$credential = Get-Credential


# ============================================================
# SESSION
# ============================================================

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession


# ============================================================
# LOGIN
# ============================================================

$loginBody = @{
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
    -Body $loginBody

Write-Host "Login HTTP: $($login.StatusCode)"
Write-Host "Login URL : $($login.BaseResponse.ResponseUri)"
Write-Host ""


# ============================================================
# DEVICES
# ============================================================

Write-Host "Lese /Devices ..."

$devicesResponse = Invoke-WebRequest `
    -UseBasicParsing `
    -Uri "https://www.wh-observer.de/Devices" `
    -Method GET `
    -WebSession $session

Write-Host "Devices HTTP: $($devicesResponse.StatusCode)"
Write-Host "Devices URL : $($devicesResponse.BaseResponse.ResponseUri)"

if ($devicesResponse.Content -match '<title>WeatherHub-Observer \| Sign in</title>') {
    throw "Session ist NICHT authentifiziert."
}

Write-Host "Authentication: OK"
Write-Host ""


# ============================================================
# DEVICE DISCOVERY
# ============================================================

Write-Host "============================================================"
Write-Host " Device Discovery"
Write-Host "============================================================"
Write-Host ""

$devicePattern = '<div\s+data-deviceid="([^"]+)"[^>]*>'

$deviceMatches = [regex]::Matches(
    $devicesResponse.Content,
    $devicePattern,
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
)

$foundDevices = @()

foreach ($match in $deviceMatches) {

    $deviceId = $match.Groups[1].Value

    # Gesamten HTML-Block dieses Devices bis zum nächsten
    # data-deviceid erfassen.
    $start = $match.Index

    $next = $devicesResponse.Content.IndexOf(
        'data-deviceid="',
        $start + $match.Length,
        [System.StringComparison]::OrdinalIgnoreCase
    )

    if ($next -lt 0) {
        $block = $devicesResponse.Content.Substring($start)
    }
    else {
        $block = $devicesResponse.Content.Substring(
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


# ============================================================
# DISCOVERY VALIDATION
# ============================================================

if ($foundDevices.Count -eq 0) {
    throw "Keine Devices in /Devices gefunden."
}

Write-Host "Devices gefunden: $($foundDevices.Count)"
Write-Host ""

if ($foundDevices.Count -ne 19) {

    Write-Warning `
        "Es wurden $($foundDevices.Count) Devices gefunden, erwartet wurden 19."

    Write-Warning `
        "Der Capture wird trotzdem für ALLE gefundenen Devices durchgeführt."
}

$foundDevices |
    Format-Table DeviceId, Name -AutoSize

Write-Host ""


# ============================================================
# RUN INDEX
# ============================================================

$runIndex = [ordered]@{
    CaptureType       = 'WeatherHub Observer Sparkline Research Capture'
    RunTimestamp      = $runTimestamp
    RunStarted        = (Get-Date).ToString('o')
    Decoder           = Split-Path $decoderPath -Leaf
    ExpectedDevices   = 19
    FoundDevices      = $foundDevices.Count
    DeviceResults     = @()
}

$deviceCounter = 0


# ============================================================
# CAPTURE EACH DEVICE
# ============================================================

foreach ($device in $foundDevices) {

    $deviceCounter++

    $deviceId = $device.DeviceId
    $deviceName = $device.Name

    Write-Host ""
    Write-Host "============================================================"
    Write-Host " Device $deviceCounter / $($foundDevices.Count)"
    Write-Host "============================================================"
    Write-Host "Device ID : $deviceId"
    Write-Host "Name      : $deviceName"
    Write-Host ""


    # --------------------------------------------------------
    # Safe directory name
    # --------------------------------------------------------

    $safeName = $deviceName

    if ([string]::IsNullOrWhiteSpace($safeName)) {
        $safeName = "Unnamed"
    }

    $safeName = [regex]::Replace(
        $safeName,
        '[\\/:*?"<>|]',
        '_'
    )

    $safeName = [regex]::Replace(
        $safeName,
        '\s+',
        '_'
    )

    $safeName = $safeName.Trim('_')

    if ($safeName.Length -gt 80) {
        $safeName = $safeName.Substring(0, 80)
    }

    $deviceDirectoryName = '{0:D3}-{1}' -f `
        $deviceCounter, `
        $safeName

    $deviceDirectory = Join-Path `
        $runDirectory `
        $deviceDirectoryName

    New-Item `
        -ItemType Directory `
        -Path $deviceDirectory `
        -Force |
        Out-Null


    # --------------------------------------------------------
    # Metadata before request
    # --------------------------------------------------------

    $captureStarted = Get-Date

    $metadata = [ordered]@{
        CaptureRun       = $runTimestamp
        DeviceNumber     = $deviceCounter
        DeviceId         = $deviceId
        Name             = $deviceName
        CaptureStarted   = $captureStarted.ToString('o')
        Endpoint         = 'https://www.wh-observer.de/Devices/SparkLineChartData'
        Method           = 'POST'
        RequestBody      = @{
            deviceID = $deviceId
        }
        Decoder          = Split-Path $decoderPath -Leaf
    }


    # --------------------------------------------------------
    # Sparkline request
    # --------------------------------------------------------

    try {

        Write-Host "Sparkline Request ..."

        $requestBody = @{
            deviceID = $deviceId
        } |
            ConvertTo-Json -Compress

        $response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri "https://www.wh-observer.de/Devices/SparkLineChartData" `
            -Method POST `
            -WebSession $session `
            -ContentType "application/json; charset=utf-8" `
            -Body $requestBody

        Write-Host "HTTP Status : $($response.StatusCode)"
        Write-Host "Content Type: $($response.Headers['Content-Type'])"
        Write-Host ""


        # ----------------------------------------------------
        # Extract Base64
        # ----------------------------------------------------

        $b64 = [System.Text.Encoding]::UTF8.GetString(
            $response.Content
        ).Trim()

        if ([string]::IsNullOrWhiteSpace($b64)) {
            throw "Sparkline-Response ist leer."
        }

        if ($b64 -notmatch '^[A-Za-z0-9+/]*={0,2}$') {
            throw "Sparkline-Response ist keine gültige Base64-Payload."
        }

        Write-Host "Base64       : OK"
        Write-Host "Base64 Length: $($b64.Length)"
        Write-Host "Base64 Prefix: $($b64.Substring(0, [Math]::Min(80, $b64.Length)))"
        Write-Host ""


        # ----------------------------------------------------
        # Save ORIGINAL Base64
        #
        # Wichtig:
        # Keine Umwandlung in Bytes und zurück.
        # Genau dieser String wird archiviert.
        # ----------------------------------------------------

        $payloadPath = Join-Path `
            $deviceDirectory `
            'payload.b64'

        [System.IO.File]::WriteAllText(
            $payloadPath,
            $b64,
            [System.Text.UTF8Encoding]::new($false)
        )

        Write-Host "Payload gespeichert:"
        Write-Host "  $payloadPath"
        Write-Host ""


        # ----------------------------------------------------
        # Decode
        # ----------------------------------------------------

        Write-Host "Decoder ..."

        $chart = Convert-WeatherHubBase64 $b64

        if ($null -eq $chart) {
            throw "Decoder lieferte NULL."
        }

        Write-Host "Decoder     : OK"
        Write-Host "Chart Type  : $($chart.GetType().FullName)"

        if ($null -eq $chart.Series) {
            Write-Host "Series Count: 0"
        }
        else {
            Write-Host "Series Count: $($chart.Series.Count)"
        }

        Write-Host ""


        # ----------------------------------------------------
        # Save decoded JSON
        # ----------------------------------------------------

        $decodedPath = Join-Path `
            $deviceDirectory `
            'decoded.json'

        $json = $chart |
            ConvertTo-Json `
                -Depth 20 `
                -Compress:$false

        [System.IO.File]::WriteAllText(
            $decodedPath,
            $json,
            [System.Text.UTF8Encoding]::new($false)
        )

        Write-Host "Decoded JSON gespeichert:"
        Write-Host "  $decodedPath"
        Write-Host ""


        # ----------------------------------------------------
        # Human-readable summary
        # ----------------------------------------------------

        $summaryPath = Join-Path `
            $deviceDirectory `
            'summary.txt'

        $summaryLines = New-Object System.Collections.Generic.List[string]

        $summaryLines.Add(
            "WeatherHub Observer Research Capture"
        )

        $summaryLines.Add(
            "===================================="
        )

        $summaryLines.Add(
            ""
        )

        $summaryLines.Add(
            "Run       : $runTimestamp"
        )

        $summaryLines.Add(
            "Device #  : $deviceCounter"
        )

        $summaryLines.Add(
            "Device ID : $deviceId"
        )

        $summaryLines.Add(
            "Name      : $deviceName"
        )

        $summaryLines.Add(
            "Captured  : $($captureStarted.ToString('o'))"
        )

        $summaryLines.Add(
            "HTTP      : $($response.StatusCode)"
        )

        $summaryLines.Add(
            "Base64    : $($b64.Length) chars"
        )

        $summaryLines.Add(
            ""
        )

        $summaryLines.Add(
            "Decoded"
        )

        $summaryLines.Add(
            "-------"
        )

        if ($null -eq $chart.Series) {

            $summaryLines.Add(
                "Series count: 0"
            )

        }
        else {

            $summaryLines.Add(
                "Series count: $($chart.Series.Count)"
            )

            $seriesIndex = 0

            foreach ($series in $chart.Series) {

                $seriesIndex++

                $summaryLines.Add(
                    ""
                )

                $summaryLines.Add(
                    "Series $seriesIndex"
                )

                $summaryLines.Add(
                    "=========="
                )

                $summaryLines.Add(
                    "SeriesID              : $($series.SeriesID)"
                )

                $summaryLines.Add(
                    "Datasets              : $($series.Datasets.Count)"
                )

                $summaryLines.Add(
                    "LineColor             : $($series.LineColor)"
                )

                $summaryLines.Add(
                    "FormattedTimestamp    : $($series.FormattedTimestamp)"
                )

                $summaryLines.Add(
                    "FormattedMeasurement  : $($series.FormattedMeasurement)"
                )

                $summaryLines.Add(
                    "ConnectionLost        : $($series.ConnectionLost)"
                )

                $summaryLines.Add(
                    "LowBattery            : $($series.LowBattery)"
                )

                $summaryLines.Add(
                    "AlertWasActive        : $($series.AlertWasActive)"
                )

                $summaryLines.Add(
                    "CardStatus            : $($series.CardStatus)"
                )

                $summaryLines.Add(
                    "AlertActive           : $($series.AlertActive)"
                )

                $summaryLines.Add(
                    "AlertSettingActive    : $($series.AlertSettingActive)"
                )

                if ($null -ne $series.Datasets) {

                    $datasetIndex = 0

                    foreach ($dataset in $series.Datasets) {

                        $datasetIndex++

                        $timestampText = ''

                        if ($dataset.PSObject.Properties.Name -contains 'Timestamp') {
                            try {
                                $timestampText = (
                                    Convert-WeatherHubTimestamp `
                                        $dataset.Timestamp
                                ).ToString('o')
                            }
                            catch {
                                $timestampText = 'Timestamp conversion failed'
                            }
                        }

                        $summaryLines.Add(
                            "  Dataset $datasetIndex : Timestamp=$($dataset.Timestamp) UTC=$timestampText Value=$($dataset.Value)"
                        )

                        if ($dataset.PSObject.Properties.Name -contains 'Tooltip') {
                            $summaryLines.Add(
                                "               Tooltip=$($dataset.Tooltip)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'AlertIsActive') {
                            $summaryLines.Add(
                                "               AlertIsActive=$($dataset.AlertIsActive)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'HiAlert') {
                            $summaryLines.Add(
                                "               HiAlert=$($dataset.HiAlert)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'HiStartEvent') {
                            $summaryLines.Add(
                                "               HiStartEvent=$($dataset.HiStartEvent)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'HiEndEvent') {
                            $summaryLines.Add(
                                "               HiEndEvent=$($dataset.HiEndEvent)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'HiSetting') {
                            $summaryLines.Add(
                                "               HiSetting=$($dataset.HiSetting)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'LoAlert') {
                            $summaryLines.Add(
                                "               LoAlert=$($dataset.LoAlert)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'LoStartEvent') {
                            $summaryLines.Add(
                                "               LoStartEvent=$($dataset.LoStartEvent)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'LoEndEvent') {
                            $summaryLines.Add(
                                "               LoEndEvent=$($dataset.LoEndEvent)"
                            )
                        }

                        if ($dataset.PSObject.Properties.Name -contains 'LoSetting') {
                            $summaryLines.Add(
                                "               LoSetting=$($dataset.LoSetting)"
                            )
                        }
                    }
                }
            }
        }


        [System.IO.File]::WriteAllLines(
            $summaryPath,
            $summaryLines,
            [System.Text.UTF8Encoding]::new($false)
        )

        Write-Host "Summary gespeichert:"
        Write-Host "  $summaryPath"
        Write-Host ""


        # ----------------------------------------------------
        # Metadata completion
        # ----------------------------------------------------

        $captureFinished = Get-Date

        $metadata.Status = 'OK'
        $metadata.CaptureFinished = $captureFinished.ToString('o')
        $metadata.DurationMilliseconds = (
            $captureFinished - $captureStarted
        ).TotalMilliseconds
        $metadata.HttpStatus = [int]$response.StatusCode
        $metadata.Base64Length = $b64.Length
        $metadata.DecoderStatus = 'OK'

        if ($null -eq $chart.Series) {
            $metadata.SeriesCount = 0
        }
        else {
            $metadata.SeriesCount = $chart.Series.Count
        }

        $metadataPath = Join-Path `
            $deviceDirectory `
            'metadata.json'

        $metadata |
            ConvertTo-Json -Depth 20 |
            Set-Content `
                -LiteralPath $metadataPath `
                -Encoding UTF8


        # ----------------------------------------------------
        # Result for index
        # ----------------------------------------------------

        $runIndex.DeviceResults += [PSCustomObject][ordered]@{
            DeviceNumber  = $deviceCounter
            DeviceId      = $deviceId
            Name          = $deviceName
            Directory     = $deviceDirectoryName
            Status        = 'OK'
            HttpStatus    = [int]$response.StatusCode
            Base64Length  = $b64.Length
            SeriesCount   = if ($null -eq $chart.Series) {
                                0
                            }
                            else {
                                $chart.Series.Count
                            }
            CaptureStarted  = $captureStarted.ToString('o')
            CaptureFinished = $captureFinished.ToString('o')
        }


        Write-Host "STATUS: OK"
    }
    catch {

        # ----------------------------------------------------
        # Error handling
        # ----------------------------------------------------

        $captureFinished = Get-Date

        Write-Host ""
        Write-Host "STATUS: FEHLER"
        Write-Host "  $($_.Exception.Message)"
        Write-Host ""

        $metadata.Status = 'ERROR'
        $metadata.CaptureFinished = $captureFinished.ToString('o')
        $metadata.DurationMilliseconds = (
            $captureFinished - $captureStarted
        ).TotalMilliseconds
        $metadata.Error = $_.Exception.Message

        $metadataPath = Join-Path `
            $deviceDirectory `
            'metadata.json'

        $metadata |
            ConvertTo-Json -Depth 20 |
            Set-Content `
                -LiteralPath $metadataPath `
                -Encoding UTF8


        $runIndex.DeviceResults += [PSCustomObject][ordered]@{
            DeviceNumber    = $deviceCounter
            DeviceId        = $deviceId
            Name            = $deviceName
            Directory       = $deviceDirectoryName
            Status          = 'ERROR'
            Error           = $_.Exception.Message
            CaptureStarted  = $captureStarted.ToString('o')
            CaptureFinished = $captureFinished.ToString('o')
        }

        # Nicht den kompletten Lauf abbrechen.
        # Der nächste Sensor soll trotzdem erfasst werden.
        continue
    }
}


# ============================================================
# FINISH RUN INDEX
# ============================================================

$runFinished = Get-Date

$okCount = @(
    $runIndex.DeviceResults |
        Where-Object { $_.Status -eq 'OK' }
).Count

$errorCount = @(
    $runIndex.DeviceResults |
        Where-Object { $_.Status -eq 'ERROR' }
).Count

$runIndex.RunFinished = $runFinished.ToString('o')
$runIndex.DurationMilliseconds = (
    $runFinished - [DateTime]::Parse($runIndex.RunStarted)
).TotalMilliseconds
$runIndex.SuccessfulDevices = $okCount
$runIndex.FailedDevices = $errorCount


# ============================================================
# SAVE INDEX
# ============================================================

$indexPath = Join-Path `
    $runDirectory `
    'index.json'

$runIndex |
    ConvertTo-Json -Depth 20 |
    Set-Content `
        -LiteralPath $indexPath `
        -Encoding UTF8


# ============================================================
# FINAL OUTPUT
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host " CAPTURE ABGESCHLOSSEN"
Write-Host "============================================================"
Write-Host ""

Write-Host "Run directory:"
Write-Host "  $runDirectory"
Write-Host ""

Write-Host "Devices gefunden : $($foundDevices.Count)"
Write-Host "Erfolgreich       : $okCount"
Write-Host "Fehler            : $errorCount"
Write-Host ""

Write-Host "Index:"
Write-Host "  $indexPath"
Write-Host ""

if ($errorCount -gt 0) {

    Write-Warning `
        "$errorCount Device(s) konnten nicht vollständig erfasst werden."

    Write-Host ""

    $runIndex.DeviceResults |
        Where-Object { $_.Status -eq 'ERROR' } |
        Format-Table DeviceNumber, DeviceId, Name, Error -AutoSize

    Write-Host ""
}

Write-Host "=== RESEARCH CAPTURE FERTIG ==="
Write-Host ""
