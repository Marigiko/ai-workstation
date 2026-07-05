# Deploy script for AI Workstation Platform (PowerShell)
param(
    [Parameter(Position=0)]
    [ValidateSet('deploy', 'stop', 'restart', 'status', 'logs')]
    [string]$Action = 'deploy',
    
    [Parameter(Position=1)]
    [string]$Service
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed"
        exit 1
    }
    
    Write-Info "Prerequisites check passed"
}

function Import-Environment {
    $envFile = Join-Path $ScriptDir "..\compose\.env"
    if (Test-Path $envFile) {
        Write-Info "Loading environment from .env file"
        Get-Content $envFile | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '^\s*[^=]+=' } | ForEach-Object {
            $parts = $_ -split '=', 2
            if ($parts.Length -eq 2) {
                $name = $parts[0].Trim()
                $value = $parts[1].Trim()
                Set-Item -Path "env:$name" -Value $value
            }
        }
    } else {
        Write-Warn "No .env file found, using defaults"
    }
}

function Build-Images {
    Write-Info "Building Docker images..."
    Push-Location $ProjectRoot
    
    $composeFile = Join-Path $ScriptDir "..\compose\docker-compose.prod.yml"
    docker compose -f $composeFile build
    
    Pop-Location
    Write-Info "Images built successfully"
}

function Start-Services {
    Write-Info "Starting services..."
    Push-Location $ProjectRoot
    
    $composeFile = Join-Path $ScriptDir "..\compose\docker-compose.prod.yml"
    docker compose -f $composeFile up -d
    
    Pop-Location
    Write-Info "Services started successfully"
}

function Wait-ForServices {
    Write-Info "Waiting for services to be healthy..."
    
    $port = if ($env:GATEWAY_PORT) { $env:GATEWAY_PORT } else { "8000" }
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Info "Gateway is healthy"
                return
            }
        } catch {
            # Ignore errors
        }
        
        Write-Warn "Attempt $attempt/$maxAttempts`: Gateway not ready yet..."
        Start-Sleep -Seconds 2
        $attempt++
    }
    
    Write-Error "Gateway failed to become healthy"
    exit 1
}

function Invoke-Migrations {
    Write-Info "Running database migrations..."
    Push-Location $ProjectRoot
    
    $composeFile = Join-Path $ScriptDir "..\compose\docker-compose.prod.yml"
    docker compose -f $composeFile exec gateway alembic upgrade head
    
    Pop-Location
    Write-Info "Migrations completed"
}

function Deploy {
    Write-Info "Starting deployment..."
    
    Test-Prerequisites
    Import-Environment
    Build-Images
    Start-Services
    Wait-ForServices
    Invoke-Migrations
    
    $port = if ($env:GATEWAY_PORT) { $env:GATEWAY_PORT } else { "8000" }
    $grafanaPort = if ($env:GRAFANA_PORT) { $env:GRAFANA_PORT } else { "3000" }
    
    Write-Info "Deployment completed successfully!"
    Write-Info "Gateway: http://localhost:$port"
    Write-Info "API Docs: http://localhost:$port/docs"
    Write-Info "Grafana: http://localhost:$grafanaPort"
}

function Stop-Services {
    Write-Info "Stopping services..."
    Push-Location $ProjectRoot
    
    $composeFile = Join-Path $ScriptDir "..\compose\docker-compose.prod.yml"
    docker compose -f $composeFile down
    
    Pop-Location
    Write-Info "Services stopped"
}

function Show-Status {
    Push-Location $ProjectRoot
    
    $composeFile = Join-Path $ScriptDir "..\compose\docker-compose.prod.yml"
    docker compose -f $composeFile ps
    
    Pop-Location
}

function Show-Logs {
    Push-Location $ProjectRoot
    
    $composeFile = Join-Path $ScriptDir "..\compose\docker-compose.prod.yml"
    if ($Service) {
        docker compose -f $composeFile logs -f $Service
    } else {
        docker compose -f $composeFile logs -f
    }
    
    Pop-Location
}

# Main
switch ($Action) {
    'deploy' { Deploy }
    'stop' { Stop-Services }
    'restart' { 
        Stop-Services
        Deploy
    }
    'status' { Show-Status }
    'logs' { Show-Logs }
    default {
        Write-Host "Usage: $PSCommandPath {deploy|stop|restart|status|logs [service]}"
        exit 1
    }
}
