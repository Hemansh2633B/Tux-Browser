#!/usr/bin/env bash
# Tux Browser - DEB Package Builder
# Creates .deb packages for Debian/Ubuntu-based distributions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGING_DIR="${PROJECT_ROOT}/packaging/deb"
BUILD_DIR="${PROJECT_ROOT}/chromium-main/chromium-main/out/tux_browser"

# Package metadata
PACKAGE_NAME="tux-browser"
VERSION="${VERSION:-1.0.0}"
ARCHITECTURE="amd64"
MAINTAINER="Tux Browser Team <team@tuxbrowser.org>"
DESCRIPTION="Privacy-focused web browser with integrated Tor network"
HOMEPAGE="https://tuxbrowser.org"
LICENSE="BSD-3-Clause"

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
Tux Browser DEB Package Builder

Usage: $0 [options]

Options:
    --version=VER        Package version (default: 1.0.0)
    --build-dir=DIR      Build directory (default: auto-detect)
    --output-dir=DIR     Output directory (default: packaging/deb/output)
    --clean              Clean build directory before packaging
    --sign               Sign package with GPG
    --help               Show this help

Examples:
    $0                           # Build with defaults
    $0 --version=1.2.3           # Build specific version
    $0 --clean --sign            # Clean build and sign
EOF
}

# Parse arguments
CLEAN=false
SIGN=false
OUTPUT_DIR="${PACKAGING_DIR}/output"

while [[ $# -gt 0 ]]; do
    case $1 in
        --version=*)
            VERSION="${1#*=}"
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

PACKAGE_FILE="${PACKAGE_NAME}_${VERSION}-1_${ARCHITECTURE}.deb"
DEB_DIR="${PACKAGING_DIR}/build/${PACKAGE_NAME}_${VERSION}-1_${ARCHITECTURE}"

# Clean if requested
if [[ "$CLEAN" == true ]]; then
    print_info "Cleaning previous build..."
    rm -rf "${PACKAGING_DIR}/build"
fi

# Check if browser binary exists
BINARY="${BUILD_DIR}/chrome"
if [[ ! -f "$BINARY" ]]; then
    print_error "Browser binary not found at $BINARY"
    print_info "Build first: ./build_tux_browser.sh"
    exit 1
fi

print_info "Building DEB package: ${PACKAGE_FILE}"

# Create directory structure
mkdir -p "$DEB_DIR"/{DEBIAN,usr/bin,usr/lib/tux-browser,usr/share/applications,usr/share/icons/hicolor/256x256/apps,usr/share/doc/tux-browser,etc/tux-browser}

# Copy binary
print_info "Copying browser binary..."
cp "$BINARY" "${DEB_DIR}/usr/lib/tux-browser/tux-browser"
chmod 755 "${DEB_DIR}/usr/lib/tux-browser/tux-browser"

# Create launcher script
cat > "${DEB_DIR}/usr/bin/tux-browser" << 'EOF'
#!/usr/bin/env bash
# Tux Browser Launcher

INSTALL_DIR="/usr/lib/tux-browser"
TOR_DATA_DIR="${HOME}/.tux-browser/tor"
PROFILE_DIR="${HOME}/.tux-browser/profile"

mkdir -p "$TOR_DATA_DIR" "$PROFILE_DIR"

# Check if Tor is running
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
chmod 755 "${DEB_DIR}/usr/bin/tux-browser"

# Copy Tor if available
TOR_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-linux-x86_64-15.0.19/tor/tor"
if [[ -f "$TOR_SOURCE" ]]; then
    print_info "Copying embedded Tor..."
    cp "$TOR_SOURCE" "${DEB_DIR}/usr/lib/tux-browser/tor"
    chmod 755 "${DEB_DIR}/usr/lib/tux-browser/tor"
    
    PT_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-linux-x86_64-15.0.19/tor/pluggable_transports"
    if [[ -d "$PT_SOURCE" ]]; then
        mkdir -p "${DEB_DIR}/usr/lib/tux-browser/pluggable_transports"
        cp "$PT_SOURCE"/* "${DEB_DIR}/usr/lib/tux-browser/pluggable_transports/"
    fi
fi

# Create desktop entry
cat > "${DEB_DIR}/usr/share/applications/tux-browser.desktop" << EOF
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

# Create icon placeholder
cat > "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/tux-browser.png.placeholder" << 'EOF'
Replace with actual 256x256 PNG icon
EOF

# Create control file
INSTALLED_SIZE=$(du -sk "${DEB_DIR}" | cut -f1)
cat > "${DEB_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}-1
Section: web
Priority: optional
Architecture: ${ARCHITECTURE}
Installed-Size: ${INSTALLED_SIZE}
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 Tux Browser is a privacy-focused web browser built on Chromium
 with integrated Tor network security layers. It routes all traffic
 through the Tor network while maintaining Chromium's performance
 and compatibility.
 .
 Features:
  * Onion Routing - All traffic encrypted through 3 Tor relays
  * IP Anonymity - Real IP hidden from websites
  * ISP Surveillance Block - ISP cannot see visited websites
  * Website Isolation - First-Party Isolation prevents tracking
  * Anti-Fingerprinting - 3 security levels (Standard/Safer/Safest)
  * Censorship Bypassing - Access blocked websites
  * Hidden/Onion Services - Native .onion domain support
  * Pluggable Transports - obfs4, Snowflake, Conjure, meek
  * NoScript-like Content Blocking - JS, WebRTC, WebGL blocked by default
Homepage: ${HOMEPAGE}
License: ${LICENSE}
Depends: libgtk-3-0, libnss3, libatk-bridge2.0-0, libdrm2, libxkbcommon0, libxcomposite1, libxdamage1, libxfixes3, libxrandr2, libgbm1, libasound2, libcups2, libatspi2.0-0, libxshmfence1, netcat-openbsd
Recommends: tor
Provides: www-browser
Conflicts: tux-browser-dev
EOF

# Create copyright file
cat > "${DEB_DIR}/usr/share/doc/tux-browser/copyright" << EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Tux Browser
Upstream-Contact: Tux Browser Team <team@tuxbrowser.org>
Source: https://github.com/tuxbrowser/tux-browser

Files: *
Copyright: 2024 The Tux Browser Authors
License: BSD-3-Clause
 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:
 .
 1. Redistributions of source code must retain the above copyright notice,
    this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.
 3. Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.
 .
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Files: debian/*
Copyright: 2024 Tux Browser Team <team@tuxbrowser.org>
License: BSD-3-Clause
EOF

# Create changelog
cat > "${DEB_DIR}/usr/share/doc/tux-browser/changelog.Debian" << EOF
tux-browser (${VERSION}-1) stable; urgency=medium

  * Initial release of Tux Browser
  * Privacy-focused Chromium with integrated Tor
  * Anti-fingerprinting protection (3 levels)
  * NoScript-like content blocking
  * Onion service support
  * Pluggable transports (obfs4, Snowflake, Conjure)

 -- Tux Browser Team <team@tuxbrowser.org>  $(date -R)
EOF
gzip -9 -c "${DEB_DIR}/usr/share/doc/tux-browser/changelog.Debian" > "${DEB_DIR}/usr/share/doc/tux-browser/changelog.Debian.gz"
rm "${DEB_DIR}/usr/share/doc/tux-browser/changelog.Debian"

# Create postinst script
cat > "${DEB_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor
fi

# Create symlink for CLI access
ln -sf /usr/bin/tux-browser /usr/local/bin/tux-browser 2>/dev/null || true

exit 0
EOF
chmod 755 "${DEB_DIR}/DEBIAN/postinst"

# Create prerm script
cat > "${DEB_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Remove CLI symlink
rm -f /usr/local/bin/tux-browser

exit 0
EOF
chmod 755 "${DEB_DIR}/DEBIAN/prerm"

# Build package
mkdir -p "$OUTPUT_DIR"
cd "$(dirname "$DEB_DIR")"
dpkg-deb --build "$(basename "$DEB_DIR")"

# Move to output
mv "${PACKAGE_FILE}" "$OUTPUT_DIR/"

# Sign if requested
if [[ "$SIGN" == true ]]; then
    print_info "Signing package..."
    dpkg-sig -k "${GPG_KEY:-}" --sign builder "$OUTPUT_DIR/${PACKAGE_FILE}"
fi

print_success "DEB package created: $OUTPUT_DIR/${PACKAGE_FILE}"
print_info "Package size: $(du -h "$OUTPUT_DIR/${PACKAGE_FILE}" | cut -f1)"

# Verify package
dpkg-deb -I "$OUTPUT_DIR/${PACKAGE_FILE}"
dpkg-deb -c "$OUTPUT_DIR/${PACKAGE_FILE}" | head -20