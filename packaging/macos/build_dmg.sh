#!/usr/bin/env bash
# Tux Browser - macOS DMG Builder
# Creates a .dmg installer for macOS

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGING_DIR="${PROJECT_ROOT}/packaging/macos"
BUILD_DIR="${PROJECT_ROOT}/chromium-main/chromium-main/out/tux_browser"

# Package metadata
PACKAGE_NAME="Tux Browser"
VERSION="${VERSION:-1.0.0}"
ARCHITECTURE="${ARCHITECTURE:-universal}"  # x86_64, arm64, or universal
DMG_NAME="TuxBrowser-${VERSION}-${ARCHITECTURE}.dmg"
APP_NAME="${PACKAGE_NAME}.app"

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

usage() {
    cat << EOF
Tux Browser macOS DMG Builder

Usage: $0 [options]

Options:
    --version=VER        Package version (default: 1.0.0)
    --arch=ARCH          Architecture: x86_64, arm64, universal (default: universal)
    --build-dir=DIR      Build directory (default: auto-detect)
    --output-dir=DIR     Output directory (default: packaging/macos/output)
    --clean              Clean build directory before packaging
    --notarize           Notarize with Apple (requires Apple Developer account)
    --sign               Sign with Developer ID
    --help               Show this help

Examples:
    $0                           # Build universal DMG
    $0 --version=1.2.3 --arch=arm64  # Build Apple Silicon version
    $0 --clean --sign --notarize    # Full signed and notarized build
EOF
}

# Parse arguments
CLEAN=false
NOTARIZE=false
SIGN=false
OUTPUT_DIR="${PACKAGING_DIR}/output"

while [[ $# -gt 0 ]]; do
    case $1 in
        --version=*)
            VERSION="${1#*=}"
            shift
            ;;
        --arch=*)
            ARCHITECTURE="${1#*=}"
            shift
            ;;
        --build-dir=*)
            BUILD_DIR="${1#*=}"
            shift
            ;;
        --output-dir=*)
            OUTPUT_DIR="${1#*=}"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --notarize)
            NOTARIZE=true
            shift
            ;;
        --sign)
            SIGN=true
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

DMG_DIR="${PACKAGING_DIR}/build/dmg"
APP_SOURCE="${BUILD_DIR}/${APP_NAME}"

# Clean if requested
if [[ "$CLEAN" == true ]]; then
    print_info "Cleaning previous build..."
    rm -rf "$DMG_DIR"
fi

# Check if app bundle exists
if [[ ! -d "$APP_SOURCE" ]]; then
    print_error "App bundle not found at $APP_SOURCE"
    print_info "Build first: ./build_tux_browser.sh"
    exit 1
fi

print_info "Building DMG: ${DMG_NAME}"

# Create build directory
mkdir -p "$DMG_DIR"
mkdir -p "$OUTPUT_DIR"

# Copy app bundle
print_info "Copying app bundle..."
cp -R "$APP_SOURCE" "$DMG_DIR/"

# Copy embedded Tor if available
TOR_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-macos-${ARCHITECTURE}/tor"
if [[ -d "$TOR_SOURCE" ]]; then
    print_info "Copying embedded Tor..."
    TOR_DEST="${DMG_DIR}/${APP_NAME}/Contents/MacOS/tor"
    cp "$TOR_SOURCE/tor" "$TOR_DEST"
    chmod +x "$TOR_DEST"
    
    PT_SOURCE="${TOR_SOURCE}/pluggable_transports"
    if [[ -d "$PT_SOURCE" ]]; then
        PT_DEST="${DMG_DIR}/${APP_NAME}/Contents/MacOS/pluggable_transports"
        mkdir -p "$PT_DEST"
        cp "$PT_SOURCE"/* "$PT_DEST/"
    fi
else
    print_warning "Embedded Tor not found at $TOR_SOURCE"
    print_warning "Users will need to install Tor separately: brew install tor"
fi

# Create launcher script
LAUNCHER="${DMG_DIR}/${APP_NAME}/Contents/MacOS/tux-browser-launcher"
cat > "$LAUNCHER" << 'EOF'
#!/usr/bin/env bash
# Tux Browser Launcher for macOS

SCRIPT_PATH="$(readlink -f "$0")"
APP_DIR="$(dirname "$(dirname "$SCRIPT_PATH")")"
MACOS_DIR="${APP_DIR}/Contents/MacOS"
TOR_BINARY="${MACOS_DIR}/tor"
TOR_DATA_DIR="${HOME}/.tux-browser/tor"
PROFILE_DIR="${HOME}/.tux-browser/profile"

mkdir -p "$TOR_DATA_DIR" "$PROFILE_DIR"

# Check if Tor is running
if ! nc -z 127.0.0.1 9050 2>/dev/null; then
    if [[ -x "$TOR_BINARY" ]]; then
        "$TOR_BINARY" --DataDirectory "$TOR_DATA_DIR" --SOCKSPort 9050 --ControlPort 9051 --CookieAuthentication 1 --Log notice stdout --AvoidDiskWrites 1 &
        TOR_PID=$!
        
        for i in {1..30}; do
            if nc -z 127.0.0.1 9050 2>/dev/null; then break; fi
            sleep 1
        done
    else
        osascript -e 'display dialog "Embedded Tor not found. Please install Tor:\n\nbrew install tor\n\nThen ensure it runs on localhost:9050" buttons {"OK"} default button "OK" with title "Tux Browser" with icon caution'
    fi
fi

exec "${MACOS_DIR}/Tux Browser" \
    --enable-features=TorNetworking \
    --proxy-server=socks5h://127.0.0.1:9050 \
    --user-data-dir="${PROFILE_DIR}" \
    "$@"
EOF
chmod +x "$LAUNCHER"

# Update Info.plist to use our launcher
PLIST="${DMG_DIR}/${APP_NAME}/Contents/Info.plist"
if [[ -f "$PLIST" ]]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleExecutable tux-browser-launcher" "$PLIST" 2>/dev/null || true
fi

# Create symlink to Applications
ln -sf /Applications "$DMG_DIR/Applications"

# Create background image for DMG (optional)
if command -v convert &> /dev/null; then
    print_info "Creating DMG background..."
    mkdir -p "$DMG_DIR/.background"
    convert -size 800x500 xc:'#1a1a2e' \
        -fill '#4ec9b0' -font /System/Library/Fonts/Helvetica.ttc -pointsize 48 \
        -gravity center -annotate +0+0 'Tux Browser' \
        "$DMG_DIR/.background/background.png" 2>/dev/null || true
fi

# Create DMG
print_info "Creating DMG installer..."
hdiutil create -volname "Tux Browser ${VERSION}" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    -imagekey zlib-level=9 \
    "${OUTPUT_DIR}/${DMG_NAME}"

# Sign if requested
if [[ "$SIGN" == true ]]; then
    print_info "Signing DMG..."
    codesign --force --sign "Developer ID Application: ${DEVELOPER_NAME:-}" \
        --timestamp "${OUTPUT_DIR}/${DMG_NAME}"
fi

# Notarize if requested
if [[ "$NOTARIZE" == true ]]; then
    print_info "Submitting for notarization..."
    xcrun notarytool submit "${OUTPUT_DIR}/${DMG_NAME}" \
        --apple-id "${APPLE_ID:-}" \
        --password "${APPLE_PASSWORD:-}" \
        --team-id "${TEAM_ID:-}" \
        --wait
    
    print_info "Stapling notarization..."
    xcrun stapler staple "${OUTPUT_DIR}/${DMG_NAME}"
fi

print_success "DMG created: ${OUTPUT_DIR}/${DMG_NAME}"
print_info "Size: $(du -h "${OUTPUT_DIR}/${DMG_NAME}" | cut -f1)"

# Verify
hdiutil verify "${OUTPUT_DIR}/${DMG_NAME}"