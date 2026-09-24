$ErrorActionPreference = 'Stop'

$packetPath = 'C:\Users\LH\Desktop\gateway_141_51_190_121_proxy_test.bin'
$expectedHash = '8FB7E0B48E5B5E19C93D29ABC7FAE35381D26AE38EA17265CB08AA81AA4AC61C'

$localIp = [System.Net.IPAddress]::Parse('141.51.190.135')
$broadcastIp = [System.Net.IPAddress]::Parse('255.255.255.255')

$packet = [System.IO.File]::ReadAllBytes($packetPath)

$actualHash = (
    Get-FileHash `
        -LiteralPath $packetPath `
        -Algorithm SHA256
).Hash.ToUpperInvariant()

if ($actualHash -ne $expectedHash) {
    throw (
        "SHA-256 stimmt nicht überein.`n" +
        "Erwartet: $expectedHash`n" +
        "Gefunden: $actualHash"
    )
}

if ($packet.Length -ne 181) {
    throw "Falsche Paketlänge: $($packet.Length), erwartet: 181."
}

$command = (([int]$packet[0] -shl 8) -bor [int]$packet[1])
$declaredLength = (([int]$packet[8] -shl 8) -bor [int]$packet[9])

if ($command -ne 4) {
    throw "Falscher Command: $command, erwartet: 4."
}

if ($declaredLength -ne 181) {
    throw "Falsche deklarierte Länge: $declaredLength, erwartet: 181."
}

Write-Host ''
Write-Host '========================================'
Write-Host 'WeatherHub Proxy-Konfiguration senden'
Write-Host '========================================'
Write-Host ''
Write-Host "Datei:             $packetPath"
Write-Host "SHA-256:           $actualHash"
Write-Host "Paketlänge:        $($packet.Length) Bytes"
Write-Host "Command:           $command"
Write-Host "Zielgateway:       141.51.190.121"
Write-Host "Proxy-Ziel:        141.51.190.103:3778"
Write-Host ''
Write-Host 'WARNUNG: Gateway .121 wird jetzt auf den LoggerPi-Proxy umgestellt.'
Write-Host 'Der LoggerPi-Testlistener leitet derzeit NICHT zur TFA-Cloud weiter.'
Write-Host ''

$confirmation = Read-Host 'Zum tatsächlichen Senden exakt SEND eingeben'

if ($confirmation -cne 'SEND') {
    Write-Host 'Nicht gesendet.'
    exit 0
}

$udp = [System.Net.Sockets.UdpClient]::new(
    [System.Net.IPEndPoint]::new($localIp, 8003)
)

try {
    $udp.EnableBroadcast = $true

    $target = [System.Net.IPEndPoint]::new(
        $broadcastIp,
        8003
    )

    Write-Host 'Sende Command 4 per UDP-Broadcast ...'

    [void]$udp.Send(
        $packet,
        $packet.Length,
        $target
    )

    Write-Host 'Command-4-Paket gesendet.'
}
finally {
    $udp.Close()
    Write-Host 'UDP-Socket geschlossen.'
}
