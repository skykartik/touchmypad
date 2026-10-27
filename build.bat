@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Building touchmypad.exe
echo.

set "MISSING="
for %%F in (touchmypad.py touchmypad_app.py ui.html) do (
  if not exist "%%F" set "MISSING=!MISSING! %%F"
)
if defined MISSING (
  echo  These files are missing from this folder:
  echo    !MISSING!
  echo.
  echo  Copy them next to build.bat and run it again.
  echo.
  pause
  exit /b 1
)

set "ICONARGS="
if exist touchmypad.ico (
  set ICONARGS=--icon touchmypad.ico --add-data "touchmypad.ico;."
) else (
  echo  Note: touchmypad.ico not found, so the exe will use the default icon.
)

echo  Building touchmypad.exe ... this takes a few minutes.
echo.
python -m pip install --upgrade pywebview pystray pillow pyinstaller
python -m PyInstaller --clean --noconfirm --onefile --windowed --name touchmypad !ICONARGS! --add-data "ui.html;." --collect-all webview --hidden-import pystray._win32 touchmypad_app.py
echo.
if exist dist\touchmypad.exe (
  echo  Done! Your app is here:  dist\touchmypad.exe
) else (
  echo  Something went wrong. Check the messages above.
)
echo.
pause
