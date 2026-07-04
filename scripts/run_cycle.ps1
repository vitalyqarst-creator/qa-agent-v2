[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $RunnerArgs
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $RepoRoot "scripts\codex_review_cycle_runner.py"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project venv Python was not found at $Python. Run 'uv sync' from the repository root first."
}

& $Python $Runner @RunnerArgs
exit $LASTEXITCODE
