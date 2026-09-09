[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Installer
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$installerPath = [IO.Path]::GetFullPath($Installer)
$temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
$installRoot = Join-Path ([IO.Path]::GetTempPath()) ("openscribe-install-smoke-" + [guid]::NewGuid().ToString("N"))
$projectWork = Join-Path ([IO.Path]::GetTempPath()) ("openscribe-install-project-" + [guid]::NewGuid().ToString("N"))
$startMenuLink = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\OpenScribe\OpenScribe command line.lnk"

foreach ($path in @($installRoot, $projectWork)) {
    $resolved = [IO.Path]::GetFullPath($path)
    if (-not $resolved.StartsWith($temporaryBase, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to use a smoke-test path outside the temporary directory: $resolved"
    }
}
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Installer is missing: $installerPath"
}

function Install-OpenScribe {
    $process = Start-Process -FilePath $installerPath -ArgumentList @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/MERGETASKS=!desktopicon",
        "/DIR=$installRoot"
    ) -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Installer failed with exit code $($process.ExitCode)."
    }
}

try {
    Install-OpenScribe
    if (-not (Test-Path -LiteralPath $startMenuLink -PathType Leaf)) {
        throw "The OpenScribe command-line shortcut was not created."
    }
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($startMenuLink)
    if (-not $shortcut.Arguments.Contains("Set-Alias openscribe") -or -not $shortcut.Arguments.Contains($installRoot)) {
        throw "The OpenScribe command-line shortcut does not configure the packaged CLI."
    }
    & (Join-Path $PSScriptRoot "test-windows-package.ps1") -BundleRoot $installRoot -WorkRoot $projectWork
    if ($LASTEXITCODE -ne 0) {
        throw "Installed package smoke test failed."
    }

    Install-OpenScribe
    $upgradeProcess = Start-Process -FilePath (Join-Path $installRoot "OpenScribe.exe") -ArgumentList "--smoke-test" -Wait -PassThru
    if ($upgradeProcess.ExitCode -ne 0) {
        throw "Upgrade smoke test failed with exit code $($upgradeProcess.ExitCode)."
    }

    $uninstaller = Join-Path $installRoot "unins000.exe"
    if (-not (Test-Path -LiteralPath $uninstaller -PathType Leaf)) {
        throw "Uninstaller is missing after installation."
    }
    $uninstallProcess = Start-Process -FilePath $uninstaller -ArgumentList @(
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART"
    ) -Wait -PassThru
    if ($uninstallProcess.ExitCode -ne 0) {
        throw "Uninstaller failed with exit code $($uninstallProcess.ExitCode)."
    }
    if (Test-Path -LiteralPath (Join-Path $installRoot "OpenScribe.exe")) {
        throw "OpenScribe.exe remained after uninstall."
    }
    if (Test-Path -LiteralPath $startMenuLink) {
        throw "The OpenScribe command-line shortcut remained after uninstall."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectWork "smoke-project\.openscribe\project.yaml"))) {
        throw "Uninstall removed the user's project."
    }
}
finally {
    foreach ($path in @($installRoot, $projectWork)) {
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Recurse -Force
        }
    }
}
