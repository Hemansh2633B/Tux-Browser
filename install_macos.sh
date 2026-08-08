#!/usr/bin/env bash
# Tux Browser Installer for macOS
# This script installs Tux Browser as a .app bundle
# Also fetches Chromium source and builds if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHROMIUM_SRC="${SCRIPT_DIR}/chromium-main/chromium-main"
BUILD_DIR="${CHROMIUM_SRC}/out/tux_browser"
APP_NAME="Tux Browser.app"
INSTALL_PREFIX="${INSTALL_PREFIX:-/Applications}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
target_os = ["mac"]
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
Tux Browser Installer for macOS

Usage: $0 [options]

Options:
    --prefix=DIR           Installation directory (default: /Applications)
    --user                 Install to ~/Applications instead
    --dmg                  Create DMG installer instead of installing
    --fetch-chromium       Fetch Chromium source before building
    --build                Build Tux Browser after fetching
    --fetch-and-build      Fetch Chromium and build (full setup)
    --uninstall            Uninstall Tux Browser
    --help                 Show this help

Examples:
    $0 --fetch-and-build              # Full setup: fetch Chromium + build + install
    $0 --fetch-chromium --build       # Fetch and build only
    $0                                 # Install only (requires existing build)
    $0 --user                         # Install to ~/Applications
    $0 --dmg                          # Create DMG installer
    $0 --uninstall                    # Uninstall
EOF
}

uninstall() {
    print_info "Uninstalling Tux Browser..."
    
    for prefix in "/Applications" "${HOME}/Applications"; do
        APP_PATH="${prefix}/${APP_NAME}"
        if [[ -d "$APP_PATH" ]]; then
            rm -rf "$APP_PATH"
            print_success "Removed $APP_PATH"
        fi
    done
    
    # Remove user data
    if [[ -d "${HOME}/.tux-browser" ]]; then
        rm -rf "${HOME}/.tux-browser"
        print_success "Removed ~/.tux-browser"
    fi
    
    print_success "Uninstallation complete!"
    exit 0
}

create_dmg() {
    print_info "Creating DMG installer..."
    
    DMG_NAME="TuxBrowser-$(date +%Y%m%d).dmg"
    DMG_DIR="${SCRIPT_DIR}/dmg_build"
    APP_SOURCE="${BUILD_DIR}/${APP_NAME}"
    
    if [[ ! -d "$APP_SOURCE" ]]; then
        print_error "App bundle not found at $APP_SOURCE"
        print_info "Please build first: ./build_tux_browser.sh"
        exit 1
    fi
    
    rm -rf "$DMG_DIR"
    mkdir -p "$DMG_DIR"
    cp -R "$APP_SOURCE" "$DMG_DIR/"
    
    # Create symlink to Applications
    ln -s /Applications "$DMG_DIR/Applications"
    
    # Create DMG
    hdiutil create -volname "Tux Browser" \
        -srcfolder "$DMG_DIR" \
        -ov -format UDZO \
        "${SCRIPT_DIR}/${DMG_NAME}"
    
    rm -rf "$DMG_DIR"
    
    print_success "Created ${SCRIPT_DIR}/${DMG_NAME}"
    print_info "Distribute this DMG for easy installation"
    exit 0
}

# Parse arguments
USER_INSTALL=false
CREATE_DMG=false
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
            INSTALL_PREFIX="${HOME}/Applications"
            shift
            ;;
        --dmg)
            CREATE_DMG=true
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

if [[ "$CREATE_DMG" == true ]]; then
    create_dmg
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
APP_SOURCE="${BUILD_DIR}/${APP_NAME}"
if [[ ! -d "$APP_SOURCE" ]]; then
    print_error "App bundle not found at $APP_SOURCE"
    print_info "Run with --fetch-and-build to fetch Chromium and build, or build first: ./build_tux_browser.sh"
    exit 1
fi

print_info "Installing Tux Browser to $INSTALL_PREFIX"

# Create Applications directory if it doesn't exist
mkdir -p "$INSTALL_PREFIX"

# Copy app bundle
APP_DEST="${INSTALL_PREFIX}/${APP_NAME}"
if [[ -d "$APP_DEST" ]]; then
    print_warning "Removing existing installation at $APP_DEST"
    rm -rf "$APP_DEST"
fi

cp -R "$APP_SOURCE" "$APP_DEST"
print_success "Installed to $APP_DEST"

# Copy embedded Tor if available
TOR_SOURCE="${SCRIPT_DIR}/tor-expert-bundle-linux-x86_64-15.0.19/tor/tor"
TOR_DEST="${APP_DEST}/Contents/MacOS/tor"
if [[ -f "$TOR_SOURCE" ]]; then
    cp "$TOR_SOURCE" "$TOR_DEST"
    chmod +x "$TOR_DEST"
    print_success "Installed embedded Tor"
    
    # Copy pluggable transports
    PT_SOURCE="${SCRIPT_DIR}/tor-expert-bundle-linux-x86_64-15.0.19/tor/pluggable_transports"
    PT_DEST="${APP_DEST}/Contents/MacOS/pluggable_transports"
    if [[ -d "$PT_SOURCE" ]]; then
        mkdir -p "$PT_DEST"
        cp "$PT_SOURCE"/* "$PT_DEST/"
        print_success "Installed pluggable transports"
    fi
else
    print_warning "Embedded Tor not found. You'll need to install Tor separately:"
    print_warning "  brew install tor"
fi

# Create launcher script inside app bundle
LAUNCHER="${APP_DEST}/Contents/MacOS/tux-browser-launcher"
cat > "$LAUNCHER" << 'EOF'
#!/usr/bin/env bash
# Tux Browser Launcher for macOS

# Find app bundle
SCRIPT_PATH="$(readlink -f "$0")"
APP_DIR="$(dirname "$(dirname "$SCRIPT_PATH")")"
MACOS_DIR="${APP_DIR}/Contents/MacOS"
TOR_BINARY="${MACOS_DIR}/tor"
TOR_DATA_DIR="${HOME}/.tux-browser/tor"
PROFILE_DIR="${HOME}/.tux-browser/profile"

mkdir -p "$TOR_DATA_DIR" "$PROFILE_DIR"

# Check if Tor is running
if ! nc -z 127.0.0.1 9050 2>/dev/null; then
    # Try to start embedded Tor
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
    else
        osascript -e 'display dialog "Embedded Tor not found. Please install Tor:\n\nbrew install tor\n\nThen ensure it runs on localhost:9050" buttons {"OK"} default button "OK" with title "Tux Browser" with icon caution'
    fi
fi

# Launch browser
exec "${MACOS_DIR}/Tux Browser" \
    --enable-features=TorNetworking \
    --proxy-server=socks5h://127.0.0.1:9050 \
    --user-data-dir="${PROFILE_DIR}" \
    "$@"
EOF

chmod +x "$LAUNCHER"

# Update Info.plist to use our launcher
PLIST="${APP_DEST}/Contents/Info.plist"
if [[ -f "$PLIST" ]]; then
    # Backup original
    cp "$PLIST" "${PLIST}.bak"
    
    # Update executable name
    /usr/libexec/PlistBuddy -c "Set :CFBundleExecutable tux-browser-launcher" "$PLIST" 2>/dev/null || true
    print_success "Updated Info.plist"
fi

# Create symlink in /usr/local/bin for CLI access
BIN_DIR="/usr/local/bin"
if [[ -w "$BIN_DIR" ]] || [[ "$USER_INSTALL" == true ]]; then
    if [[ "$USER_INSTALL" == true ]]; then
        BIN_DIR="${HOME}/.local/bin"
        mkdir -p "$BIN_DIR"
    fi
    
    ln -sf "$LAUNCHER" "${BIN_DIR}/tux-browser"
    print_success "Created CLI command: tux-browser"
else
    print_warning "Could not create CLI command (need write access to /usr/local/bin)"
    print_info "Run: sudo ln -sf \"$LAUNCHER\" /usr/local/bin/tux-browser"
fi

# Remove quarantine attribute (for unsigned builds)
if xattr -d com.apple.quarantine "$APP_DEST" 2>/dev/null; then
    print_success "Removed quarantine attribute"
fi

print_success "Installation complete!"
echo ""
echo "You can now run Tux Browser from:"
echo "  - Applications folder: Tux Browser"
echo "  - Spotlight: Search 'Tux Browser'"
echo "  - Terminal: tux-browser"
echo "  - Dock: Drag from Applications"
echo ""
echo "On first launch, Tux Browser will connect to Tor network (10-30 seconds)."
echo "Visit https://check.torproject.org to verify your connection."
echo ""
echo "Note: If you see 'app is damaged' error, run:"
echo "  xattr -d com.apple.quarantine \"$APP_DEST\""