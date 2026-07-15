@echo off
title SLASH Browser - Native Windows Compiler
echo ==========================================================
echo       🚀 SLASH Browser - Native Windows Compiler & Installer
echo ==========================================================
echo.

:: 1. Check for Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Python is not detected on your Windows system.
    echo 📥 Downloading official Python 3.11.9 (64-bit) installer...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe', 'python_installer.exe')"
    if not exist python_installer.exe (
        echo ❌ Error: Failed to download Python installer automatically.
        echo Please ensure you are connected to the Internet, or download Python manually from:
        echo https://www.python.org/
        pause
        exit /b 1
    )
    echo ⚙️ Installing Python silently (User-level, with pip, added to PATH)...
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_doc=0 Include_pip=1
    
    :: Clean up the installer file
    del python_installer.exe
    
    :: Update PATH for the current CMD session to point to the newly installed Python
    set "PATH=%LocalAppData%\Programs\Python\Python311;%LocalAppData%\Programs\Python\Python311\Scripts;%PATH%"
    
    :: Double check if Python works now
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Error: Python silent installation completed but Python is still not found in PATH.
        echo Please restart this terminal or install Python manually from:
        echo https://www.python.org/
        pause
        exit /b 1
    )
    echo ✅ Python installed and configured successfully!
) else (
    echo ✅ Python is already installed on your system.
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
