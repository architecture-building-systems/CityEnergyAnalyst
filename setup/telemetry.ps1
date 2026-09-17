param(
    [string]$ApiKey,
    [string]$PostHogHost,
    [string]$EventName,
    [string]$CeaVersion,
    [string]$InstallerStep,
    [string]$ErrorCode,
    [string]$ErrorDetail
)

# Fire-and-forget anonymous installer telemetry. This must never affect the
# installer's outcome: any failure here (bad network, blocked endpoint,
# timeout) is swallowed, and the exit code is always 0.
try {
    $distinctId = [guid]::NewGuid().ToString()

    $properties = @{
        cea_version                = $CeaVersion
        os                         = "windows"
        arch                       = $env:PROCESSOR_ARCHITECTURE
        '$process_person_profile' = $false
    }

    if ($InstallerStep) { $properties.installer_step = $InstallerStep }
    if ($ErrorCode)      { $properties.error_code     = $ErrorCode }
    if ($ErrorDetail)    { $properties.error_detail    = $ErrorDetail.Substring(0, [Math]::Min(64, $ErrorDetail.Length)) }

    $body = @{
        api_key     = $ApiKey
        event       = $EventName
        distinct_id = $distinctId
        properties  = $properties
    } | ConvertTo-Json -Depth 6 -Compress

    Invoke-RestMethod -Uri $PostHogHost -Method Post -Body $body -ContentType "application/json" -TimeoutSec 3 | Out-Null
}
catch {
    # Intentionally ignored - see comment above.
}

# Best-effort tidy-up of the $TEMP copy the installer left behind. Not required
# for correctness (the installer overwrites it on the next run) and must never
# affect the exit code, so failures here are swallowed too.
try {
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
}
catch {
}

exit 0
