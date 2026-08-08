#!/usr/bin/env bash
# Tux Browser Installer for Linux
# This script installs Tux Browser system-wide or user-wide

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"
BUILD_DIR="${SCRIPT_DIR}/chromium-main/chromium-main/out/tux_browser"
DESKTOP_FILE="tux-browser.desktop"
ICON_FILE="tux-browser.png"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
print_error() { echo -e "${RED}[ERROR]${NC} $*"; }

usage() {
    cat << EOF
Tux Browser Installer

Usage: $0 [options]

Options:
    --prefix=DIR      Installation prefix (default: /usr/local)
    --user            Install to ~/.local instead of system-wide
    --uninstall       Uninstall Tux Browser
    --help            Show this help

Examples:
    $0                    # Install system-wide to /usr/local
    $0 --user             # Install to ~/.local
    $0 --prefix=/opt      # Install to /opt
    $0 --uninstall        # Uninstall
EOF
}

uninstall() {
    print_info "Uninstalling Tux Browser..."
    
    # System-wide
    for prefix in "/usr/local" "/opt"; do
        if [[ -f "${prefix}/bin/tux-browser" ]]; then
            rm -f "${prefix}/bin/tux-browser"
            print_success "Removed ${prefix}/bin/tux-browser"
        fi
        if [[ -d "${prefix}/lib/tux-browser" ]]; then
            rm -rf "${prefix}/lib/tux-browser"
            print_success "Removed ${prefix}/lib/tux-browser"
        fi
        if [[ -f "${prefix}/share/applications/tux-browser.desktop" ]]; then
            rm -f "${prefix}/share/applications/tux-browser.desktop"
            print_success "Removed desktop entry"
        fi
        if [[ -f "${prefix}/share/icons/hicolor/256x256/apps/tux-browser.png" ]]; then
            rm -f "${prefix}/share/icons/hicolor/256x256/apps/tux-browser.png"
            print_success "Removed icon"
        fi
    done
    
    # User-wide
    if [[ -f "${HOME}/.local/bin/tux-browser" ]]; then
        rm -f "${HOME}/.local/bin/tux-browser"
        print_success "Removed ~/.local/bin/tux-browser"
    fi
    if [[ -d "${HOME}/.local/lib/tux-browser" ]]; then
        rm -rf "${HOME}/.local/lib/tux-browser"
        print_success "Removed ~/.local/lib/tux-browser"
    fi
    if [[ -f "${HOME}/.local/share/applications/tux-browser.desktop" ]]; then
        rm -f "${HOME}/.local/share/applications/tux-browser.desktop"
        print_success "Removed user desktop entry"
    fi
    if [[ -f "${HOME}/.local/share/icons/hicolor/256x256/apps/tux-browser.png" ]]; then
        rm -f "${HOME}/.local/share/icons/hicolor/256x256/apps/tux-browser.png"
        print_success "Removed user icon"
    fi
    
    print_success "Uninstallation complete!"
    exit 0
}

# Parse arguments
USER_INSTALL=false
UNINSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix=*)
            INSTALL_PREFIX="${1#*=}"
            shift
            ;;
        --user)
            USER_INSTALL=true
            INSTALL_PREFIX="${HOME}/.local"
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

if [[ "$UNINSTALL" == true ]]; then
    uninstall
fi

# Check if build exists
BINARY="${BUILD_DIR}/chrome"
if [[ ! -f "$BINARY" ]]; then
    print_error "Tux Browser binary not found at $BINARY"
    print_info "Please build first: ./build_tux_browser.sh"
    exit 1
fi

print_info "Installing Tux Browser to $INSTALL_PREFIX"

# Create directories
BIN_DIR="${INSTALL_PREFIX}/bin"
LIB_DIR="${INSTALL_PREFIX}/lib/tux-browser"
DESKTOP_DIR="${INSTALL_PREFIX}/share/applications"
ICON_DIR="${INSTALL_PREFIX}/share/icons/hicolor/256x256/apps"

mkdir -p "$BIN_DIR" "$LIB_DIR" "$DESKTOP_DIR" "$ICON_DIR"

# Copy binary and libraries
print_info "Copying binary..."
cp "$BINARY" "$LIB_DIR/tux-browser"

# Create wrapper script
cat > "$BIN_DIR/tux-browser" << 'EOF'
#!/usr/bin/env bash
# Tux Browser Launcher

# Find installation directory
SCRIPT_PATH="$(readlink -f "$0")"
INSTALL_DIR="$(dirname "$(dirname "$SCRIPT_PATH")")/lib/tux-browser"

# Tor configuration
TOR_DATA_DIR="${HOME}/.tux-browser/tor"
mkdir -p "$TOR_DATA_DIR"

# Check if Tor is running
if ! nc -z 127.0.0.1 9050 2>/dev/null; then
    # Try to start embedded Tor
    TOR_BINARY="${INSTALL_DIR}/tor"
    if [[ -x "$TOR_BINARY" ]]; then
        "$TOR_BINARY" --DataDirectory "$TOR_DATA_DIR" --SOCKSPort 9050 --ControlPort 9051 --CookieAuthentication 1 --Log notice stdout --AvoidDiskWrites 1 &
        TOR_PID=$!
        # Wait for Tor to start
        for i in {1..30}; do
            if nc -z 127.0.0.1 9050 2>/dev/null; then
                break
            fi
            sleep 1
        done
    fi
fi

# Launch browser
exec "${INSTALL_DIR}/tux-browser" \
    --enable-features=TorNetworking \
    --proxy-server=socks5h://127.0.0.1:9050 \
    --user-data-dir="${HOME}/.tux-browser/profile" \
    "$@"
EOF

chmod +x "$BIN_DIR/tux-browser"
print_success "Installed launcher to $BIN_DIR/tux-browser"

# Copy browser binary
cp "$BINARY" "$LIB_DIR/tux-browser"
print_success "Installed binary to $LIB_DIR/tux-browser"

# Copy Tor if available
TOR_BINARY="${SCRIPT_DIR}/tor-expert-bundle-linux-x86_64-15.0.19/tor/tor"
if [[ -f "$TOR_BINARY" ]]; then
    cp "$TOR_BINARY" "$LIB_DIR/tor"
    chmod +x "$LIB_DIR/tor"
    print_success "Installed embedded Tor"
    
    # Copy pluggable transports
    PT_DIR="${SCRIPT_DIR}/tor-expert-bundle-linux-x86_64-15.0.19/tor/pluggable_transports"
    if [[ -d "$PT_DIR" ]]; then
        mkdir -p "$LIB_DIR/pluggable_transports"
        cp "$PT_DIR"/* "$LIB_DIR/pluggable_transports/"
        print_success "Installed pluggable transports"
    fi
fi

# Create desktop entry
cat > "$DESKTOP_DIR/tux-browser.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Tux Browser
GenericName=Privacy Web Browser
Comment=Privacy-focused browser with integrated Tor network
Exec=tux-browser %U
Terminal=false
Icon=tux-browser
Categories=Network;WebBrowser;Security;
StartupNotify=true
Keywords=tor;privacy;anonymous;onion;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
EOF
print_success "Created desktop entry"

# Create icon (placeholder - replace with actual icon)
if command -v convert &> /dev/null; then
    # Create a simple icon using ImageMagick
    convert -size 256x256 xc:'#1a1a2e' \
        -fill '#4ec9b0' -font DejaVu-Sans-Bold -pointsize 120 \
        -gravity center -annotate +0+0 '🐧' \
        "$ICON_DIR/tux-browser.png" 2>/dev/null || true
else
    # Create a simple text-based placeholder
    cat > "$ICON_DIR/tux-browser.png.placeholder" << 'EOF'
This is a placeholder for the Tux Browser icon.
Replace with actual 256x256 PNG icon.
EOF
fi
print_success "Icon placeholder created (replace with actual icon)"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f "$(dirname "$ICON_DIR")" 2>/dev/null || true
fi

print_success "Installation complete!"
echo ""
echo "You can now run Tux Browser from:"
echo "  - Application menu: Search for 'Tux Browser'"
echo "  - Terminal: tux-browser"
echo "  - Run dialog: Alt+F2, type 'tux-browser'"
echo ""
echo "On first launch, Tux Browser will connect to Tor network (10-30 seconds)."
echo "Visit https://check.torproject.org to verify your connection."