#!/usr/bin/env bash
# Tux Browser - RPM Package Builder
# Creates .rpm packages for Fedora/RHEL/openSUSE-based distributions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGING_DIR="${PROJECT_ROOT}/packaging/rpm"
BUILD_DIR="${PROJECT_ROOT}/chromium-main/chromium-main/out/tux_browser"

# Package metadata
PACKAGE_NAME="tux-browser"
VERSION="${VERSION:-1.0.0}"
RELEASE="1"
ARCHITECTURE="x86_64"
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
Tux Browser RPM Package Builder

Usage: $0 [options]

Options:
    --version=VER        Package version (default: 1.0.0)
    --release=REL        Package release (default: 1)
    --build-dir=DIR      Build directory (default: auto-detect)
    --output-dir=DIR     Output directory (default: packaging/rpm/output)
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
        --release=*)
            RELEASE="${1#*=}"
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

RPM_DIR="${PACKAGING_DIR}/build/rpmbuild"
PACKAGE_FILE="${PACKAGE_NAME}-${VERSION}-${RELEASE}.${ARCHITECTURE}.rpm"

# Clean if requested
if [[ "$CLEAN" == true ]]; then
    print_info "Cleaning previous build..."
    rm -rf "$RPM_DIR"
fi

# Check if browser binary exists
BINARY="${BUILD_DIR}/chrome"
if [[ ! -f "$BINARY" ]]; then
    print_error "Browser binary not found at $BINARY"
    print_info "Build first: ./build_tux_browser.sh"
    exit 1
fi

print_info "Building RPM package: ${PACKAGE_FILE}"

# Create rpmbuild directory structure
mkdir -p "$RPM_DIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball (for SRPM)
SOURCE_DIR="${RPM_DIR}/SOURCES/${PACKAGE_NAME}-${VERSION}"
mkdir -p "$SOURCE_DIR"

# Copy binary and resources
mkdir -p "$SOURCE_DIR"/{usr/bin,usr/lib/tux-browser,usr/share/applications,usr/share/icons/hicolor/256x256/apps,usr/share/doc/tux-browser,etc/tux-browser}

cp "$BINARY" "$SOURCE_DIR/usr/lib/tux-browser/tux-browser"
chmod 755 "$SOURCE_DIR/usr/lib/tux-browser/tux-browser"

# Create launcher
cat > "$SOURCE_DIR/usr/bin/tux-browser" << 'EOF'
#!/usr/bin/env bash
INSTALL_DIR="/usr/lib/tux-browser"
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
chmod 755 "$SOURCE_DIR/usr/bin/tux-browser"

# Copy Tor if available
TOR_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-linux-x86_64-15.0.19/tor/tor"
if [[ -f "$TOR_SOURCE" ]]; then
    cp "$TOR_SOURCE" "$SOURCE_DIR/usr/lib/tux-browser/tor"
    chmod 755 "$SOURCE_DIR/usr/lib/tux-browser/tor"
    
    PT_SOURCE="${PROJECT_ROOT}/tor-expert-bundle-linux-x86_64-15.0.19/tor/pluggable_transports"
    if [[ -d "$PT_SOURCE" ]]; then
        mkdir -p "$SOURCE_DIR/usr/lib/tux-browser/pluggable_transports"
        cp "$PT_SOURCE"/* "$SOURCE_DIR/usr/lib/tux-browser/pluggable_transports/"
    fi
fi

# Desktop entry
cat > "$SOURCE_DIR/usr/share/applications/tux-browser.desktop" << EOF
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

# Create spec file
cat > "${RPM_DIR}/SPECS/${PACKAGE_NAME}.spec" << EOF
Name:           ${PACKAGE_NAME}
Version:        ${VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        Privacy-focused web browser with integrated Tor network
License:        BSD-3-Clause
URL:            ${HOMEPAGE}
Source0:        %{name}-%{version}.tar.gz
BuildArch:      ${ARCHITECTURE}
Requires:       gtk3, nss, at-spi2-atk, libdrm, libxkbcommon, libxcomposite, libxdamage, libxfixes, libxrandr, mesa-libgbm, alsa-lib, cups-libs, libatspi, libxshmfence
Recommends:     tor
Provides:       www-browser
Conflicts:      tux-browser-dev
%description
Tux Browser is a privacy-focused web browser built on Chromium
with integrated Tor network security layers. It routes all traffic
through the Tor network while maintaining Chromium's performance
and compatibility.

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

%prep
%setup -q

%build
# No build step needed - using pre-built binary

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/lib/tux-browser
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
mkdir -p %{buildroot}/usr/share/doc/tux-browser
mkdir -p %{buildroot}/etc/tux-browser

cp -r * %{buildroot}/

%post
update-desktop-database /usr/share/applications &>/dev/null || :
gtk-update-icon-cache -f /usr/share/icons/hicolor &>/dev/null || :
ln -sf /usr/bin/tux-browser /usr/local/bin/tux-browser 2>/dev/null || :

%preun
rm -f /usr/local/bin/tux-browser

%files
%license LICENSE
%doc README.md CHANGELOG.md
%{_bindir}/tux-browser
%{_libdir}/tux-browser/
%{_datadir}/applications/tux-browser.desktop
%{_datadir}/icons/hicolor/256x256/apps/tux-browser.png*
%dir %{_sysconfdir}/tux-browser

%changelog
* $(date +"%a %b %d %Y") Tux Browser Team <team@tuxbrowser.org> - ${VERSION}-${RELEASE}
- Initial RPM release of Tux Browser
- Privacy-focused Chromium with integrated Tor
- Anti-fingerprinting protection (3 levels)
- NoScript-like content blocking
- Onion service support
- Pluggable transports (obfs4, Snowflake, Conjure)
EOF

# Create source tarball
cd "$RPM_DIR/SOURCES"
tar -czf "${PACKAGE_NAME}-${VERSION}.tar.gz" "${PACKAGE_NAME}-${VERSION}"

# Build RPM
cd "$RPM_DIR"
rpmbuild --define "_topdir $RPM_DIR" -ba "SPECS/${PACKAGE_NAME}.spec"

# Copy to output
mkdir -p "$OUTPUT_DIR"
cp "$RPM_DIR/RPMS/${ARCHITECTURE}/${PACKAGE_FILE}" "$OUTPUT_DIR/"

if [[ "$SIGN" == true ]]; then
    print_info "Signing package..."
    rpm --addsign "$OUTPUT_DIR/${PACKAGE_FILE}"
fi

print_success "RPM package created: $OUTPUT_DIR/${PACKAGE_FILE}"
print_info "Package size: $(du -h "$OUTPUT_DIR/${PACKAGE_FILE}" | cut -f1)"

# Verify
rpm -qip "$OUTPUT_DIR/${PACKAGE_FILE}"
rpm -qlp "$OUTPUT_DIR/${PACKAGE_FILE}" | head -20