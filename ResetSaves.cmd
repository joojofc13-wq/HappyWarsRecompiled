@echo off
if exist "%~dp0scripts\reset_saves.ps1" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\reset_saves.ps1" %*
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset_saves.ps1" %*
)
if errorlevel 1 pause
