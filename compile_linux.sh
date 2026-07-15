#!/bin/bash
set -e

echo "=========================================================="
echo "      🚀 SLASH Browser - Standalone Linux App Compiler     "
echo "=========================================================="

# 1. Verification of python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not installed."
    exit 1
fi

# 2. Virtual Environment Setup
echo "📦 Configuring virtual environment for compilation..."
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if ! python3 -m venv "$INSTALL_DIR/venv" &> /dev/null; then
    echo "⚠️  Python venv package is missing. Attempting to install system dependencies..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3-virtualenv python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python-virtualenv python-pip
    fi
    python3 -m venv "$INSTALL_DIR/venv"
fi

# 3. Upgrade pip and install PyQt6, PyQt6-WebEngine, and PyInstaller
echo "⚡ Installing PyQt6 and PyInstaller inside compiler sandbox..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install PyQt6 PyQt6-WebEngine pyinstaller

# 4. Compile application using PyInstaller
echo "🔨 Compiling browser.py into a standalone native Linux binary..."
"$INSTALL_DIR/venv/bin/pyinstaller" --noconsole --onefile --add-data "home.html:." --name="SLASH" browser.py

# 5. Writing the desktop application icon
echo "🎨 Registering app icon..."
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cat << 'EOF' > ~/.local/share/icons/hicolor/scalable/apps/slash.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="108" height="108">
  <rect width="108" height="108" rx="22" fill="#38BDF8"/>
  <path d="M38 74 L54 34 M54 74 L70 34" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round"/>
</svg>
EOF

# 6. Writing desktop application integration shortcut (.desktop file) pointing to compiled binary
echo "🖥️  Registering native Linux Desktop shortcut..."
mkdir -p ~/.local/share/applications
cat << EOF > ~/.local/share/applications/slash.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=SLASH
Comment=Secure, Localized Web Browser
Exec="${INSTALL_DIR}/dist/SLASH"
Icon=slash
Terminal=false
Categories=Network;WebBrowser;
EOF
chmod +x ~/.local/share/applications/slash.desktop

echo "=========================================================="
echo "🎉 SUCCESS: SLASH has been compiled into a native Linux binary!"
echo "=========================================================="
echo "Executable Path: $INSTALL_DIR/dist/SLASH"
echo "Desktop Shortcut: Installed under application launcher!"
echo "=========================================================="
