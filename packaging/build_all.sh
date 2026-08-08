#!/usr/bin/env bash
# Tux Browser - Universal Package Builder
# Builds all package formats: DEB, RPM, DMG, MSI, NSIS, AppImage

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Package metadata
VERSION="${VERSION:-1.0.0}"
ARCHITECTURE="${ARCHITECTURE:-x86_64}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() { echo -e "${CYAN}===========================================${NC}"; echo -e "${CYAN}$*${NC}"; echo -e "${CYAN}===========================================${NC}"; }
print_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
print_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Track build results
BUILD_RESULTS=()

usage() {
    cat << EOF
Tux Browser Universal Package Builder

Usage: $0 [options]

Options:
    --version=VER        Package version (default: 1.0.0)
    --arch=ARCH          Architecture (default: x86_64)
    --formats=FORMATS    Comma-separated list: deb,rpm,dmg,msi,nsis,appimage,all (default: all)
    --clean              Clean before building
    --output-dir=DIR     Output directory (default: packaging/output)
    --parallel           Build packages in parallel (where possible)
    --help               Show this help

Examples:
    $0                                    # Build all formats
    $0 --formats=deb,rpm                  # Build only Linux packages
    $0 --formats=dmg --version=1.2.3      # Build macOS DMG
    $0 --clean --parallel                 # Clean parallel build
EOF
}

# Parse arguments
CLEAN=false
PARALLEL=false
FORMATS="all"
OUTPUT_DIR="${PROJECT_ROOT}/packaging/output"

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
        --formats=*)
            FORMATS="${1#*=}"
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --output-dir=*)
            OUTPUT_DIR="${1#*=}"
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

# Determine which formats to build
BUILD_DEB=false
BUILD_RPM=false
BUILD_DMG=false
BUILD_MSI=false
BUILD_NSIS=false
BUILD_APPIMAGE=false

if [[ "$FORMATS" == "all" ]]; then
    BUILD_DEB=true
    BUILD_RPM=true
    BUILD_DMG=true
    BUILD_MSI=true
    BUILD_NSIS=true
    BUILD_APPIMAGE=true
else
    IFS=',' read -ra FORMAT_ARRAY <<< "$FORMATS"
    for fmt in "${FORMAT_ARRAY[@]}"; do
        case "$fmt" in
            deb) BUILD_DEB=true ;;
            rpm) BUILD_RPM=true ;;
            dmg) BUILD_DMG=true ;;
            msi) BUILD_MSI=true ;;
            nsis) BUILD_NSIS=true ;;
            appimage) BUILD_APPIMAGE=true ;;
            *) print_warning "Unknown format: $fmt" ;;
        esac
    done
fi

# Check build binary
BUILD_DIR="${PROJECT_ROOT}/chromium-main/chromium-main/out/tux_browser"
BINARY="${BUILD_DIR}/chrome"
if [[ ! -f "$BINARY" ]]; then
    print_error "Browser binary not found at $BINARY"
    print_info "Build first: ./build_tux_browser.sh"
    exit 1
fi

print_header "Tux Browser Universal Package Builder"
print_info "Version: $VERSION"
print_info "Architecture: $ARCHITECTURE"
print_info "Formats: $FORMATS"
print_info "Output: $OUTPUT_DIR"

# Clean if requested
if [[ "$CLEAN" == true ]]; then
    print_info "Cleaning previous builds..."
    rm -rf "${PROJECT_ROOT}/packaging/deb/build"
    rm -rf "${PROJECT_ROOT}/packaging/rpm/build"
    rm -rf "${PROJECT_ROOT}/packaging/macos/build"
    rm -rf "${PROJECT_ROOT}/packaging/windows/build"
    rm -rf "${PROJECT_ROOT}/packaging/universal/build"
fi

mkdir -p "$OUTPUT_DIR"

# Function to build DEB
build_deb() {
    print_header "Building DEB Package"
    if "${PROJECT_ROOT}/packaging/deb/build_deb.sh" --version="$VERSION" --output-dir="$OUTPUT_DIR" ${CLEAN:+--clean}; then
        BUILD_RESULTS+=("DEB: SUCCESS")
        print_success "DEB package built successfully"
    else
        BUILD_RESULTS+=("DEB: FAILED")
        print_error "DEB package build failed"
    fi
}

# Function to build RPM
build_rpm() {
    print_header "Building RPM Package"
    if "${PROJECT_ROOT}/packaging/rpm/build_rpm.sh" --version="$VERSION" --output-dir="$OUTPUT_DIR" ${CLEAN:+--clean}; then
        BUILD_RESULTS+=("RPM: SUCCESS")
        print_success "RPM package built successfully"
    else
        BUILD_RESULTS+=("RPM: FAILED")
        print_error "RPM package build failed"
    fi
}

# Function to build DMG
build_dmg() {
    print_header "Building macOS DMG"
    if "${PROJECT_ROOT}/packaging/macos/build_dmg.sh" --version="$VERSION" --arch="$ARCHITECTURE" --output-dir="$OUTPUT_DIR" ${CLEAN:+--clean}; then
        BUILD_RESULTS+=("DMG: SUCCESS")
        print_success "DMG package built successfully"
    else
        BUILD_RESULTS+=("DMG: FAILED")
        print_error "DMG package build failed"
    fi
}

# Function to build MSI (WiX)
build_msi() {
    print_header "Building Windows MSI (WiX)"
    if command -v candle &> /dev/null && command -v light &> /dev/null; then
        cd "${PROJECT_ROOT}/packaging/windows"
        if candle -DVERSION="$VERSION" -DBinarySource="${BUILD_DIR}" TuxBrowser.wxs -o build/ && \
           light -o "${OUTPUT_DIR}/TuxBrowser-${VERSION}-${ARCHITECTURE}.msi" build/TuxBrowser.wixobj; then
            BUILD_RESULTS+=("MSI: SUCCESS")
            print_success "MSI package built successfully"
        else
            BUILD_RESULTS+=("MSI: FAILED")
            print_error "MSI package build failed"
        fi
    else
        print_warning "WiX tools (candle, light) not found. Skipping MSI build."
        BUILD_RESULTS+=("MSI: SKIPPED (WiX not installed)")
    fi
}

# Function to build NSIS installer
build_nsis() {
    print_header "Building Windows NSIS Installer"
    if command -v makensis &> /dev/null; then
        cd "${PROJECT_ROOT}/packaging/windows"
        if makensis /DVERSION="$VERSION" /DBinarySource="${BUILD_DIR}" /DTOR_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-windows-x64/tor" /DOUTPUT_DIR="${OUTPUT_DIR}" TuxBrowser.nsi; then
            BUILD_RESULTS+=("NSIS: SUCCESS")
            print_success "NSIS installer built successfully"
        else
            BUILD_RESULTS+=("NSIS: FAILED")
            print_error "NSIS installer build failed"
        fi
    else
        print_warning "NSIS (makensis) not found. Skipping NSIS build."
        BUILD_RESULTS+=("NSIS: SKIPPED (NSIS not installed)")
    fi
}

# Function to build AppImage
build_appimage() {
    print_header "Building AppImage"
    
    APPIMAGE_DIR="${PROJECT_ROOT}/packaging/universal/build/appimage"
    mkdir -p "$APPIMAGE_DIR"
    
    # Create AppDir structure
    APPDIR="${APPIMAGE_DIR}/TuxBrowser.AppDir"
    mkdir -p "$APPDIR"/{usr/bin,usr/lib/tux-browser,usr/share/applications,usr/share/icons/hicolor/256x256/apps}
    
    # Copy binary
    cp "$BINARY" "$APPDIR/usr/lib/tux-browser/tux-browser"
    chmod 755 "$APPDIR/usr/lib/tux-browser/tux-browser"
    
    # Create launcher
    cat > "$APPDIR/usr/bin/tux-browser" << 'EOF'
#!/usr/bin/env bash
APPDIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
INSTALL_DIR="${APPDIR}/usr/lib/tux-browser"
TOR_DATA_DIR="${HOME}/.tux-browser/tor"
PROFILE_DIR="${HOME}/.tux-browser/profile"

mkdir -p "$TOR_DATA_DIR" "$PROFILE_DIR"

if ! nc -z 127.0.0.1 9050 2>/dev/null; then
    TOR_BINARY="${INSTALL_DIR}/tor"
    if [[ -x "$TOR_BINARY" ]]; then
        "$TOR_BINARY" --DataDirectory "$TOR_DATA_DIR" --SOCKSPort 9050 --ControlPort 9051 --CookieAuthentication 1 --Log notice stdout --AvoidDiskWrites 1 &
        for i in {1..30}; do
            if nc -z 127.0.0.1 9050 2>/dev/null; then break; fi
            sleep 1
        done
    fi
fi

exec "${INSTALL_DIR}/tux-browser" \
    --enable-features=TorNetworking \
    --proxy-server=socks5h://127.0.0.1:9050 \
    --user-data-dir="${PROFILE_DIR}" \
    "$@"
EOF
    chmod 755 "$APPDIR/usr/bin/tux-browser"
    
    # Copy Tor if available
    TOR_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-linux-x86_64-15.0.19/tor/tor"
    if [[ -f "$TOR_SOURCE" ]]; then
        cp "$TOR_SOURCE" "$APPDIR/usr/lib/tux-browser/tor"
        chmod 755 "$APPDIR/usr/lib/tux-browser/tor"
        
        PT_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-linux-x86_64-15.0.19/tor/pluggable_transports"
        if [[ -d "$PT_SOURCE" ]]; then
            mkdir -p "$APPDIR/usr/lib/tux-browser/pluggable_transports"
            cp "$PT_SOURCE"/* "$APPDIR/usr/lib/tux-browser/pluggable_transports/"
        fi
    fi
    
    # Desktop entry
    cat > "$APPDIR/usr/share/applications/tux-browser.desktop" << EOF
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
    
    # Icon placeholder
    cat > "$APPDIR/usr/share/icons/hicolor/256x256/apps/tux-browser.png.placeholder" << 'EOF'
Replace with actual 256x256 PNG icon
EOF
    
    # AppRun
    cat > "$APPDIR/AppRun" << 'EOF'
#!/usr/bin/env bash
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="${APPDIR}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${LD_LIBRARY_PATH}"
exec "${APPDIR}/usr/bin/tux-browser" "$@"
EOF
    chmod 755 "$APPDIR/AppRun"
    
    # Download appimagetool if needed
    APPIMAGETOOL="${APPIMAGE_DIR}/appimagetool-x86_64.AppImage"
    if [[ ! -f "$APPIMAGETOOL" ]]; then
        print_info "Downloading appimagetool..."
        wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O "$APPIMAGETOOL"
        chmod +x "$APPIMAGETOOL"
    fi
    
    # Build AppImage
    print_info "Building AppImage..."
    ARCH="${ARCHITECTURE}" "$APPIMAGETOOL" "$APPDIR" "${OUTPUT_DIR}/TuxBrowser-${VERSION}-${ARCHITECTURE}.AppImage"
    
    BUILD_RESULTS+=("AppImage: SUCCESS")
    print_success "AppImage built successfully"
}

# Build packages
START_TIME=$(date +%s)

if [[ "$PARALLEL" == true ]]; then
    print_info "Building packages in parallel..."
    
    PIDS=()
    
    [[ "$BUILD_DEB" == true ]] && build_deb & PIDS+=($!)
    [[ "$BUILD_RPM" == true ]] && build_rpm & PIDS+=($!)
    [[ "$BUILD_DMG" == true ]] && build_dmg & PIDS+=($!)
    [[ "$BUILD_MSI" == true ]] && build_msi & PIDS+=($!)
    [[ "$BUILD_NSIS" == true ]] && build_nsis & PIDS+=($!)
    [[ "$BUILD_APPIMAGE" == true ]] && build_appimage & PIDS+=($!)
    
    # Wait for all background jobs
    for pid in "${PIDS[@]}"; do
        wait "$pid"
    done
else
    print_info "Building packages sequentially..."
    
    [[ "$BUILD_DEB" == true ]] && build_deb
    [[ "$BUILD_RPM" == true ]] && build_rpm
    [[ "$BUILD_DMG" == true ]] && build_dmg
    [[ "$BUILD_MSI" == true ]] && build_msi
    [[ "$BUILD_NSIS" == true ]] && build_nsis
    [[ "$BUILD_APPIMAGE" == true ]] && build_appimage
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Print summary
print_header "Build Summary"
print_info "Total time: ${DURATION}s"
print_info "Version: $VERSION"
echo ""

for result in "${BUILD_RESULTS[@]}"; do
    if [[ "$result" == *"SUCCESS"* ]]; then
        print_success "$result"
    elif [[ "$result" == *"SKIPPED"* ]]; then
        print_warning "$result"
    else
        print_error "$result"
    fi
done

echo ""
print_info "Output directory: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/ 2>/dev/null || true

# Check for any failures
FAILED=0
for result in "${BUILD_RESULTS[@]}"; do
    if [[ "$result" == *"FAILED"* ]]; then
        FAILED=1
    fi
done

exit $FAILED