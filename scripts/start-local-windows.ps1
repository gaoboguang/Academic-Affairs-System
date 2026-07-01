$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$HostName = "127.0.0.1"
$LogDir = Join-Path $RootDir "data\logs\local-services"
$NoOpen = $args -contains "--no-open"

$Services = @(
  @{
    Name = "backend"
    Label = "backend"
    Port = 8000
    HealthPath = "/api/system/health"
    Args = "run backend:dev"
    Url = "http://127.0.0.1:8000"
  },
  @{
    Name = "frontend"
    Label = "frontend"
    Port = 5173
    HealthPath = "/"
    Args = "run frontend:dev"
    Url = "http://127.0.0.1:5173"
  }
)

function Get-ServiceUrl($Service) {
  return "http://$($HostName):$($Service.Port)$($Service.HealthPath)"
}

function Get-LogPath($Service) {
  return Join-Path $LogDir "$($Service.Name).log"
}

function Get-PidPath($Service) {
  return Join-Path $LogDir "$($Service.Name).pid.json"
}

function Test-HttpHealth($Service) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri (Get-ServiceUrl $Service) -TimeoutSec 2
    return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
  } catch {
    return $false
  }
}

function Test-PortAvailable($Service) {
  $listener = $null
  try {
    $address = [System.Net.IPAddress]::Parse($HostName)
    $listener = [System.Net.Sockets.TcpListener]::new($address, [int]$Service.Port)
    $listener.Start()
    return $true
  } catch {
    return $false
  } finally {
    if ($listener) {
      $listener.Stop()
    }
  }
}

function Test-PidRunning($PidValue) {
  if (-not $PidValue) {
    return $false
  }
  try {
    $null = Get-Process -Id ([int]$PidValue) -ErrorAction Stop
    return $true
  } catch {
    return $false
  }
}

function Get-SavedPid($Service) {
  $pidPath = Get-PidPath $Service
  if (-not (Test-Path -LiteralPath $pidPath)) {
    return $null
  }
  try {
    $data = Get-Content -LiteralPath $pidPath -Encoding UTF8 -Raw | ConvertFrom-Json
    return [int]$data.pid
  } catch {
    return $null
  }
}

function Remove-StalePid($Service) {
  $pidPath = Get-PidPath $Service
  if (Test-Path -LiteralPath $pidPath) {
    Remove-Item -LiteralPath $pidPath -Force
  }
}

function Start-LocalService($Service) {
  $logPath = Get-LogPath $Service
  Add-Content -LiteralPath $logPath -Encoding UTF8 -Value ""
  Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "===== $((Get-Date).ToUniversalTime().ToString("o")) start $($Service.Name) via windows launcher ====="

  $innerCommand = "cd /d `"$RootDir`" && npm.cmd $($Service.Args) >> `"$logPath`" 2>&1"
  $argumentList = "/d /s /c `"$innerCommand`""
  $process = Start-Process -FilePath $env:ComSpec -ArgumentList $argumentList -WorkingDirectory $RootDir -WindowStyle Hidden -PassThru

  $pidInfo = [ordered]@{
    pid = $process.Id
    command = "$env:ComSpec $argumentList"
    url = $Service.Url
    log = $logPath
    startedAt = (Get-Date).ToUniversalTime().ToString("o")
  }
  $pidInfo | ConvertTo-Json | Set-Content -LiteralPath (Get-PidPath $Service) -Encoding ASCII
  return $process.Id
}

function Wait-ServiceReady($Service, $TimeoutSeconds = 45) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpHealth $Service) {
      return $true
    }
    Start-Sleep -Seconds 1
  }
  return $false
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Set-Location $RootDir

Write-Host "Checking local services..."
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend: http://127.0.0.1:8000"
Write-Host "Log directory: $LogDir"
Write-Host ""

$started = @()
foreach ($service in $Services) {
  if (Test-HttpHealth $service) {
    Write-Host "[$($service.Label)] already running: $($service.Url)"
    continue
  }

  $savedPid = Get-SavedPid $service
  if ($savedPid -and -not (Test-PidRunning $savedPid)) {
    Remove-StalePid $service
    Write-Host "[$($service.Label)] removed stale pid record: $savedPid"
  }

  if (-not (Test-PortAvailable $service)) {
    throw "[$($service.Label)] Port $($HostName):$($service.Port) is occupied, but health check failed. Close the process using that port first."
  }

  $pidValue = Start-LocalService $service
  $started += $service
  Write-Host "[$($service.Label)] started in background, pid=$pidValue, log=$(Get-LogPath $service)"
}

foreach ($service in $started) {
  if (-not (Wait-ServiceReady $service)) {
    $logPath = Get-LogPath $service
    Write-Error "[$($service.Label)] health check failed after startup. Check log: $logPath"
    if (Test-Path -LiteralPath $logPath) {
      Get-Content -LiteralPath $logPath -Encoding UTF8 -Tail 60
    }
    exit 1
  }
}

Write-Host ""
Write-Host "Local edu tool is ready."
Write-Host "Browser URL: http://127.0.0.1:5173"
Write-Host "Logs:"
foreach ($service in $Services) {
  Write-Host "- $($service.Label): $(Get-LogPath $service)"
}

if (-not $NoOpen) {
  Start-Process "http://127.0.0.1:5173"
}
