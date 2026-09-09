[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipInstaller,
    [switch]$KeepBuild,
    [string]$InnoCompiler
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repository = Split-Path -Parent $PSScriptRoot
$artifacts = Join-Path $repository "artifacts"
$temporaryBase = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
$packageBuild = Join-Path ([IO.Path]::GetTempPath()) ("openscribe-windows-package-" + [guid]::NewGuid().ToString("N"))
$pyInstallerDist = Join-Path $packageBuild "pyinstaller-dist"
$pyInstallerWork = Join-Path $packageBuild "pyinstaller-work"

function Remove-RepositoryItem([string]$Path) {
    $resolvedRepository = [IO.Path]::GetFullPath($repository).TrimEnd('\') + '\'
    $resolvedPath = [IO.Path]::GetFullPath($Path)
    if (-not $resolvedPath.StartsWith($resolvedRepository, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the repository: $resolvedPath"
    }
    if (Test-Path -LiteralPath $resolvedPath) {
        $item = Get-Item -LiteralPath $resolvedPath -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and ($item.LinkType -or $item.Target)) {
            throw "Refusing to recursively remove a repository reparse point: $resolvedPath"
        }
        Remove-Item -LiteralPath $resolvedPath -Recurse -Force
    }
}

function Remove-TemporaryItem([string]$Path) {
    $resolvedPath = [IO.Path]::GetFullPath($Path)
    if (-not $resolvedPath.StartsWith($temporaryBase, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the temporary directory: $resolvedPath"
    }
    if (Test-Path -LiteralPath $resolvedPath) {
        $item = Get-Item -LiteralPath $resolvedPath -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and ($item.LinkType -or $item.Target)) {
            throw "Refusing to recursively remove a temporary reparse point: $resolvedPath"
        }
        Remove-Item -LiteralPath $resolvedPath -Recurse -Force
    }
}

if (-not $IsWindows) {
    throw "Windows executable packages must be built on Windows."
}

if (-not $Version) {
    $projectMetadata = Join-Path $repository "pyproject.toml"
    $Version = python -c "import sys, tomllib; print(tomllib.load(open(sys.argv[1], 'rb'))['project']['version'])" $projectMetadata
    if ($LASTEXITCODE -ne 0 -or -not $Version) {
        throw "Could not read the package version from pyproject.toml."
    }
}

Push-Location $repository
try {
    Remove-RepositoryItem $artifacts
    New-Item -ItemType Directory -Path $pyInstallerDist, $pyInstallerWork, $artifacts -Force | Out-Null

    python -m PyInstaller --noconfirm --clean --distpath $pyInstallerDist --workpath (Join-Path $pyInstallerWork "desktop") packaging\openscribe-desktop.spec
    if ($LASTEXITCODE -ne 0) {
        throw "The desktop executable build failed."
    }
    python -m PyInstaller --noconfirm --clean --distpath $pyInstallerDist --workpath (Join-Path $pyInstallerWork "cli") packaging\openscribe-cli.spec
    if ($LASTEXITCODE -ne 0) {
        throw "The CLI executable build failed."
    }

    $portableName = "OpenScribe-Portable-$Version-x64"
    $portableRoot = Join-Path $packageBuild $portableName
    New-Item -ItemType Directory -Path $portableRoot -Force | Out-Null
    Copy-Item -Path (Join-Path $pyInstallerDist "OpenScribe\*") -Destination $portableRoot -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $pyInstallerDist "openscribe-cli.exe") -Destination $portableRoot -Force
    Copy-Item -LiteralPath (Join-Path $repository "packaging\PORTABLE-README.txt") -Destination $portableRoot -Force
    Copy-Item -LiteralPath (Join-Path $repository "LICENSE") -Destination (Join-Path $portableRoot "LICENSE.txt") -Force
    python scripts\collect-package-licenses.py --output (Join-Path $portableRoot "THIRD-PARTY-LICENSES.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Third-party license collection failed."
    }

    & (Join-Path $repository "scripts\test-windows-package.ps1") -BundleRoot $portableRoot
    if ($LASTEXITCODE -ne 0) {
        throw "The portable package smoke test failed."
    }

    $portableZip = Join-Path $artifacts "$portableName.zip"
    Compress-Archive -Path (Join-Path $portableRoot "*") -DestinationPath $portableZip -CompressionLevel Optimal

    if (-not $SkipInstaller) {
        if (-not $InnoCompiler) {
            $candidates = @(
                (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
                "C:\Program Files\Inno Setup 7\ISCC.exe",
                "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                "C:\Program Files\Inno Setup 6\ISCC.exe"
            ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
            $InnoCompiler = $candidates | Select-Object -First 1
        }
        if (-not $InnoCompiler -or -not (Test-Path -LiteralPath $InnoCompiler)) {
            throw "Inno Setup compiler was not found. Install Inno Setup or use -SkipInstaller."
        }
        & $InnoCompiler "/DAppVersion=$Version" "/DSourceDir=$portableRoot" "/DOutputDir=$artifacts" (Join-Path $repository "packaging\openscribe.iss")
        if ($LASTEXITCODE -ne 0) {
            throw "The Windows installer build failed."
        }
    }

    $checksumPath = Join-Path $artifacts "SHA256SUMS.txt"
    Get-ChildItem -LiteralPath $artifacts -File | Where-Object Name -ne "SHA256SUMS.txt" | Sort-Object Name | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $($_.Name)"
    } | Set-Content -LiteralPath $checksumPath -Encoding ascii

    Get-ChildItem -LiteralPath $artifacts -File | Select-Object Name, Length
}
finally {
    Pop-Location
    if ($KeepBuild) {
        Write-Output "Build workspace retained at $packageBuild"
    }
    else {
        Remove-TemporaryItem $packageBuild
    }
}
