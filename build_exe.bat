@echo off
setlocal

title Build Executable

if not exist .venv\Scripts\python.exe (
    echo Virtual environment not found.
    echo Run setup_env.bat first.
    pause
    exit /b
)

echo.
echo =====================================
echo Cleaning old builds
echo =====================================

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
del /q *.spec 2>nul

echo.
echo =====================================
echo Building executable
echo =====================================

uv run --python .venv\Scripts\python.exe pyinstaller --onefile --console --icon=ALM.ico main.py

echo.
echo Build complete.
echo dist\main.exe
pause