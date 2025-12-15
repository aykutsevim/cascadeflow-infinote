@echo off
REM Windows batch script for common commands
REM Alternative to Makefile for Windows users

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="build" goto build
if "%1"=="up" goto up
if "%1"=="start" goto start
if "%1"=="down" goto down
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="logs-api" goto logs-api
if "%1"=="logs-worker" goto logs-worker
if "%1"=="shell" goto shell
if "%1"=="bash" goto bash
if "%1"=="migrate" goto migrate
if "%1"=="makemigrations" goto makemigrations
if "%1"=="createsuperuser" goto createsuperuser
if "%1"=="test" goto test
if "%1"=="ps" goto ps
if "%1"=="clean" goto clean
if "%1"=="dev-setup" goto dev-setup

:help
echo Available commands:
echo   run.bat build            - Build all Docker images
echo   run.bat up               - Start all services
echo   run.bat start            - Start all services (alias)
echo   run.bat down             - Stop all services
echo   run.bat stop             - Stop all services (alias)
echo   run.bat restart          - Restart all services
echo   run.bat logs             - View logs from all services
echo   run.bat logs-api         - View API service logs
echo   run.bat logs-worker      - View worker service logs
echo   run.bat shell            - Open Django shell
echo   run.bat bash             - Open bash in API container
echo   run.bat migrate          - Run database migrations
echo   run.bat makemigrations   - Create new migrations
echo   run.bat createsuperuser  - Create Django superuser
echo   run.bat test             - Run tests
echo   run.bat ps               - Show running containers
echo   run.bat clean            - Remove containers and volumes
echo   run.bat dev-setup        - Setup development environment
goto end

:build
docker-compose build
goto end

:up
docker-compose up -d
echo Services are starting...
echo API: http://localhost:8000
echo MinIO Console: http://localhost:9001
echo Flower: http://localhost:5555
goto end

:start
docker-compose up -d
echo Services are starting...
echo API: http://localhost:8000
echo MinIO Console: http://localhost:9001
echo Flower: http://localhost:5555
goto end

:down
docker-compose down
goto end

:stop
docker-compose down
goto end

:restart
docker-compose restart
goto end

:logs
docker-compose logs -f
goto end

:logs-api
docker-compose logs -f api
goto end

:logs-worker
docker-compose logs -f worker
goto end

:shell
docker-compose exec api python manage.py shell
goto end

:bash
docker-compose exec api bash
goto end

:migrate
docker-compose exec api python manage.py migrate
goto end

:makemigrations
docker-compose exec api python manage.py makemigrations
goto end

:createsuperuser
docker-compose exec api python manage.py createsuperuser
goto end

:test
docker-compose exec api python manage.py test
goto end

:ps
docker-compose ps
goto end

:clean
docker-compose down -v
echo Containers and volumes removed
goto end

:dev-setup
echo Setting up development environment...
docker-compose build
docker-compose up -d
timeout /t 10 /nobreak > nul
docker-compose exec api python manage.py migrate
echo.
echo Development environment ready!
echo Run 'run.bat createsuperuser' to create an admin user
goto end

:end
