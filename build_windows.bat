@echo off
title SLASH Browser - Native Windows Compiler
echo ==========================================================
echo       🚀 SLASH Browser - Native Windows Compiler & Installer
echo ==========================================================
echo.

:: 1. Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is required but not found in your Windows PATH.
    echo Please download and install Python 3.10+ from https://www.python.org/
    echo Make sure to check the option "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: 2. Setup Virtual Environment
echo 📦 Creating local sandboxed Python environment (win_venv)...
if not exist win_venv (
    python -m venv win_venv
    if %errorlevel% neq 0 (
        echo ❌ Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Upgrade pip and install PyQt6, PyQt6-WebEngine, and PyInstaller
echo ⚡ Installing PyQt6 and PyInstaller dependencies inside sandbox...
call win_venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install PyQt6 PyQt6-WebEngine pyinstaller
if %errorlevel% neq 0 (
    echo ❌ Error: Failed to install python packages.
    pause
    exit /b 1
)

:: 4. Run PyInstaller Compilation
echo 🔨 Compiling browser.py into standalone executable...
pyinstaller --noconsole --onefile --add-data "home.html;." --name="SLASH" browser.py
if %errorlevel% neq 0 (
    echo ❌ Error: PyInstaller compilation failed.
    pause
    exit /b 1
)

:: 5. Create Desktop Shortcut using PowerShell
echo 🖥️  Registering Windows Desktop Shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'SLASH.lnk')); $Shortcut.TargetPath = '%CD%\dist\SLASH.exe'; $Shortcut.WorkingDirectory = '%CD%\dist'; $Shortcut.Description = 'Secure, Localized Web Browser'; $Shortcut.Save()"

echo.
echo ==========================================================
echo 🎉 SUCCESS: SLASH has been compiled successfully!
echo ==========================================================
echo.
echo Standalone Executable: %CD%\dist\SLASH.exe
echo.
echo A Windows Desktop shortcut 'SLASH' has been created for you.
echo You can now close this window.
echo ==========================================================
pause
