@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv" (
  echo [error] .venv not found. Run setup.bat first.
  exit /b 1
)
call .venv\Scripts\activate.bat
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set "%%a=%%b"
  )
)
if "%STREAMLIT_SERVER_PORT%"=="" set STREAMLIT_SERVER_PORT=8620
streamlit run app.py --server.port %STREAMLIT_SERVER_PORT% --server.headless true
