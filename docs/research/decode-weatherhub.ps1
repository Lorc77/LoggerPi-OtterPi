param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile
)

# ============================================================
# WeatherHub Observer - ChartData Proto2 Decoder
#
# ChartData
#   field 1 = Series (repeated ChartSeries)
#
# ChartSeries
#   field 1  = SeriesID              string
#   field 2  = Datasets              repeated ChartDataset
#   field 3  = LineColor             string
#   field 4  = FormattedTimestamp    string
#   field 5  = FormattedMeasurement  string
#   field 6  = ConnectionLost        bool
#   field 7  = LowBattery            bool
#   field 8  = AlertWasActive        bool
#   field 9  = CardStatus            string
#   field 10 = AlertActive           bool
#   field 11 = AlertSettingActive    bool
#
# ChartDataset
#   field 1  = Timestamp             double
#   field 2  = Value                 double
#   field 3  = AlertIsActive         bool
#   field 4  = Measurement            message
#   field 5  = Tooltip                string
#   field 6  = HiAlert                bool
#   field 7  = HiStartEvent           bool
#   field 8  = HiEndEvent             bool
#   field 9  = HiSetting              double
#   field 10 = LoAlert                bool
#   field 11 = LoStartEvent           bool
#   field 12 = LoEndEvent             bool
#   field 13 = LoSetting              double
#
# Proto wire types:
#
#   0 = varint
#   1 = fixed64
#   2 = length-delimited
#   5 = fixed32
# ============================================================


# ============================================================
# Read Base64
# ============================================================

$b64 = (Get-Content $InputFile -Raw).Trim()

$bytes = [Convert]::FromBase64String($b64)

Write-Host ""
Write-Host "Input:"
Write-Host "  Base64 length : $($b64.Length)"
Write-Host "  Byte count    : $($bytes.Length)"
Write-Host ""


# ============================================================
# VARINT
#
# Position is passed by reference because this function
# advances the caller's cursor.
# ============================================================

function Read-Varint {
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
# DOUBLE / FIXED64
# ============================================================

function Read-Double {
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
#
# IMPORTANT:
# $Position is already a PSReference here.
# Therefore we pass $Position directly to Read-Varint.
# ============================================================

function Read-Bytes {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    $length = Read-Varint $Data $Position $End

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

function Read-String {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End
    )

    $raw = Read-Bytes $Data $Position $End

    return [Text.Encoding]::UTF8.GetString($raw)
}


# ============================================================
# SKIP UNKNOWN FIELD
# ============================================================

function Skip-Field {
    param(
        [byte[]]$Data,
        [ref]$Position,
        [int]$End,
        [int]$WireType
    )

    switch ($WireType) {

        # VARINT
        0 {
            [void](Read-Varint $Data $Position $End)
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
            [void](Read-Bytes $Data $Position $End)
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

function Read-Message {
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

        # IMPORTANT:
        # Here $pos is a normal Int32 variable,
        # therefore [ref] is required.
        $tag = Read-Varint $Data ([ref]$pos) $end

        $fieldNumber = [int]($tag -shr 3)
        $wireType = [int]($tag -band 7)


        # ====================================================
        # ChartData
        # ====================================================

        if ($MessageType -eq "ChartData") {

            if ($fieldNumber -eq 1 -and $wireType -eq 2) {

                $raw = Read-Bytes $Data ([ref]$pos) $end

                if (-not $result.Contains("Series")) {
                    $result.Series = @()
                }

                $series = Read-Message `
                    $raw `
                    0 `
                    $raw.Length `
                    "ChartSeries"

                $result.Series += $series
            }
            else {

                Skip-Field `
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

                # --------------------------------------------
                # field 1 = SeriesID
                # --------------------------------------------

                1 {

                    if ($wireType -eq 2) {

                        $result.SeriesID =
                            Read-String $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 2 = Datasets
                # --------------------------------------------

                2 {

                    if ($wireType -eq 2) {

                        $raw = Read-Bytes $Data ([ref]$pos) $end

                        if (-not $result.Contains("Datasets")) {
                            $result.Datasets = @()
                        }

                        $dataset = Read-Message `
                            $raw `
                            0 `
                            $raw.Length `
                            "ChartDataset"

                        $result.Datasets += $dataset
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 3 = LineColor
                # --------------------------------------------

                3 {

                    if ($wireType -eq 2) {

                        $result.LineColor =
                            Read-String $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 4 = FormattedTimestamp
                # --------------------------------------------

                4 {

                    if ($wireType -eq 2) {

                        $result.FormattedTimestamp =
                            Read-String $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 5 = FormattedMeasurement
                # --------------------------------------------

                5 {

                    if ($wireType -eq 2) {

                        $result.FormattedMeasurement =
                            Read-String $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 6 = ConnectionLost
                # --------------------------------------------

                6 {

                    if ($wireType -eq 0) {

                        $result.ConnectionLost =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 7 = LowBattery
                # --------------------------------------------

                7 {

                    if ($wireType -eq 0) {

                        $result.LowBattery =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 8 = AlertWasActive
                # --------------------------------------------

                8 {

                    if ($wireType -eq 0) {

                        $result.AlertWasActive =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 9 = CardStatus
                # --------------------------------------------

                9 {

                    if ($wireType -eq 2) {

                        $result.CardStatus =
                            Read-String $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 10 = AlertActive
                # --------------------------------------------

                10 {

                    if ($wireType -eq 0) {

                        $result.AlertActive =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 11 = AlertSettingActive
                # --------------------------------------------

                11 {

                    if ($wireType -eq 0) {

                        $result.AlertSettingActive =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # Unknown field
                # --------------------------------------------

                default {

                    Skip-Field `
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

                # --------------------------------------------
                # field 1 = Timestamp
                # wire type 1 = fixed64 / double
                # --------------------------------------------

                1 {

                    if ($wireType -eq 1) {

                        $result.Timestamp =
                            Read-Double $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 2 = Value
                # wire type 1 = fixed64 / double
                # --------------------------------------------

                2 {

                    if ($wireType -eq 1) {

                        $result.Value =
                            Read-Double $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 3 = AlertIsActive
                # --------------------------------------------

                3 {

                    if ($wireType -eq 0) {

                        $result.AlertIsActive =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 4 = Measurement
                #
                # We deliberately skip this for now.
                # --------------------------------------------

                4 {

                    Skip-Field `
                        $Data `
                        ([ref]$pos) `
                        $end `
                        $wireType
                }


                # --------------------------------------------
                # field 5 = Tooltip
                # --------------------------------------------

                5 {

                    if ($wireType -eq 2) {

                        $result.Tooltip =
                            Read-String $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 6 = HiAlert
                # --------------------------------------------

                6 {

                    if ($wireType -eq 0) {

                        $result.HiAlert =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 7 = HiStartEvent
                # --------------------------------------------

                7 {

                    if ($wireType -eq 0) {

                        $result.HiStartEvent =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 8 = HiEndEvent
                # --------------------------------------------

                8 {

                    if ($wireType -eq 0) {

                        $result.HiEndEvent =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 9 = HiSetting
                # --------------------------------------------

                9 {

                    if ($wireType -eq 1) {

                        $result.HiSetting =
                            Read-Double $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 10 = LoAlert
                # --------------------------------------------

                10 {

                    if ($wireType -eq 0) {

                        $result.LoAlert =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 11 = LoStartEvent
                # --------------------------------------------

                11 {

                    if ($wireType -eq 0) {

                        $result.LoStartEvent =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 12 = LoEndEvent
                # --------------------------------------------

                12 {

                    if ($wireType -eq 0) {

                        $result.LoEndEvent =
                            ((Read-Varint `
                                $Data `
                                ([ref]$pos) `
                                $end) -ne 0)
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # field 13 = LoSetting
                # --------------------------------------------

                13 {

                    if ($wireType -eq 1) {

                        $result.LoSetting =
                            Read-Double $Data ([ref]$pos) $end
                    }
                    else {

                        Skip-Field `
                            $Data `
                            ([ref]$pos) `
                            $end `
                            $wireType
                    }
                }


                # --------------------------------------------
                # Unknown field
                # --------------------------------------------

                default {

                    Skip-Field `
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
# Decode complete ChartData
# ============================================================

$chart = Read-Message `
    $bytes `
    0 `
    $bytes.Length `
    "ChartData"


# ============================================================
# Human-readable output
# ============================================================

Write-Host "ChartData"
Write-Host "  Series: $($chart.Series.Count)"
Write-Host ""


$seriesIndex = 0


foreach ($series in $chart.Series) {

    Write-Host "============================================================"
    Write-Host "Series[$seriesIndex]"
    Write-Host "============================================================"

    Write-Host "SeriesID:             $($series.SeriesID)"
    Write-Host "LineColor:            $($series.LineColor)"
    Write-Host "FormattedTimestamp:   $($series.FormattedTimestamp)"
    Write-Host "FormattedMeasurement: $($series.FormattedMeasurement)"
    Write-Host "ConnectionLost:       $($series.ConnectionLost)"
    Write-Host "LowBattery:           $($series.LowBattery)"
    Write-Host "AlertWasActive:       $($series.AlertWasActive)"
    Write-Host "CardStatus:           $($series.CardStatus)"
    Write-Host "AlertActive:          $($series.AlertActive)"
    Write-Host "AlertSettingActive:   $($series.AlertSettingActive)"
    Write-Host "Datasets:             $($series.Datasets.Count)"
    Write-Host ""


    $datasetIndex = 0


    foreach ($ds in $series.Datasets) {

        $timestampText = ""

        if ($null -ne $ds.Timestamp) {

            $timestampText =
                ([DateTimeOffset]::FromUnixTimeMilliseconds(
                    [Int64]$ds.Timestamp
                )).ToString("yyyy-MM-dd HH:mm:ss")
        }


        Write-Host (
            "Dataset[{0}]  {1}  Value={2}" -f `
            $datasetIndex,
            $timestampText,
            $ds.Value
        )


        # ----------------------------------------------------
        # Only display fields that are actually present.
        #
        # This is important for proto2:
        #
        # absent != explicit false
        # ----------------------------------------------------

        $flags = @()


        foreach ($name in @(
            "AlertIsActive",
            "HiAlert",
            "HiStartEvent",
            "HiEndEvent",
            "HiSetting",
            "LoAlert",
            "LoStartEvent",
            "LoEndEvent",
            "LoSetting"
        )) {

            if ($ds.PSObject.Properties.Name -contains $name) {

                $flags += "$name=$($ds.$name)"
            }
        }


        if ($flags.Count -gt 0) {

            Write-Host (
                "             " + ($flags -join "  ")
            )
        }


        $datasetIndex++
    }


    Write-Host ""

    $seriesIndex++
}


Write-Host "============================================================"
Write-Host "Decode complete."
Write-Host "============================================================"
Write-Host ""