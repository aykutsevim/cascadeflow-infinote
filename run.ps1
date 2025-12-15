# PowerShell script for common commands
# Alternative to Makefile for Windows users

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Available commands:" -ForegroundColor Cyan
    Write-Host "  .\run.ps1 build            - Build all Docker images"
    Write-Host "  .\run.ps1 up               - Start all services"
    Write-Host "  .\run.ps1 start            - Start all services (alias)"
    Write-Host "  .\run.ps1 down             - Stop all services"
    Write-Host "  .\run.ps1 stop             - Stop all services (alias)"
    Write-Host "  .\run.ps1 restart          - Restart all services"
    Write-Host "  .\run.ps1 logs             - View logs from all services"
    Write-Host "  .\run.ps1 logs-api         - View API service logs"
    Write-Host "  .\run.ps1 logs-worker      - View worker service logs"
    Write-Host "  .\run.ps1 shell            - Open Django shell"
    Write-Host "  .\run.ps1 bash             - Open bash in API container"
    Write-Host "  .\run.ps1 migrate          - Run database migrations"
    Write-Host "  .\run.ps1 makemigrations   - Create new migrations"
    Write-Host "  .\run.ps1 createsuperuser  - Create Django superuser"
    Write-Host "  .\run.ps1 test             - Run tests"
    Write-Host "  .\run.ps1 ps               - Show running containers"
    Write-Host "  .\run.ps1 clean            - Remove containers and volumes"
    Write-Host "  .\run.ps1 dev-setup        - Setup development environment"
}

function Build {
    docker-compose build
}

function Start-Services {
    docker-compose up -d
    Write-Host "`nServices are starting..." -ForegroundColor Green
    Write-Host "API: http://localhost:8000" -ForegroundColor Yellow
    Write-Host "MinIO Console: http://localhost:9001" -ForegroundColor Yellow
    Write-Host "Flower: http://localhost:5555" -ForegroundColor Yellow
}

function Stop-Services {
    docker-compose down
}

function Restart-Services {
    docker-compose restart
}

function Show-Logs {
    docker-compose logs -f
}

function Show-ApiLogs {
    docker-compose logs -f api
}

function Show-WorkerLogs {
    docker-compose logs -f worker
}

function Open-Shell {
    docker-compose exec api python manage.py shell
}

function Open-Bash {
    docker-compose exec api bash
}

function Run-Migrate {
    docker-compose exec api python manage.py migrate
}

function Make-Migrations {
    docker-compose exec api python manage.py makemigrations
}

function Create-SuperUser {
    docker-compose exec api python manage.py createsuperuser
}

function Run-Tests {
    docker-compose exec api python manage.py test
}

function Show-Ps {
    docker-compose ps
}

function Clean {
    docker-compose down -v
    Write-Host "Containers and volumes removed" -ForegroundColor Green
}

function Dev-Setup {
    Write-Host "Setting up development environment..." -ForegroundColor Cyan
    docker-compose build
    docker-compose up -d
    Start-Sleep -Seconds 10
    docker-compose exec api python manage.py migrate
    Write-Host "`nDevelopment environment ready!" -ForegroundColor Green
    Write-Host "Run '.\run.ps1 createsuperuser' to create an admin user" -ForegroundColor Yellow
}

# Execute command
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "build" { Build }
    "up" { Start-Services }
    "start" { Start-Services }
    "down" { Stop-Services }
    "stop" { Stop-Services }
    "restart" { Restart-Services }
    "logs" { Show-Logs }
    "logs-api" { Show-ApiLogs }
    "logs-worker" { Show-WorkerLogs }
    "shell" { Open-Shell }
    "bash" { Open-Bash }
    "migrate" { Run-Migrate }
    "makemigrations" { Make-Migrations }
    "createsuperuser" { Create-SuperUser }
    "test" { Run-Tests }
    "ps" { Show-Ps }
    "clean" { Clean }
    "dev-setup" { Dev-Setup }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
