# ============================================================
# WeatherHub Observer - ChartData Proto2 Decoder v2
#
# Research decoder / reusable decoder functions
#
# Unlike the legacy decoder, this file does NOT decode a file
# automatically when it is loaded.
#
# Intended usage:
#
#   . .\decode-weatherhub-v2.ps1
#
#   $chart = Convert-WeatherHubBase64 $base64
#
# The decoder can therefore be used by:
#
#   test-weatherhub-19.ps1
#
# without coupling HTTP access and decoding.
# ============================================================


# ============================================================
# VARINT
# ============================================================

function Read-WeatherHubVarint {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    [UInt64]$result = 0
    $shift = 0

    while ($Position.Value -lt $End) {

        $b = [int]$Data[$Position.Value]

        $Position.Value = $Position.Value + 1

        $part = ([UInt64]($b -band 0x7F)) -shl $shift

        $result = $result -bor $part

        if (($b -band 0x80) -eq 0) {
            return $result
        }

        $shift += 7

        if ($shift -ge 64) {
            throw "Invalid varint"
        }
    }

    throw "Unexpected end of buffer while reading varint"
}


# ============================================================
# FIXED64 / DOUBLE
# ============================================================

function Read-WeatherHubDouble {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    if (($Position.Value + 8) -gt $End) {
        throw "Unexpected end while reading double"
    }

    $value = [BitConverter]::ToDouble(
        $Data,
        $Position.Value
    )

    $Position.Value = $Position.Value + 8

    return $value
}


# ============================================================
# LENGTH-DELIMITED BYTES
# ============================================================

function Read-WeatherHubBytes {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    $length = Read-WeatherHubVarint $Data $Position $End

    if ($length -gt [int]::MaxValue) {
        throw "Length too large: $length"
    }

    $length = [int]$length

    if (($Position.Value + $length) -gt $End) {
        throw "Length-delimited field exceeds buffer"
    }

    $result = New-Object byte[] $length

    [Array]::Copy(
        $Data,
        $Position.Value,
        $result,
        0,
        $length
    )

    $Position.Value = $Position.Value + $length

    return $result
}


# ============================================================
# UTF-8 STRING
# ============================================================

function Read-WeatherHubString {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    $raw = Read-WeatherHubBytes $Data $Position $End

    return [Text.Encoding]::UTF8.GetString($raw)
}


# ============================================================
# SKIP UNKNOWN FIELD
# ============================================================

function Skip-WeatherHubField {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End,
        [int]$WireType
    )

    switch ($WireType) {

        # VARINT
        0 {
            [void](Read-WeatherHubVarint $Data $Position $End)
        }

        # FIXED64
        1 {
            if (($Position.Value + 8) -gt $End) {
                throw "Invalid fixed64 field"
            }

            $Position.Value = $Position.Value + 8
        }

        # LENGTH DELIMITED
        2 {
            [void](Read-WeatherHubBytes $Data $Position $End)
        }

        # FIXED32
        5 {
            if (($Position.Value + 4) -gt $End) {
                throw "Invalid fixed32 field"
            }

            $Position.Value = $Position.Value + 4
        }

        default {
            throw "Unsupported wire type: $WireType"
        }
    }
}


# ============================================================
# GENERIC MESSAGE READER
# ============================================================

function Read-WeatherHubMessage {
    param(
        [byte[]]$Data,
        [int]$Start,
        [int]$Length,
        [string]$MessageType
    )

    $pos = $Start
    $end = $Start + $Length

    $result = [ordered]@{}

    while ($pos -lt $end) {

        $tag = Read-WeatherHubVarint `
            $Data `
            ([ref]$pos) `
            $end

        $fieldNumber = [int]($tag -shr 3)
        $wireType = [int]($tag -band 7)


        # ====================================================
        # ChartData
        # ====================================================

        if ($MessageType -eq "ChartData") {

            if ($fieldNumber -eq 1 -and $wireType -eq 2) {

                $raw = Read-WeatherHubBytes `
                    $Data `
                    ([ref]$pos) `
                    $end

                if (-not $result.Contains("Series")) {
                    $result.Series = @()
                }

                $series = Read-WeatherHubMessage `
                    $raw `
                    0 `
                    $raw.Length `
                    "ChartSeries"

                $result.Series += $series
            }
            else {

                Skip-WeatherHubField `
                    $Data `
                    ([ref]$pos) `
                    $end `
                    $wireType
            }

            continue
        }


        # ====================================================
        # ChartSeries
        # ====================================================

        if ($MessageType -eq "ChartSeries") {

            switch ($fieldNumber) {

                1 {
                    if ($wireType -eq 2) {
                        $result.SeriesID =
                            Read-WeatherHubString `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                2 {
                    if ($wireType -eq 2) {

                        $raw = Read-WeatherHubBytes `
                            $Data `
                            ([ref]$pos) `
                            $end

                        if (-not $result.Contains("Datasets")) {
                            $result.Datasets = @()
                        }

                        $dataset = Read-WeatherHubMessage `
                            $raw `
                            0 `
                            $raw.Length `
                            "ChartDataset"

                        $result.Datasets += $dataset
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                3 {
                    if ($wireType -eq 2) {
                        $result.LineColor =
                            Read-WeatherHubString `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                4 {
                    if ($wireType -eq 2) {
                        $result.FormattedTimestamp =
                            Read-WeatherHubString `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                5 {
                    if ($wireType -eq 2) {
                        $result.FormattedMeasurement =
                            Read-WeatherHubString `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                6 {
                    if ($wireType -eq 0) {
                        $result.ConnectionLost =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                7 {
                    if ($wireType -eq 0) {
                        $result.LowBattery =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                8 {
                    if ($wireType -eq 0) {
                        $result.AlertWasActive =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                9 {
                    if ($wireType -eq 2) {
                        $result.CardStatus =
                            Read-WeatherHubString `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                10 {
                    if ($wireType -eq 0) {
                        $result.AlertActive =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                11 {
                    if ($wireType -eq 0) {
                        $result.AlertSettingActive =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                default {
                    Skip-WeatherHubField `
                        $Data `
                        ([ref]$pos) `
                        $end `
                        $wireType
                }
            }

            continue
        }


        # ====================================================
        # ChartDataset
        # ====================================================

        if ($MessageType -eq "ChartDataset") {

            switch ($fieldNumber) {

                1 {
                    if ($wireType -eq 1) {
                        $result.Timestamp =
                            Read-WeatherHubDouble `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                2 {
                    if ($wireType -eq 1) {
                        $result.Value =
                            Read-WeatherHubDouble `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                3 {
                    if ($wireType -eq 0) {
                        $result.AlertIsActive =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                # Measurement bewusst weiterhin ignoriert
                4 {
                    Skip-WeatherHubField `
                        $Data `
                        ([ref]$pos) `
                        $end `
                        $wireType
                }

                5 {
                    if ($wireType -eq 2) {
                        $result.Tooltip =
                            Read-WeatherHubString `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                6 {
                    if ($wireType -eq 0) {
                        $result.HiAlert =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                7 {
                    if ($wireType -eq 0) {
                        $result.HiStartEvent =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                8 {
                    if ($wireType -eq 0) {
                        $result.HiEndEvent =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                9 {
                    if ($wireType -eq 1) {
                        $result.HiSetting =
                            Read-WeatherHubDouble `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                10 {
                    if ($wireType -eq 0) {
                        $result.LoAlert =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                11 {
                    if ($wireType -eq 0) {
                        $result.LoStartEvent =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                12 {
                    if ($wireType -eq 0) {
                        $result.LoEndEvent =
                            ((Read-WeatherHubVarint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                13 {
                    if ($wireType -eq 1) {
                        $result.LoSetting =
                            Read-WeatherHubDouble `
                                $Data `
                                ([ref]$pos) `
                                $end
                    }
                    else {
                        Skip-WeatherHubField `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }

                default {
                    Skip-WeatherHubField `
                        $Data `
                        ([ref]$pos) `
                        $end `
                        $wireType
                }
            }

            continue
        }
    }

    return [PSCustomObject]$result
}


# ============================================================
# PUBLIC DECODER FUNCTION
# ============================================================

function Convert-WeatherHubBase64 {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Base64
    )

    if ([string]::IsNullOrWhiteSpace($Base64)) {
        throw "Base64 input is empty"
    }

    $Base64 = $Base64.Trim()

    try {
        $bytes = [Convert]::FromBase64String($Base64)
    }
    catch {
        throw "Invalid WeatherHub Base64 payload: $($_.Exception.Message)"
    }

    if ($bytes.Length -eq 0) {
        throw "Decoded WeatherHub payload is empty"
    }

    return Read-WeatherHubMessage `
        $bytes `
        0 `
        $bytes.Length `
        "ChartData"
}


# ============================================================
# PUBLIC HELPER
# ============================================================

function Convert-WeatherHubTimestamp {
    param(
        [Parameter(Mandatory=$true)]
        [double]$Timestamp
    )

    return (
        [DateTimeOffset]::FromUnixTimeMilliseconds(
            [Int64]$Timestamp
        )
    )
}


# ============================================================
# Optional file helper
#
# This keeps the v2 decoder convenient for fixture testing,
# without making InputFile mandatory when the file is loaded.
# ============================================================

function Convert-WeatherHubFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$InputFile
    )

    $b64 = (Get-Content $InputFile -Raw).Trim()

    return Convert-WeatherHubBase64 $b64
}
