@echo off
REM Build script for keep_to_joplin GUI executable for Windows using PyInstaller

setlocal

cd /d "%~dp0"

REM Check if .venv exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing/upgrading dependencies...
pip install --upgrade pyinstaller PyQt6 >nul 2>&1

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del /q *.spec 2>nul

REM Build the executable
echo Building standalone executable for Windows...
python -m PyInstaller ^
    --onefile ^
    --name keep_to_joplin ^
    --windowed ^
    --icon=NONE ^
    keep_to_joplin_gui.py

echo.
echo Build complete! Executable is at: dist\keep_to_joplin.exe
echo.
echo To test the GUI, run: dist\keep_to_joplin.exe

endlocal

