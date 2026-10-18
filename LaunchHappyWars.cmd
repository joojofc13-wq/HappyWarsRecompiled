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
start "" /D "%~dp0build\game" "%~dp0build\game\HappyWars.exe" "--game_data_root=%~dp0private\game" "--user_data_root=%~dp0private\smoke-user" "--cache_root=%~dp0private\smoke-cache" "--log_file=%~dp0logs\runtime-launcher.log" --window_width=1280 --window_height=720 --mnk_mode=true
