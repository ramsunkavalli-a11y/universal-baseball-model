@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The local Python environment is missing.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" "scripts\materialize_prospect_hitter_comparables.py" --as-of-date 2026-09-08
if errorlevel 1 goto :build_error
".venv\Scripts\python.exe" "scripts\materialize_prospect_pitcher_comparables.py" --as-of-date 2026-09-08
if errorlevel 1 goto :build_error
".venv\Scripts\python.exe" "scripts\build_talent_value_explorer.py"
if errorlevel 1 goto :build_error
if /i "%~1"=="--build-only" (
  endlocal
  exit /b 0
)
set "RESULT_PATH=%~dp0reports\generated\talent-value-explorer\index.html"
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
echo Open this file in a browser:
echo %RESULT_PATH%
explorer.exe /select,"%RESULT_PATH%"
pause
endlocal
exit /b 0

:build_error
echo.
echo The prospect talent foundation viewer could not be created.
pause
endlocal
exit /b 1
