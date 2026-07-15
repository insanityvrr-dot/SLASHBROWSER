#!/bin/bash
set -e

echo "=========================================="
echo "       Installing SLASH Browser Linux     "
echo "=========================================="

# 1. Ensure local folder structures exist
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
mkdir -p ~/.local/share/applications

# 2. Write the SVG icon (Sky Blue with white custom slash emblem)
echo "Generating SLASH sky-blue app icon..."
cat << 'EOF' > ~/.local/share/icons/hicolor/scalable/apps/slash.svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="108" height="108">
  <rect width="108" height="108" rx="22" fill="#38BDF8"/>
  <path d="M38 74 L54 34 M54 74 L70 34" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round"/>
</svg>
EOF

# 3. Create the Linux desktop shortcut dynamically linking the absolute directory
echo "Registering desktop shortcut..."
INSTALL_DIR="$(pwd)"
cat << EOF > ~/.local/share/applications/slash.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=SLASH
Comment=Secure, Localized Web Browser
Exec=${INSTALL_DIR}/slashbrowser
Icon=slash
Terminal=false
Categories=Network;WebBrowser;
EOF

chmod +x ~/.local/share/applications/slash.desktop

echo "=========================================="
echo "SLASH is successfully configured for Linux!"
echo "Icon: ~/.local/share/icons/hicolor/scalable/apps/slash.svg"
echo "Shortcut: ~/.local/share/applications/slash.desktop"
echo "=========================================="
