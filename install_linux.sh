#!/usr/bin/env bash
# Tux Browser Installer for Linux
# This script installs Tux Browser system-wide or user-wide
# Also fetches Chromium source and builds if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"
CHROMIUM_SRC="${SCRIPT_DIR}/chromium-main/chromium-main"
BUILD_DIR="${CHROMIUM_SRC}/out/tux_browser"
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

fetch_chromium() {
    print_info "Fetching Chromium source..."
    
    # Check if depot_tools is available
    if ! command -v gclient &> /dev/null; then
        print_info "Installing depot_tools..."
        DEPOT_TOOLS_DIR="${HOME}/.tux-browser/depot_tools"
        if [[ ! -d "$DEPOT_TOOLS_DIR" ]]; then
            git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "$DEPOT_TOOLS_DIR"
        fi
        export PATH="${DEPOT_TOOLS_DIR}:${PATH}"
    fi
    
    # Create chromium-main directory
    mkdir -p "${SCRIPT_DIR}/chromium-main"
    cd "${SCRIPT_DIR}/chromium-main"
    
    # Initialize gclient if needed
    if [[ ! -f ".gclient" ]]; then
        print_info "Configuring gclient for Chromium..."
        cat > .gclient << 'EOF'
solutions = [
  {
    "name": "chromium-main",
    "url": "https://chromium.googlesource.com/chromium/src.git",
    "deps_file": "DEPS",
    "managed": True,
    "custom_deps": {},
    "safesync_url": "",
  },
]
target_os = ["linux"]
target_os_only = True
EOF
    fi
    
    # Sync Chromium (this will take a while)
    print_info "Syncing Chromium source (this may take 30-60 minutes)..."
    gclient sync --no-history --shallow
    
    print_success "Chromium source fetched successfully"
}

build_tux_browser() {
    print_info "Building Tux Browser..."
    
    if [[ ! -f "${CHROMIUM_SRC}/BUILD.gn" ]]; then
        print_error "Chromium source not found. Run with --fetch-chromium first."
        exit 1
    fi
    
    cd "${CHROMIUM_SRC}"
    
    # Run build script
    "${SCRIPT_DIR}/build_tux_browser.sh" --clean
    
    print_success "Tux Browser built successfully"
}

usage() {
    cat << EOF
Tux Browser Installer

Usage: $0 [options]

Options:
    --prefix=DIR           Installation prefix (default: /usr/local)
    --user                 Install to ~/.local instead of system-wide
    --fetch-chromium       Fetch Chromium source before building
    --build                Build Tux Browser after fetching
    --fetch-and-build      Fetch Chromium and build (full setup)
    --uninstall            Uninstall Tux Browser
    --help                 Show this help

Examples:
    $0 --fetch-and-build              # Full setup: fetch Chromium + build + install
    $0 --fetch-chromium --build       # Fetch and build only
    $0                                 # Install only (requires existing build)
    $0 --user                         # Install to ~/.local
    $0 --uninstall                    # Uninstall
EOF
}

# Parse arguments
USER_INSTALL=false
UNINSTALL=false
FETCH_CHROMIUM=false
BUILD=false

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
        --fetch-chromium)
            FETCH_CHROMIUM=true
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --fetch-and-build)
            FETCH_CHROMIUM=true
            BUILD=true
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

# Fetch Chromium if requested
if [[ "$FETCH_CHROMIUM" == true ]]; then
    fetch_chromium
fi

# Build if requested
if [[ "$BUILD" == true ]]; then
    build_tux_browser
fi

# Check if build exists
BINARY="${BUILD_DIR}/chrome"
if [[ ! -f "$BINARY" ]]; then
    print_error "Tux Browser binary not found at $BINARY"
    print_info "Run with --fetch-and-build to fetch Chromium and build, or build first: ./build_tux_browser.sh"
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