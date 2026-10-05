param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string]$FunctionInfos,

    [string]$OutputDir = "coverage_reports",
    [string]$IncludedModules,
    [int]$Pid = 8123,
    [string]$AgentScript
)

$ErrorActionPreference = "Stop"
$ToolPath = Join-Path $PSScriptRoot "manual-test-coverage.exe"

$ArgsList = @(
    "--target", $Target,
    "--function_infos", $FunctionInfos,
    "--output_dir", $OutputDir,
    "--pid", $Pid
)

if ($IncludedModules) {
    $ArgsList += @("--included_modules", $IncludedModules)
}

if ($AgentScript) {
    $ArgsList += @("--agent-script", $AgentScript)
}

& $ToolPath @ArgsList
exit $LASTEXITCODE
