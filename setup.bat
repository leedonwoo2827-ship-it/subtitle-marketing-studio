@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul || (echo [error] python not on PATH & exit /b 1)
if not exist ".venv" (
  python -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -e .
if not exist ".env" (
  copy .env.example .env >nul
  echo Created .env from .env.example
)
echo.
echo Setup complete. Run run.bat to start.
