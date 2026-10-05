param(
    [ValidateSet("Windows")]
    [string]$Platform = "Windows"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SymbolExtractorBuildDir = Join-Path $ProjectRoot "build\symbol-extractor"
$SymbolExtractorInstallDir = Join-Path $SymbolExtractorBuildDir "install"

Push-Location $ProjectRoot
try {
    cmake -S tools/symbol-extractor `
        -B $SymbolExtractorBuildDir `
        -DCMAKE_BUILD_TYPE=Release `
        -DCMAKE_INSTALL_PREFIX=$SymbolExtractorInstallDir
    cmake --build $SymbolExtractorBuildDir --config Release
    cmake --install $SymbolExtractorBuildDir --config Release

    poetry run python -m pip show pyinstaller *> $null
    if ($LASTEXITCODE -ne 0) {
        poetry run python -m pip install pyinstaller
    }

    poetry run pyinstaller packaging/manual-test-coverage.spec --clean --noconfirm

    Copy-Item packaging/windows/run-coverage.ps1 dist/manual-test-coverage/ -Force
    Copy-Item packaging/README.txt dist/manual-test-coverage/ -Force
    New-Item -ItemType Directory -Path dist/manual-test-coverage/tools -Force *> $null
    Copy-Item `
        (Join-Path $SymbolExtractorInstallDir "tools\symbol-extractor") `
        dist/manual-test-coverage/tools/ `
        -Recurse `
        -Force

    Write-Host "Package created at dist/manual-test-coverage"
}
finally {
    Pop-Location
}
