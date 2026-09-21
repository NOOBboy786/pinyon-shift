[CmdletBinding()]
param(
    [string]$StateRoot,
    [string]$Output,
    [string]$RenderTestScript = 'config/render-tests/fh1-race.fh1test',
    [ValidateRange(1, 3600)]
    [int]$TimeoutSeconds = 180,
    [ValidateRange(1, 32)]
    [int]$Parallel = [Math]::Max(2, [Math]::Min(16, [Environment]::ProcessorCount - 1)),
    [switch]$SkipBuild,
    [switch]$MarkersOnly,
    [switch]$OpenInWpa
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'release-common.ps1')

$root = Get-PinyonRepoRoot
$profile = Join-Path $root 'config/performance/pinyon-critical-path.wprp'
$build = Join-Path $root 'out/build/win-amd64-relwithdebinfo'
if (-not $Output) {
    $Output = Join-Path $root ('.local/cpu-profile/' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
$Output = [IO.Path]::GetFullPath($Output)
[void](New-Item -ItemType Directory -Force -Path $Output)

if (-not $StateRoot) {
    $StateRoot = Join-Path $env:LOCALAPPDATA 'PinyonShift/source/0.1.0/.local/preview'
}
$StateRoot = (Resolve-Path -LiteralPath $StateRoot).Path
$profiles = @(Get-ChildItem -LiteralPath (Join-Path $StateRoot 'user') -Filter ForzaProfile -File -Recurse |
    Where-Object { $_.Directory.Name -eq 'ForzaProfile' })
if (-not $profiles.Count) { throw 'Forza profile missing in the selected state root' }
if (Get-Process pinyon_shift -ErrorAction SilentlyContinue) { throw 'Game already running' }

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $MarkersOnly -and -not $isAdministrator) {
    throw 'CPU sampling and context-switch capture require an elevated PowerShell session.'
}
if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'build-preview.ps1') -Configuration RelWithDebInfo -Parallel $Parallel
    if ($LASTEXITCODE -ne 0) { throw 'RelWithDebInfo build failed' }
}

$symbols = & (Join-Path $PSScriptRoot 'verify-profile-symbols.ps1') -BuildDirectory $build -Json |
    ConvertFrom-Json
$symbolOutput = Join-Path $Output 'symbols'
[void](New-Item -ItemType Directory -Force -Path $symbolOutput)
foreach ($module in $symbols.modules) {
    foreach ($relative in @($module.binary, $module.pdb)) {
        $source = Join-Path $root $relative
        Copy-Item -LiteralPath $source -Destination (Join-Path $symbolOutput (Split-Path $source -Leaf))
    }
}
$symbols | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Output 'symbols.json')

$etl = Join-Path $Output 'pinyon-shift.etl'
$wprProfile = "$profile!PinyonCriticalPath.Verbose"
$wprArguments = if ($MarkersOnly) {
    @('-start', $wprProfile, '-filemode')
} else {
    @('-start', 'CPU.Verbose', '-start', $wprProfile, '-filemode')
}
$recording = $false
$startedUtc = [DateTime]::UtcNow
try {
    & wpr @wprArguments
    if ($LASTEXITCODE -ne 0) { throw "WPR failed to start (exit $LASTEXITCODE)" }
    $recording = $true
    & (Join-Path $PSScriptRoot 'launch-preview.ps1') -Configuration RelWithDebInfo `
        -StateRoot $StateRoot -RenderTestScript $RenderTestScript `
        -RenderTestOutput (Join-Path $Output 'render-test') `
        -RenderTestTimeoutSeconds $TimeoutSeconds -Hidden `
        -GameArguments @('--pinyon_shift_capture_performance=true', '--perf_log_max_mb=512') `
        -Json | Set-Content -LiteralPath (Join-Path $Output 'launch.json')
    if ($LASTEXITCODE -ne 0) { throw 'Profile route failed' }
    & wpr -stop $etl 'Pinyon Shift CPU hotspot capture'
    if ($LASTEXITCODE -ne 0) { throw "WPR failed to stop (exit $LASTEXITCODE)" }
    $recording = $false
}
finally {
    if ($recording) { & wpr -cancel | Out-Null }
}

$perfCapture = Get-ChildItem -LiteralPath (Join-Path $StateRoot 'logs') -Filter '*.perf.csv' -File |
    Where-Object { $_.LastWriteTimeUtc -ge $startedUtc.AddSeconds(-2) } |
    Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
if ($perfCapture) {
    Copy-Item -LiteralPath $perfCapture.FullName -Destination (Join-Path $Output 'frames.perf.csv')
}
$manifest = [ordered]@{
    schema = 'pinyon-shift.cpu-profile-capture.v1'
    created_utc = [DateTime]::UtcNow.ToString('o')
    markers_only = $MarkersOnly.IsPresent
    route = (Resolve-Path -LiteralPath $RenderTestScript).Path
    state_root = $StateRoot
    etl = $etl
    symbols = 'symbols.json'
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $Output 'capture.json')

if ($OpenInWpa) {
    $wpa = Get-Command wpa.exe -ErrorAction SilentlyContinue
    if (-not $wpa) { throw 'Windows Performance Analyzer is not installed' }
    Start-Process -FilePath $wpa.Source -ArgumentList @($etl)
}
$manifest
