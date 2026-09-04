#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$ConfigPath = '.docs-authority.json',
    [switch]$FailOnGap,
    [switch]$Markdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$resolvedConfigPath = if ([IO.Path]::IsPathRooted($ConfigPath)) {
    $ConfigPath
}
else {
    Join-Path $repositoryRoot $ConfigPath
}

if (-not (Test-Path -LiteralPath $resolvedConfigPath -PathType Leaf)) {
    Write-Error "Authority map not found at $resolvedConfigPath. This repository is not compliant."
    exit 1
}

$config = Get-Content -LiteralPath $resolvedConfigPath -Raw | ConvertFrom-Json
if ($config.standardVersion -ne '2.2') {
    Write-Error "Expected documentation standard 2.2, found '$($config.standardVersion)'."
    exit 1
}

$maxDrift = if ($config.maxDriftDays) { [int]$config.maxDriftDays } else { 30 }
$responsibilityNames = @($config.responsibilities.PSObject.Properties.Name)
$tier = [string]$config.tier
$tierLevel = switch ($tier) {
    '0' { 0 }
    '1' { 1 }
    '2' { 2 }
    '2C' { 3 }
    default { throw "Unsupported project tier '$tier'." }
}
$requiredResponsibilities = @('Project overview', 'Change history')
if ($tierLevel -ge 1) {
    $requiredResponsibilities += @(
        'Agent rules',
        'Development rules',
        'Current assessment',
        'Technical debt',
        'Deferred improvements',
        'Validation'
    )
}
if ($tierLevel -ge 2) {
    $requiredResponsibilities += @(
        'Architecture',
        'Defect tracking',
        'Operations',
        'Decision history',
        'Resolved history'
    )
}
if ($tier -eq '2C') {
    $requiredResponsibilities += @(
        'Agreed scope',
        'Agreed design',
        'Scope amendments',
        'Requirement traceability'
    )
}

function Get-LastCommitDate {
    param([string]$RelativePath)

    $iso = & git -C $repositoryRoot log -1 --format=%cI -- $RelativePath 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($iso)) {
        return $null
    }
    return [datetimeoffset]::Parse($iso)
}

function Test-PathDirty {
    param([string]$RelativePath)

    $status = & git -C $repositoryRoot status --porcelain -- $RelativePath 2>$null
    return -not [string]::IsNullOrWhiteSpace(($status -join "`n"))
}

$sourceDates = foreach ($sourcePath in $config.sourcePaths) {
    if (Test-PathDirty -RelativePath $sourcePath) {
        [datetimeoffset]::Now
    }
    else {
        Get-LastCommitDate -RelativePath $sourcePath
    }
}
$sourceDate = $sourceDates | Where-Object { $_ } | Sort-Object -Descending | Select-Object -First 1

$rows = @()
foreach ($required in $requiredResponsibilities) {
    if ($required -notin $responsibilityNames) {
        $rows += [pscustomobject]@{
            Responsibility = $required
            Authority      = ''
            Status         = 'MISSING'
            LastUpdated    = ''
        }
    }
}

foreach ($name in $responsibilityNames) {
    $entry = $config.responsibilities.$name
    $authority = [string]$entry.authority
    $class = [string]$entry.class

    if ($authority -in @('Not required at this tier', 'External tracker')) {
        $status = if ($name -in $requiredResponsibilities) { 'MISSING' } else { 'Not required' }
        $rows += [pscustomobject]@{
            Responsibility = $name
            Authority      = $authority
            Status         = $status
            LastUpdated    = ''
        }
        continue
    }

    if ($class -notin @('living', 'contractual', 'derived', 'governance')) {
        $rows += [pscustomobject]@{
            Responsibility = $name
            Authority      = $authority
            Status         = 'INVALID CLASS'
            LastUpdated    = ''
        }
        continue
    }

    $authorityPath = [IO.Path]::GetFullPath((Join-Path $repositoryRoot $authority))
    $insideRepository = $authorityPath.StartsWith(
        $repositoryRoot + [IO.Path]::DirectorySeparatorChar,
        [StringComparison]::OrdinalIgnoreCase
    )
    if (-not $insideRepository -or -not (Test-Path -LiteralPath $authorityPath)) {
        $rows += [pscustomobject]@{
            Responsibility = $name
            Authority      = $authority
            Status         = 'MISSING'
            LastUpdated    = ''
        }
        continue
    }

    $docDate = Get-LastCommitDate -RelativePath $authority
    $isDirty = Test-PathDirty -RelativePath $authority
    $updated = if ($isDirty -or -not $docDate) { 'uncommitted' } else { $docDate.ToString('yyyy-MM-dd') }

    if ($class -ne 'living' -or $isDirty -or -not $sourceDate -or -not $docDate) {
        $status = 'Current'
    }
    else {
        $drift = [int]($sourceDate - $docDate).TotalDays
        $status = if ($drift -gt $maxDrift) { "REVIEW ($($drift)d)" } else { 'Current' }
    }

    $rows += [pscustomobject]@{
        Responsibility = $name
        Authority      = $authority
        Status         = $status
        LastUpdated    = $updated
    }
}

if ($Markdown) {
    '| Responsibility | Authority | Last updated | Status |'
    '|---|---|---|---|'
    $rows | ForEach-Object {
        "| $($_.Responsibility) | $($_.Authority) | $($_.LastUpdated) | $($_.Status) |"
    }
}
else {
    $rows | Format-Table -AutoSize
}

$gaps = $rows | Where-Object {
    $_.Status -eq 'MISSING' -or $_.Status -like 'REVIEW*' -or $_.Status -like 'INVALID*'
}
if ($gaps -and $FailOnGap) {
    exit 1
}
