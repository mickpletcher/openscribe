[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$BundleRoot,
    [string]$WorkRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$bundle = [IO.Path]::GetFullPath($BundleRoot)
$desktop = Join-Path $bundle "OpenScribe.exe"
$cli = Join-Path $bundle "openscribe-cli.exe"
$license = Join-Path $bundle "LICENSE.txt"
$thirdPartyLicenses = Join-Path $bundle "THIRD-PARTY-LICENSES.txt"
$createdWorkRoot = -not $WorkRoot
if ($createdWorkRoot) {
    $WorkRoot = Join-Path ([IO.Path]::GetTempPath()) ("openscribe-package-smoke-" + [guid]::NewGuid().ToString("N"))
}
$work = [IO.Path]::GetFullPath($WorkRoot)
$project = Join-Path $work "smoke-project"

function Invoke-Checked([string]$Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE."
    }
}

function Invoke-DesktopSmoke {
    $process = Start-Process -FilePath $desktop -ArgumentList "--smoke-test" -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        $errorLog = Join-Path $env:LOCALAPPDATA "OpenScribe\openscribe-error.log"
        if (Test-Path -LiteralPath $errorLog) {
            Get-Content -LiteralPath $errorLog | Write-Output
        }
        throw "$desktop failed with exit code $($process.ExitCode)."
    }
}

if (-not (Test-Path -LiteralPath $desktop -PathType Leaf)) {
    throw "Desktop executable is missing: $desktop"
}
if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) {
    throw "CLI executable is missing: $cli"
}
if (-not (Test-Path -LiteralPath $license -PathType Leaf)) {
    throw "OpenScribe license is missing: $license"
}
if (-not (Test-Path -LiteralPath $thirdPartyLicenses -PathType Leaf)) {
    throw "Third-party license notice is missing: $thirdPartyLicenses"
}

try {
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    Invoke-DesktopSmoke
    Invoke-Checked $cli @("--help")
    Invoke-Checked $cli @("desktop", "--help")
    Invoke-Checked $cli @("init", "Package Smoke", "--path", $project, "--template", "fiction")

    Push-Location $project
    try {
        Invoke-Checked $cli @("new", "part", "Opening")
        Invoke-Checked $cli @("new", "chapter", "Arrival", "--part", "Opening")
        Invoke-Checked $cli @("new", "scene", "First Scene", "--chapter", "Arrival", "--body", "This is synthetic package test text.")
        Invoke-Checked $cli @("snapshot", "save", "package-smoke")
        $snapshot = Get-ChildItem -LiteralPath ".openscribe\snapshots" -Directory | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
        if (-not $snapshot) {
            throw "The package smoke snapshot was not created."
        }
        $chapter = Get-ChildItem -LiteralPath "manuscript" -Filter "*.md" -File -Recurse | Select-Object -First 1
        Add-Content -LiteralPath $chapter.FullName -Value "`nTemporary recovery test edit." -Encoding utf8
        Invoke-Checked $cli @("snapshot", "restore", $snapshot.Name)
        Invoke-Checked $cli @("snapshot", "restore", $snapshot.Name, "--apply")
        if ((Get-Content -LiteralPath $chapter.FullName -Raw).Contains("Temporary recovery test edit.")) {
            throw "Snapshot recovery did not restore the packaged project."
        }
        foreach ($format in @("docx", "pdf", "epub")) {
            Invoke-Checked $cli @("compile", "--format", $format)
        }
        Invoke-Checked $cli @("word", "--help")
    }
    finally {
        Pop-Location
    }

    foreach ($extension in @("docx", "pdf", "epub")) {
        if (-not (Get-ChildItem -LiteralPath (Join-Path $project "build") -Filter "*.$extension" -File)) {
            throw "The packaged CLI did not create a $extension export."
        }
    }
}
finally {
    if ($createdWorkRoot -and (Test-Path -LiteralPath $work)) {
        Remove-Item -LiteralPath $work -Recurse -Force
    }
}
