@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo [error] python not on PATH. Install Python 3.10~3.12 first: https://www.python.org/downloads/
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
echo [setup] Installing Chromium for Playwright (PNG rendering)...
echo         첫 실행 시 ~150~250MB 다운로드. 이미 설치되어 있으면 건너뜁니다.
python -m playwright install chromium
if errorlevel 1 (
  echo.
  echo [warn] Playwright Chromium install failed. PNG 카드 추출이 안 될 수 있습니다.
  echo        수동 설치: .venv\Scripts\activate.bat ^&^& python -m playwright install chromium
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
