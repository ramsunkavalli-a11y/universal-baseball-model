@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing.
  echo Run the project setup first, then try again.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "scripts\build_results_explorer.py"
if errorlevel 1 (
  echo.
  echo The viewer could not be created. See the message above.
  pause
  exit /b 1
)
start "" "reports\generated\results-explorer\index.html"
endlocal
