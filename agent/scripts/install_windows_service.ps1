$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentDir = Split-Path -Parent $ScriptDir
$RepoRoot = Split-Path -Parent $AgentDir

$InstallDir = "C:\Program Files\LanControlPlaneAgent"
$LogsDir = "C:\ProgramData\LanControlPlaneAgent\logs"
$WinSWExe = Join-Path $InstallDir "LanControlPlaneAgent.exe"
$WinSWXmlSource = Join-Path $AgentDir "packaging\windows\LanControlPlaneAgent.xml"
$WinSWXmlDest = Join-Path $InstallDir "LanControlPlaneAgent.xml"

Write-Host "==> ScriptDir: $ScriptDir"
Write-Host "==> AgentDir:  $AgentDir"
Write-Host "==> RepoRoot:  $RepoRoot"

& py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 or newer is required."
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "==> Copying agent and shared"
Remove-Item -Recurse -Force (Join-Path $InstallDir "agent") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $InstallDir "shared") -ErrorAction SilentlyContinue

$InstalledAgentDir = Join-Path $InstallDir "agent"
$InstalledSharedDir = Join-Path $InstallDir "shared"
New-Item -ItemType Directory -Force -Path $InstalledAgentDir, $InstalledSharedDir | Out-Null
Copy-Item -Force (Join-Path $AgentDir "pyproject.toml") $InstalledAgentDir
Copy-Item -Force (Join-Path $AgentDir "uv.lock") $InstalledAgentDir
Copy-Item -Recurse -Force (Join-Path $AgentDir "src") (Join-Path $InstalledAgentDir "src")
Copy-Item -Force (Join-Path $RepoRoot "shared\pyproject.toml") $InstalledSharedDir
Copy-Item -Recurse -Force (Join-Path $RepoRoot "shared\src") (Join-Path $InstalledSharedDir "src")

$LogsDir = "C:\ProgramData\LanControlPlaneAgent\logs"

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

Write-Host "==> Preparing env file"
if (-not (Test-Path (Join-Path $InstallDir "agent.env"))) {
    $LocalEnv = Join-Path $AgentDir ".env"
    if (Test-Path $LocalEnv) {
        Copy-Item -Force $LocalEnv (Join-Path $InstallDir "agent.env")
    }
    else {
        throw "Missing agent\.env. Create it from agent\.env.example first."
    }
}

Write-Host "==> Creating virtual environment"
py -3.12 -m venv (Join-Path $InstallDir ".venv")

Write-Host "==> Installing uv"
& (Join-Path $InstallDir ".venv\Scripts\pip.exe") install --no-cache-dir uv

Write-Host "==> Installing agent dependencies"
Push-Location (Join-Path $InstallDir "agent")
& (Join-Path $InstallDir ".venv\Scripts\uv.exe") sync --frozen --no-dev
Pop-Location

Write-Host "==> Downloading WinSW"
Invoke-WebRequest `
  -Uri "https://github.com/winsw/winsw/releases/latest/download/WinSW-x64.exe" `
  -OutFile $WinSWExe

Write-Host "==> Installing WinSW XML"
Copy-Item -Force $WinSWXmlSource $WinSWXmlDest

Write-Host "==> Installing Windows service"
& $WinSWExe install

Write-Host "==> Starting Windows service"
& $WinSWExe start

Write-Host "==> Done"
