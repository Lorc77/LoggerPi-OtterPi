Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================================================
# WeatherHub Sparkline Research Dumper
#
# Holt eine frische Sparkline-Payload und analysiert sie roh.
# Bestehende Decoder-Datei wird NICHT verändert.
# ============================================================

$deviceId = '0E74A4597B54'

$outDir = Join-Path $PSScriptRoot 'weatherhub-dumps'

if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

$base64File = Join-Path $outDir "sparkline-$deviceId-$timestamp.b64"
$binaryFile = Join-Path $outDir "sparkline-$deviceId-$timestamp.bin"
$dumpFile   = Join-Path $outDir "sparkline-$deviceId-$timestamp.txt"

Write-Host "=== WeatherHub Sparkline Research Dumper ==="
Write-Host ""
Write-Host "Device: $deviceId"
Write-Host ""

# ------------------------------------------------------------
# Credentials
# ------------------------------------------------------------

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
Write-Host ""

# ------------------------------------------------------------
# Devices / Session check
# ------------------------------------------------------------

Write-Host "Prüfe Session ..."

$devices = Invoke-WebRequest `
    -UseBasicParsing `
    -Uri "https://www.wh-observer.de/Devices" `
    -Method GET `
    -WebSession $session

if ($devices.Content -match '<title>WeatherHub-Observer \| Sign in</title>') {
    throw "Session ist NICHT authentifiziert."
}

Write-Host "Authentication: OK"
Write-Host ""

# ------------------------------------------------------------
# Sparkline
# ------------------------------------------------------------

Write-Host "Hole Sparkline ..."
Write-Host "  Device ID: $deviceId"
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

Write-Host "HTTP: $($response.StatusCode)"
Write-Host "Response type: $($response.Content.GetType().FullName)"
Write-Host "Response bytes: $($response.Content.Length)"
Write-Host ""

# ------------------------------------------------------------
# Base64 sichern
# ------------------------------------------------------------

$b64 = [System.Text.Encoding]::UTF8.GetString($response.Content).Trim()

if ($b64 -notmatch '^[A-Za-z0-9+/]*={0,2}$') {
    throw "Response ist keine gültige Base64-Payload."
}

$b64 | Set-Content -Path $base64File -NoNewline -Encoding ascii

Write-Host "Base64 gespeichert:"
Write-Host "  $base64File"
Write-Host "  Length: $($b64.Length)"
Write-Host ""

# ------------------------------------------------------------
# Binary sichern
# ------------------------------------------------------------

$bytes = [Convert]::FromBase64String($b64)

[System.IO.File]::WriteAllBytes(
    $binaryFile,
    $bytes
)

Write-Host "Binary gespeichert:"
Write-Host "  $binaryFile"
Write-Host "  Length: $($bytes.Length)"
Write-Host ""

# ============================================================
# Hilfsfunktionen
# ============================================================

function Read-Varint {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    [UInt64]$result = 0
    $shift = 0
    $start = $Position.Value

    while ($Position.Value -lt $End) {

        $b = [int]$Data[$Position.Value]
        $Position.Value++

        $result = $result -bor (
            ([UInt64]($b -band 0x7F)) -shl $shift
        )

        if (($b -band 0x80) -eq 0) {
            return [PSCustomObject]@{
                Value = $result
                Start = $start
                End   = $Position.Value
            }
        }

        $shift += 7

        if ($shift -ge 64) {
            throw "Invalid varint"
        }
    }

    throw "Unexpected end while reading varint"
}


function Get-Hex {
    param(
        [byte[]]$Bytes
    )

    if ($Bytes.Length -eq 0) {
        return ''
    }

    return (($Bytes | ForEach-Object {
        $_.ToString('X2')
    }) -join ' ')
}


function Get-Ascii {
    param(
        [byte[]]$Bytes
    )

    $chars = foreach ($b in $Bytes) {

        if ($b -ge 32 -and $b -le 126) {
            [char]$b
        }
        else {
            '.'
        }
    }

    return -join $chars
}


function Get-UTF8 {
    param(
        [byte[]]$Bytes
    )

    try {
        $text = [Text.Encoding]::UTF8.GetString($Bytes)

        if ($text -match '[\x00-\x08\x0B\x0C\x0E-\x1F]') {
            return ''
        }

        return $text
    }
    catch {
        return ''
    }
}


# ============================================================
# Recursive protobuf-ish dump
# ============================================================

function Dump-Message {
    param(
        [byte[]]$Data,
        [int]$Start,
        [int]$Length,
        [string]$Path,
        [int]$Depth
    )

    $lines = New-Object System.Collections.Generic.List[string]

    $pos = $Start
    $end = $Start + $Length

    $indent = '  ' * $Depth

    $lines.Add(
        "${indent}MESSAGE $Path  offset=$Start length=$Length"
    )

    while ($pos -lt $end) {

        $fieldStart = $pos

        $tagInfo = Read-Varint `
            $Data `
            ([ref]$pos) `
            $end

        $tag = $tagInfo.Value

        $fieldNumber = [int]($tag -shr 3)
        $wireType = [int]($tag -band 7)

        $fieldIndent = '  ' * ($Depth + 1)

        $lines.Add(
            "${fieldIndent}FIELD $fieldNumber  wire=$wireType  tagOffset=$fieldStart"
        )

        switch ($wireType) {

            # ------------------------------------------------
            # VARINT
            # ------------------------------------------------

            0 {

                $valueInfo = Read-Varint `
                    $Data `
                    ([ref]$pos) `
                    $end

                $rawStart = $valueInfo.Start
                $rawLength = $valueInfo.End - $rawStart

                $raw = New-Object byte[] $rawLength

                [Array]::Copy(
                    $Data,
                    $rawStart,
                    $raw,
                    0,
                    $rawLength
                )

                $lines.Add(
                    "${fieldIndent}  VARINT = $($valueInfo.Value)"
                )

                $lines.Add(
                    "${fieldIndent}  RAW    = $(Get-Hex $raw)"
                )
            }

            # ------------------------------------------------
            # FIXED64
            # ------------------------------------------------

            1 {

                if (($pos + 8) -gt $end) {
                    throw "Invalid fixed64 at offset $pos"
                }

                $raw = New-Object byte[] 8

                [Array]::Copy(
                    $Data,
                    $pos,
                    $raw,
                    0,
                    8
                )

                $value = [BitConverter]::ToDouble(
                    $raw,
                    0
                )

                $lines.Add(
                    "${fieldIndent}  FIXED64 DOUBLE = $value"
                )

                $lines.Add(
                    "${fieldIndent}  RAW            = $(Get-Hex $raw)"
                )

                $pos += 8
            }

            # ------------------------------------------------
            # LENGTH DELIMITED
            # ------------------------------------------------

            2 {

                $lengthInfo = Read-Varint `
                    $Data `
                    ([ref]$pos) `
                    $end

                $payloadLength = [int]$lengthInfo.Value
                $payloadStart = $pos

                if (($pos + $payloadLength) -gt $end) {
                    throw "Length-delimited field exceeds message"
                }

                $raw = New-Object byte[] $payloadLength

                [Array]::Copy(
                    $Data,
                    $pos,
                    $raw,
                    0,
                    $payloadLength
                )

                $lines.Add(
                    "${fieldIndent}  LENGTH = $payloadLength"
                )

                $lines.Add(
                    "${fieldIndent}  HEX    = $(Get-Hex $raw)"
                )

                $ascii = Get-Ascii $raw
                $utf8  = Get-UTF8 $raw

                if ($ascii.Length -gt 0) {
                    $lines.Add(
                        "${fieldIndent}  ASCII  = $ascii"
                    )
                }

                if ($utf8.Length -gt 0 -and $utf8 -ne $ascii) {
                    $lines.Add(
                        "${fieldIndent}  UTF8   = $utf8"
                    )
                }

                # ------------------------------------------------
                # Heuristik:
                #
                # Wenn das Feld wie ein Nested Message aussieht,
                # versuchen wir zusätzlich eine Rekursion.
                # Fehler dabei werden NICHT als Fehler gewertet.
                # ------------------------------------------------

                if ($payloadLength -gt 0) {

                    try {

                        $nestedLines = Dump-Message `
                            $raw `
                            0 `
                            $raw.Length `
                            "$Path.field$fieldNumber" `
                            ($Depth + 1)

                        if ($nestedLines.Count -gt 1) {

                            $lines.Add(
                                "${fieldIndent}  --- NESTED MESSAGE ---"
                            )

                            foreach ($nestedLine in $nestedLines) {
                                $lines.Add($nestedLine)
                            }

                            $lines.Add(
                                "${fieldIndent}  --- END NESTED ---"
                            )
                        }
                    }
                    catch {
                        # Kein gültiges Nested-Message-Format.
                    }
                }

                $pos += $payloadLength
            }

            # ------------------------------------------------
            # FIXED32
            # ------------------------------------------------

            5 {

                if (($pos + 4) -gt $end) {
                    throw "Invalid fixed32 at offset $pos"
                }

                $raw = New-Object byte[] 4

                [Array]::Copy(
                    $Data,
                    $pos,
                    $raw,
                    0,
                    4
                )

                $uint32 = [BitConverter]::ToUInt32(
                    $raw,
                    0
                )

                $float = [BitConverter]::ToSingle(
                    $raw,
                    0
                )

                $lines.Add(
                    "${fieldIndent}  FIXED32 UINT32 = $uint32"
                )

                $lines.Add(
                    "${fieldIndent}  FIXED32 FLOAT  = $float"
                )

                $lines.Add(
                    "${fieldIndent}  RAW             = $(Get-Hex $raw)"
                )

                $pos += 4
            }

            default {

                throw "Unsupported wire type $wireType at offset $fieldStart"
            }
        }
    }

    return $lines
}


# ============================================================
# Dump
# ============================================================

Write-Host "Analysiere Payload ..."
Write-Host ""

$dump = Dump-Message `
    $bytes `
    0 `
    $bytes.Length `
    'ChartData' `
    0

$dump | Set-Content `
    -Path $dumpFile `
    -Encoding utf8

Write-Host "Dump gespeichert:"
Write-Host "  $dumpFile"
Write-Host ""

Write-Host "=== ERSTE 250 ZEILEN ==="
$dump | Select-Object -First 250

Write-Host ""
Write-Host "=== FERTIG ==="
