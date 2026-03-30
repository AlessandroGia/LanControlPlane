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

Write-Host "==> Copying agent and shared"
Remove-Item -Recurse -Force (Join-Path $InstallDir "agent") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $InstallDir "shared") -ErrorAction SilentlyContinue

Copy-Item -Recurse -Force $AgentDir (Join-Path $InstallDir "agent")
Copy-Item -Recurse -Force (Join-Path $RepoRoot "shared") (Join-Path $InstallDir "shared")

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
py -3 -m venv (Join-Path $InstallDir ".venv")

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
