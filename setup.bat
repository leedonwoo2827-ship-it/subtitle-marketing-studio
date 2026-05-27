@echo off
chcp 65001 >nul 2>nul
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [error] python not on PATH. Install Python 3.10~3.12: https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [setup] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [error] Failed to create venv.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 (
  echo [error] pip upgrade failed.
  pause
  exit /b 1
)

pip install -e .
if errorlevel 1 (
  echo.
  echo [error] Dependency install failed.
  echo.
  pause
  exit /b 1
)

echo.
echo [setup] Installing Chromium for Playwright PNG rendering...
echo         First time: ~150-250MB download. Skipped if already installed.
python -m playwright install chromium
if errorlevel 1 (
  echo.
  echo [warn] Playwright Chromium install failed.
  echo        Manual install: .venv\Scripts\activate.bat ^&^& python -m playwright install chromium
  echo        Without this, PNG card extraction will not work.
  echo.
)

if not exist ".env" (
  copy .env.example .env >nul
  echo [setup] Created .env from .env.example
)

echo.
echo ============================================
echo  Setup complete. Double-click run.bat to start.
echo ============================================
echo.
pause
