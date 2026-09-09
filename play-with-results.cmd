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
if /i "%~1"=="--build-only" (
  endlocal
  exit /b 0
)
set "RESULT_PATH=%~dp0reports\generated\results-explorer\index.html"
set "EDGE_PATH=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if exist "%EDGE_PATH%" (
  start "" "%EDGE_PATH%" "%RESULT_PATH%"
  endlocal
  exit /b 0
)
if exist "%CHROME_PATH%" (
  start "" "%CHROME_PATH%" "%RESULT_PATH%"
  endlocal
  exit /b 0
)
echo.
echo The results were built, but Edge or Chrome was not found.
echo Open this file in your browser:
echo %RESULT_PATH%
explorer.exe /select,"%RESULT_PATH%"
pause
endlocal
