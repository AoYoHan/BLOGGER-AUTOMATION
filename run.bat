@echo off
setlocal enabledelayedexpansion

:: ==========================================
:: Blogger Automation Runner (Enhanced)
:: ==========================================

:: 1. 가상환경 확인 및 활성화
if exist "venv\Scripts\python.exe" (
    set PYTHON_EXE=venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
    echo [WARNING] venv not found. Using system python...
)

:MENU
cls
echo ==========================================
echo    AI Blogger Automation System
echo ==========================================
echo  1. [Generate] Create Drafts (Pending)
echo  2. [Publish] Post Approved Drafts
echo  3. [Status] Check Current Status
echo  4. [Auto] Run Generate + Publish (Once)
echo  5. [Loop] Auto-loop every 1 hour
echo  6. [Init] Initialize Google Sheets
echo  0. Exit
echo ==========================================
set /p choice="Choose an option (0-6): "

if "%choice%"=="1" goto GENERATE
if "%choice%"=="2" goto PUBLISH
if "%choice%"=="3" goto STATUS
if "%choice%"=="4" goto AUTO
if "%choice%"=="5" goto LOOP
if "%choice%"=="6" goto INIT
if "%choice%"=="0" exit
goto MENU

:GENERATE
echo.
echo [RUNNING] Generating drafts...
%PYTHON_EXE% main.py generate
pause
goto MENU

:PUBLISH
echo.
echo [RUNNING] Publishing approved...
%PYTHON_EXE% main.py publish
pause
goto MENU

:STATUS
echo.
echo [RUNNING] Fetching status...
%PYTHON_EXE% main.py status
pause
goto MENU

:AUTO
echo.
echo [RUNNING] Running Generate followed by Publish...
%PYTHON_EXE% main.py auto
pause
goto MENU

:LOOP
echo.
echo [RUNNING] Auto-loop mode (Press Ctrl+C to stop)
%PYTHON_EXE% main.py loop
pause
goto MENU

:INIT
echo.
echo [WARNING] This will initialize Google Sheets headers.
echo Proceed? (Y/N)
set /p confirm="> "
if /i "%confirm%"=="Y" (
    %PYTHON_EXE% main.py init
)
pause
goto MENU
