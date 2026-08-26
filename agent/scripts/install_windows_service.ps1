$ErrorActionPreference = "Stop"

$CurrentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $CurrentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this installer from an elevated PowerShell or Command Prompt (Run as administrator)."
}

function Assert-NativeSuccess {
    param([Parameter(Mandatory = $true)][string]$Action)

    if ($LASTEXITCODE -ne 0) {
        throw "$Action failed with exit code $LASTEXITCODE."
    }
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentDir = Split-Path -Parent $ScriptDir
$RepoRoot = Split-Path -Parent $AgentDir

$InstallDir = "C:\Program Files\LanControlPlaneAgent"
$LogsDir = "C:\ProgramData\LanControlPlaneAgent\logs"
$ServiceName = "LanControlPlaneAgent"
$WinSWExe = Join-Path $InstallDir "LanControlPlaneAgent.exe"
$WinSWXmlSource = Join-Path $AgentDir "packaging\windows\LanControlPlaneAgent.xml"
$WinSWXmlDest = Join-Path $InstallDir "LanControlPlaneAgent.xml"

Write-Host "==> ScriptDir: $ScriptDir"
Write-Host "==> AgentDir:  $AgentDir"
Write-Host "==> RepoRoot:  $RepoRoot"

& py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"
Assert-NativeSuccess "Python 3.12 validation"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "==> Stopping previous service, if installed"
$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($null -ne $ExistingService) {
    if ($ExistingService.Status -ne [System.ServiceProcess.ServiceControllerStatus]::Stopped) {
        Stop-Service -Name $ServiceName -Force
        $ExistingService.WaitForStatus(
            [System.ServiceProcess.ServiceControllerStatus]::Stopped,
            [TimeSpan]::FromSeconds(30)
        )
    }

    & sc.exe delete $ServiceName | Out-Host
    Assert-NativeSuccess "Removing the previous Windows service registration"

    $DeleteDeadline = [DateTime]::UtcNow.AddSeconds(30)
    while ((Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) -and [DateTime]::UtcNow -lt $DeleteDeadline) {
        Start-Sleep -Milliseconds 500
    }
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        throw "The previous Windows service is still marked for deletion. Close service-management windows and retry."
    }
}

Write-Host "==> Copying agent and shared"
$ValidatedInstallDir = [IO.Path]::GetFullPath($InstallDir).TrimEnd([IO.Path]::DirectorySeparatorChar)
$SourceTargets = @(
    (Join-Path $ValidatedInstallDir "agent"),
    (Join-Path $ValidatedInstallDir "shared")
)
foreach ($Target in $SourceTargets) {
    $ValidatedTarget = [IO.Path]::GetFullPath($Target)
    if (-not $ValidatedTarget.StartsWith("$ValidatedInstallDir\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove an unexpected path: $ValidatedTarget"
    }
    if (Test-Path -LiteralPath $ValidatedTarget) {
        Remove-Item -LiteralPath $ValidatedTarget -Recurse -Force
    }
    if (Test-Path -LiteralPath $ValidatedTarget) {
        throw "Unable to remove the previous installation directory: $ValidatedTarget"
    }
}

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
$InstalledEnv = Join-Path $InstallDir "agent.env"
$LocalEnv = Join-Path $AgentDir ".env"
if (Test-Path -LiteralPath $LocalEnv) {
    Copy-Item -LiteralPath $LocalEnv -Destination $InstalledEnv -Force
}
elseif (-not (Test-Path -LiteralPath $InstalledEnv)) {
    throw "Missing agent\.env. Create it from agent\.env.example first."
}
else {
    Write-Host "==> Keeping existing installed agent.env"
}

Write-Host "==> Creating virtual environment"
& py -3.12 -m venv (Join-Path $InstallDir ".venv")
Assert-NativeSuccess "Creating the bootstrap virtual environment"

Write-Host "==> Installing uv"
& (Join-Path $InstallDir ".venv\Scripts\pip.exe") install --no-cache-dir uv
Assert-NativeSuccess "Installing uv"

Write-Host "==> Installing agent dependencies"
Push-Location $InstalledAgentDir
try {
    & (Join-Path $InstallDir ".venv\Scripts\uv.exe") sync --frozen --no-dev
    Assert-NativeSuccess "Synchronizing agent dependencies"
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $WinSWExe)) {
    Write-Host "==> Downloading WinSW"
    Invoke-WebRequest `
      -Uri "https://github.com/winsw/winsw/releases/latest/download/WinSW-x64.exe" `
      -OutFile $WinSWExe
}
else {
    Write-Host "==> Reusing installed WinSW executable"
}

Write-Host "==> Installing WinSW XML"
Copy-Item -Force $WinSWXmlSource $WinSWXmlDest

Write-Host "==> Installing Windows service"
& $WinSWExe install
Assert-NativeSuccess "Installing the Windows service"

Write-Host "==> Starting Windows service"
& $WinSWExe start
Assert-NativeSuccess "Starting the Windows service"

Write-Host "==> Done"
