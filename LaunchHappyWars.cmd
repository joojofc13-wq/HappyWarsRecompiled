@echo off
setlocal
if not exist "%~dp0build\game\HappyWars.exe" (
  echo HappyWars.exe is missing. Follow docs\BUILDING.md to build it first.
  pause
  exit /b 1
)
if not exist "%~dp0private\game\Default.xex" (
  echo Game files are missing. Extract your package with scripts\extract.py first.
  pause
  exit /b 1
)
if not exist "%~dp0logs" mkdir "%~dp0logs"
start "" /D "%~dp0" pyw.exe "%~dp0scripts\playtest.py"
