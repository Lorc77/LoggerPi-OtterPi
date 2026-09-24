$ErrorActionPreference = 'Stop'

$localIp = [System.Net.IPAddress]::Parse('141.51.190.135')
$broadcastIp = [System.Net.IPAddress]::Parse('255.255.255.255')

$gatewayIp = '141.51.190.121'
$gatewayMac = '00-1D-8C-0D-F8-1C'

$gatewayId = [byte[]](
    0x00, 0x1D, 0x8C,
    0x0D, 0xF8, 0x1C
)

function Read-UInt16BigEndian {
    param(
        [byte[]]$Data,
        [int]$Offset
    )

    $high = [int]$Data[$Offset]
    $low = [int]$Data[$Offset + 1]

    return (($high -shl 8) -bor $low)
}

function Read-FixedAscii {
    param(
        [byte[]]$Data,
        [int]$Offset,
        [int]$Length
    )

    $bytes = $Data[$Offset..($Offset + $Length - 1)]
    $zeroIndex = [Array]::IndexOf($bytes, [byte]0)

    if ($zeroIndex -eq 0) {
        return ''
    }

    if ($zeroIndex -gt 0) {
        $bytes = $bytes[0..($zeroIndex - 1)]
    }

    return [Text.Encoding]::ASCII.GetString($bytes)
}

function Read-IPv4 {
    param(
        [byte[]]$Data,
        [int]$Offset
    )

    return @(
        $Data[$Offset]
        $Data[$Offset + 1]
        $Data[$Offset + 2]
        $Data[$Offset + 3]
    ) -join '.'
}

function Receive-GatewayConfig {
    param(
        [System.Net.Sockets.UdpClient]$Udp,
        [byte[]]$Request,
        [string]$LocalIp
    )

    $target = [System.Net.IPEndPoint]::new(
        [System.Net.IPAddress]::Parse('255.255.255.255'),
        8003
    )

    [void]$Udp.Send(
        $Request,
        $Request.Length,
        $target
    )

    $deadline = [DateTime]::UtcNow.AddSeconds(10)

    while ([DateTime]::UtcNow -lt $deadline) {
        $remote = [System.Net.IPEndPoint]::new(
            [System.Net.IPAddress]::Any,
            0
        )

        try {
            $response = $Udp.Receive([ref]$remote)
        }
        catch [System.Net.Sockets.SocketException] {
            break
        }

        if ($remote.Address.ToString() -eq $LocalIp) {
            Write-Host 'Eigenes Broadcast-Paket ignoriert.'
            continue
        }

        if ($remote.Address.ToString() -ne $gatewayIp) {
            Write-Host "Antwort von anderem Host ignoriert: $($remote.Address)"
            continue
        }

        if ($response.Length -ne 186) {
            throw "Unerwartete Antwortlänge: $($response.Length)"
        }

        $command = Read-UInt16BigEndian $response 0
        $declaredLength = Read-UInt16BigEndian $response 8

        if ($command -ne 3) {
            throw "Unerwarteter Antwort-Command: $command"
        }

        if ($declaredLength -ne 186) {
            throw "Unerwartete deklarierte Länge: $declaredLength"
        }

        $responseGatewayId = (($response[2..7] | ForEach-Object {
            $_.ToString('X2')
        }) -join '-')

        if ($responseGatewayId -ne $gatewayMac) {
            throw "Falsche Gateway-ID: $responseGatewayId"
        }

        return $response
    }

    throw "Keine gültige Get-Config-Antwort von $gatewayIp erhalten."
}

$request = [byte[]](
    0x00, 0x02,
    $gatewayId[0], $gatewayId[1], $gatewayId[2],
    $gatewayId[3], $gatewayId[4], $gatewayId[5],
    0x00, 0x0A
)

$udp = [System.Net.Sockets.UdpClient]::new(
    [System.Net.IPEndPoint]::new($localIp, 8003)
)

try {
    $udp.EnableBroadcast = $true
    $udp.Client.ReceiveTimeout = 10000

    Write-Host 'Lese aktuelle Gateway-Konfiguration ...'
    $original = Receive-GatewayConfig `
        -Udp $udp `
        -Request $request `
        -LocalIp $localIp.ToString()

    $currentName = Read-FixedAscii $original 28 21
    $currentUseProxy = [int]$original[114]
    $currentProxyHost = Read-FixedAscii $original 115 65
    $currentProxyPort = Read-UInt16BigEndian $original 180

    Write-Host ''
    Write-Host 'Aktuelle Konfiguration:'
    Write-Host "  Name:       $currentName"
    Write-Host "  Use Proxy:  $currentUseProxy"
    Write-Host "  Proxy Host: $currentProxyHost"
    Write-Host "  Proxy Port: $currentProxyPort"
    Write-Host ''

    $packet = New-Object byte[] 181

    # Command 4
    $packet[0] = 0x00
    $packet[1] = 0x04

    # Gateway-ID unverändert
    [Array]::Copy($original, 2, $packet, 2, 6)

    # Länge 181
    $packet[8] = 0x00
    $packet[9] = 0xB5

    # Alle nicht-proxybezogenen Werte unverändert übernehmen
    [Array]::Copy($original, 15, $packet, 10, 1)  # Use DHCP
    [Array]::Copy($original, 16, $packet, 11, 4)  # Fixed IP
    [Array]::Copy($original, 20, $packet, 15, 4)  # Netmask
    [Array]::Copy($original, 24, $packet, 19, 4)  # Gateway
    [Array]::Copy($original, 28, $packet, 23, 21) # Name
    [Array]::Copy($original, 49, $packet, 44, 65) # Data Server

    # Proxy zurück auf ursprüngliche Werte
    $packet[109] = 0x00

    $originalProxyHost = [Text.Encoding]::ASCII.GetBytes(
        '192.168.1.1'
    )

    [Array]::Clear($packet, 110, 65)

    [Array]::Copy(
        $originalProxyHost,
        0,
        $packet,
        110,
        $originalProxyHost.Length
    )

    # Port 80, Big-Endian: 00 50
    $packet[175] = 0x00
    $packet[176] = 0x50

    # DNS unverändert
    [Array]::Copy($original, 182, $packet, 177, 4)

    $outputPath = Join-Path `
        'C:\Users\LH\Desktop' `
        'gateway_141_51_190_121_cloud_restore.bin'

    [System.IO.File]::WriteAllBytes(
        $outputPath,
        $packet
    )

    $newProxyPort = Read-UInt16BigEndian $packet 175
    $newProxyHost = Read-FixedAscii $packet 110 65
    $newName = Read-FixedAscii $packet 23 21

    Write-Host 'Neues Restore-Paket:'
    Write-Host "  Länge:      $($packet.Length)"
    Write-Host "  Name:       $newName"
    Write-Host "  Use Proxy:  $([int]$packet[109])"
    Write-Host "  Proxy Host: $newProxyHost"
    Write-Host "  Proxy Port: $newProxyPort"
    Write-Host "  Datei:      $outputPath"
    Write-Host ''

    if ($packet.Length -ne 181) {
        throw 'Restore-Paket hat nicht 181 Bytes.'
    }

    if ($newName -ne $currentName) {
        throw 'Der Gateway-Name wurde unerwartet verändert.'
    }

    if ([int]$packet[109] -ne 0) {
        throw 'Use Proxy ist nicht deaktiviert.'
    }

    if ($newProxyHost -ne '192.168.1.1') {
        throw 'Proxy-Host ist nicht auf 192.168.1.1 gesetzt.'
    }

    if ($newProxyPort -ne 80) {
        throw "Proxy-Port ist nicht 80, sondern $newProxyPort."
    }

    Write-Host 'Lokale Prüfung erfolgreich.'
    Write-Host 'Name bleibt unverändert; nur die Proxy-Konfiguration wird zurückgesetzt.'
    Write-Host ''

    $confirmation = Read-Host `
        'Zum tatsächlichen Senden exakt SEND eingeben'

    if ($confirmation -cne 'SEND') {
        Write-Host 'Nicht gesendet.'
        exit 0
    }

    $target = [System.Net.IPEndPoint]::new(
        [System.Net.IPAddress]::Parse('255.255.255.255'),
        8003
    )

    Write-Host 'Sende Cloud-Restore-Paket ...'

    [void]$udp.Send(
        $packet,
        $packet.Length,
        $target
    )

    Write-Host 'Cloud-Restore-Paket gesendet.'
    Write-Host 'Kein Reboot-Befehl wurde gesendet.'
}
finally {
    $udp.Close()
    Write-Host 'UDP-Socket geschlossen.'
}
