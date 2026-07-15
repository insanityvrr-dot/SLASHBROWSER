#!/bin/bash
set -e

echo "=========================================================="
echo "      🚀 SLASH Browser - Native Linux Desktop Installer   "
echo "=========================================================="

# 1. Verification of python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not installed."
    echo "Please install python3 using your distribution's package manager and try again."
    exit 1
fi

# 2. Virtual Environment Setup
echo "📦 Configuring local sandboxed Python environment..."
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if venv works. If not, attempt automatic provisioning of python3-venv on common distros.
if ! python3 -m venv "$INSTALL_DIR/venv" &> /dev/null; then
    echo "⚠️  Python venv package is missing. Attempting to install system dependencies..."
    if command -v apt-get &> /dev/null; then
        echo "Running: sudo apt-get update && sudo apt-get install -y python3-venv python3-pip"
        sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
    elif command -v dnf &> /dev/null; then
        echo "Running: sudo dnf install -y python3-virtualenv python3-pip"
        sudo dnf install -y python3-virtualenv python3-pip
    elif command -v pacman &> /dev/null; then
        echo "Running: sudo pacman -S --noconfirm python-virtualenv python-pip"
        sudo pacman -S --noconfirm python-virtualenv python-pip
    else
        echo "❌ System package manager not identified. Please install python3-venv and pip manually."
        exit 1
    fi
    # Re-try creating the virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
fi

# 3. Upgrading pip and installing PyQt6 dependencies
echo "⚡ Installing latest Qt6 and WebEngine bindings..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install PyQt6 PyQt6-WebEngine

# 4. Creating the main launcher script 'slashbrowser'
echo "🔨 Creating local executable launcher..."
cat << 'EOF' > "$INSTALL_DIR/slashbrowser"
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
"$DIR/venv/bin/python" "$DIR/browser.py" "$@"
EOF
chmod +x "$INSTALL_DIR/slashbrowser"

# 5. Placing high-quality Sky Blue App Icon to matching system specification
echo "🎨 Writing high-quality desktop icon..."
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cat << 'EOF' > ~/.local/share/icons/hicolor/scalable/apps/slash.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="108" height="108">
  <rect width="108" height="108" rx="22" fill="#38BDF8"/>
  <path d="M38 74 L54 34 M54 74 L70 34" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round"/>
</svg>
EOF

# 6. Writing desktop application integration shortcut (.desktop file)
echo "🖥️  Registering Linux Desktop shortcut..."
mkdir -p ~/.local/share/applications
cat << EOF > ~/.local/share/applications/slash.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=SLASH
Comment=Secure, Localized Web Browser
Exec="${INSTALL_DIR}/slashbrowser"
Icon=slash
Terminal=false
Categories=Network;WebBrowser;
EOF
chmod +x ~/.local/share/applications/slash.desktop

echo "=========================================================="
echo "🎉 SUCCESS: SLASH has been fully installed on your Linux desktop!"
echo "=========================================================="
echo "You can now run SLASH directly from your Application Launcher"
echo "or via command-line in this folder using: ./slashbrowser"
echo "=========================================================="
