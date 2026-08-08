# Tux Browser

![Tux Browser](https://img.shields.io/badge/Tux%20Browser-Privacy%20Focused-blue?style=for-the-badge&logo=tor)
![License](https://img.shields.io/badge/License-BSD--3--Clause-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey?style=for-the-badge)

**Tux Browser** is a privacy-focused web browser built on Chromium with integrated Tor network security layers. It routes all traffic through the Tor network while maintaining Chromium's performance, compatibility, and extension support.

## 🎯 Key Features

### 🔐 Network Security
- **Onion Routing**: All traffic encrypted and routed through 3 Tor relays
- **IP Anonymity**: Your real IP address is hidden from websites
- **ISP Surveillance Block**: Your ISP cannot see which websites you visit
- **Website Isolation**: First-Party Isolation prevents cross-site tracking
- **Anti-Fingerprinting**: 3 security levels (Standard/Safer/Safest) make all users look identical

### 🛡️ Security & Access
- **Censorship Bypassing**: Access blocked websites in restricted regions
- **Hidden/Onion Services**: Native `.onion` domain support
- **Pluggable Transports**: obfs4, Snowflake, Conjure, meek, webtunnel bridges
- **Adjustable Security Levels**: Standard → Safer → Safest modes

### 🔧 Privacy Features
- **No Telemetry**: Zero metrics, crash reporting, or safe browsing to Google
- **NoScript-like Blocking**: JavaScript, WebAssembly, WebRTC, WebGL blocked by default
- **HTTPS-Only Mode**: Automatic HTTPS enforcement
- **Referrer Protection**: Strict-origin-when-cross-origin policy
- **ETag/Cache Protection**: Anti-tracking cache headers

---

## 📦 Installation

### 🐧 Linux

#### Option 1: AppImage (Recommended - Universal)
```bash
# Download latest release
wget https://github.com/tuxbrowser/tux-browser/releases/latest/download/TuxBrowser-latest-x86_64.AppImage
chmod +x TuxBrowser-latest-x86_64.AppImage
./TuxBrowser-latest-x86_64.AppImage
```

#### Option 2: DEB Package (Debian/Ubuntu/Mint)
```bash
# Add repository
curl -fsSL https://repo.tuxbrowser.org/KEY.gpg | sudo gpg --dearmor -o /usr/share/keyrings/tuxbrowser-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/tuxbrowser-archive-keyring.gpg] https://repo.tuxbrowser.org/apt stable main" | sudo tee /etc/apt/sources.list.d/tuxbrowser.list

# Install
sudo apt update && sudo apt install tux-browser
```

#### Option 3: RPM Package (Fedora/RHEL/openSUSE)
```bash
# Add repository
sudo dnf config-manager --add-repo https://repo.tuxbrowser.org/rpm/tuxbrowser.repo

# Install
sudo dnf install tux-browser
```

#### Option 4: Flatpak
```bash
flatpak install flathub org.tuxbrowser.TuxBrowser
flatpak run org.tuxbrowser.TuxBrowser
```

#### Option 5: Build from Source
```bash
# Install dependencies
sudo apt install -y git python3 gn ninja-build nodejs npm  # Debian/Ubuntu
sudo dnf install -y git python3 gn ninja-build nodejs npm  # Fedora

# Clone and build
git clone https://github.com/tuxbrowser/tux-browser.git
cd tux-browser
./build_tux_browser.sh --clean

# Run
./chromium-main/chromium-main/out/tux_browser/chrome --enable-features=TorNetworking
```

#### System Requirements (Linux)
- **OS**: Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch Linux
- **Arch**: x86_64 (ARM64 experimental)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk**: 3 GB for installation
- **Tor**: Runs embedded (no separate Tor installation needed)

---

### 🪟 Windows

#### Option 1: Installer (Recommended)
1. Download `TuxBrowser-Setup-x64.exe` from [Releases](https://github.com/tuxbrowser/tux-browser/releases)
2. Run the installer (requires Administrator for system-wide install)
3. Launch from Start Menu or Desktop shortcut

#### Option 2: Portable Version
1. Download `TuxBrowser-Portable-x64.zip`
2. Extract to any folder (e.g., `C:\TuxBrowser` or USB drive)
3. Run `TuxBrowser.exe` - no installation needed

#### Option 3: Winget
```powershell
winget install TuxBrowser.TuxBrowser
```

#### Option 4: Chocolatey
```powershell
choco install tux-browser
```

#### Option 5: Scoop
```powershell
scoop bucket add extras
scoop install tux-browser
```

#### Option 6: Build from Source (Developer)
```powershell
# Prerequisites (run in Administrator PowerShell)
# Install Visual Studio 2022 with "Desktop development with C++"
# Install Windows 10 SDK (10.0.19041.0+)
# Install Git, Python 3.11+, Node.js, GN, Ninja

git clone https://github.com/tuxbrowser/tux-browser.git
cd tux-browser
.\build_tux_browser.ps1 -Clean

# Run
.\chromium-main\chromium-main\out\tux_browser\chrome.exe --enable-features=TorNetworking
```

#### System Requirements (Windows)
- **OS**: Windows 10 21H2+ (19044+), Windows 11
- **Arch**: x64 (ARM64 not yet supported)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk**: 3 GB for installation
- **Visual C++ Redist**: Included in installer

---

### 🍎 macOS

#### Option 1: DMG Installer (Recommended)
1. Download `TuxBrowser-x64.dmg` (Intel) or `TuxBrowser-arm64.dmg` (Apple Silicon)
2. Open DMG and drag Tux Browser to Applications
3. **First launch**: Right-click → "Open" (bypasses Gatekeeper for unsigned builds)
4. Or: `xattr -d com.apple.quarantine /Applications/Tux\ Browser.app`

#### Option 2: Homebrew
```bash
brew tap tuxbrowser/tuxbrowser
brew install --cask tux-browser
```

#### Option 3: MacPorts
```bash
sudo port install tux-browser
```

#### Option 4: Build from Source
```bash
# Prerequisites
xcode-select --install
brew install python3 gn ninja node git

# Clone and build
git clone https://github.com/tuxbrowser/tux-browser.git
cd tux-browser
./build_tux_browser.sh --clean

# Run
./chromium-main/chromium-main/out/tux_browser/Tux\ Browser.app/Contents/MacOS/Tux\ Browser --enable-features=TorNetworking
```

#### System Requirements (macOS)
- **OS**: macOS 12 Monterey+ (Intel), macOS 13 Ventura+ (Apple Silicon)
- **Arch**: x86_64 (Intel), arm64 (Apple Silicon M1/M2/M3)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk**: 3 GB for installation
- **Note**: Notarized builds require Apple Developer Program ($99/yr)

---

## 🚀 Quick Start

### First Launch
1. **Tor Connection**: On first launch, Tux Browser connects to Tor network (10-30 seconds)
2. **Security Level**: Choose your privacy level:
   - **Standard** (Default): Balance of usability and privacy
   - **Safer**: Blocks JavaScript by default, allows on click
   - **Safest**: Maximum protection, minimal functionality
3. **Verify Connection**: Visit [check.torproject.org](https://check.torproject.org) to confirm Tor is working

### Essential Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+N` (Win/Linux) / `Cmd+Shift+N` (Mac) | New Identity (New Tor Circuit) |
| `Ctrl+Shift+T` | New Circuit for This Site |
| `Ctrl+,` | Settings |
| `Ctrl+Shift+J` | Developer Tools |

### Security Slider
Click the shield icon 🛡️ in toolbar to adjust:
- **Standard**: Most sites work, basic fingerprinting protection
- **Safer**: JS blocked by default, click to allow per-site
- **Safest**: JS/Wasm/WebGL/WebRTC blocked, only static content

---

## ⚙️ Configuration

### Tor Bridges (Censorship Circumvention)
```
Settings → Privacy & Security → Tor Bridges
```
- **obfs4**: Obfuscated bridges (recommended)
- **Snowflake**: Ephemeral WebRTC proxies
- **Conjure**: TLS-based obfuscation
- **Custom**: Enter bridge lines manually

### Per-Site Permissions
Click lock icon 🔒 in address bar to allow:
- JavaScript
- WebRTC (video calls)
- WebGL (3D graphics)
- Canvas (drawing)
- Cookies/Storage

### Onion Services
- Direct `.onion` address support
- Automatic Onion-Location header detection
- Onion indicator in address bar

---

## 🔨 Building from Source

### Prerequisites
| Platform | Dependencies |
|----------|--------------|
| **Linux** | `git python3 gn ninja-build nodejs npm clang lld` |
| **Windows** | Visual Studio 2022, Windows 10 SDK, Git, Python, Node.js, GN, Ninja |
| **macOS** | Xcode Command Line Tools, `brew install python3 gn ninja node` |

### Build Commands
```bash
# Clean build (recommended for first build)
./build_tux_browser.sh --clean

# Incremental build (faster)
./build_tux_browser.sh

# Custom output directory
./build_tux_browser.sh --out-dir=out/my_build

# Build specific target
./build_tux_browser.sh --target=chrome

# Parallel jobs (default: all cores)
./build_tux_browser.sh --jobs=8
```

### Build Output
```
chromium-main/chromium-main/out/tux_browser/
├── chrome                    # Linux binary
├── chrome.exe                # Windows binary
├── Tux Browser.app/          # macOS app bundle
├── args.gn                   # Build configuration
└── obj/                      # Intermediate files
```

### GN Build Args (Customization)
```gn
# Tux Browser branding
is_tux_browser = true
enable_tor = true
enable_tor_networking = true

# Privacy defaults
enable_google_services = false
enable_metrics_reporting = false
enable_crash_reporter = false
safe_browsing_mode = 0

# Build type
is_official_build = false
is_debug = false
symbol_level = 1
is_component_build = false
use_thin_lto = true

# Tor configuration
tor_embedded = true
tor_bridges = ["obfs4", "snowflake"]
```

---

## 🧪 Testing

### Run Test Suite
```bash
# Activate test environment
source test_env/bin/activate

# Integration tests (source files & config)
python3 test_tux_browser.py

# Rigorous attack tests
python3 tests/rigorous/run_all_tests.py

# Individual attack tests
python3 tests/rigorous/ip_attack_tests.py --proxy-host 127.0.0.1 --proxy-port 9050
python3 tests/rigorous/webrtc_attack_tests.py --browser out/tux_browser/chrome
python3 tests/rigorous/fingerprinting_attack_tests.py --browser out/tux_browser/chrome
```

### Manual Verification
```bash
# Start Tor (if not embedded)
tor -f tests/torrc &

# Launch browser with Tor
./out/tux_browser/chrome --enable-features=TorNetworking --proxy-server=socks5h://127.0.0.1:9050

# Verify at:
# - https://check.torproject.org
# - https://dnsleaktest.com
# - https://browserleaks.com/webrtc
# - https://amiunique.org
```

---

## 📁 Project Structure

```
tux-browser/
├── build_tux_browser.sh          # Linux/macOS build script
├── build_tux_browser.ps1         # Windows build script
├── tux_browser_args.gn           # GN build arguments
├── test_tux_browser.py           # Integration test
├── test_env/                     # Python test virtual environment
├── tests/
│   ├── leak_tests/               # IP/WebRTC leak tests
│   ├── rigorous/                 # Attack test suites
│   └── torrc                     # Tor configuration
├── tor-expert-bundle/            # Tor binaries & pluggable transports
├── chromium-main/
│   └── chromium-main/            # Chromium source tree
│       ├── chrome/
│       │   └── app/theme/tux/    # Tux Browser branding
│       ├── net/tor/              # Tor integration layer
│       │   ├── tor_client.h/.cc
│       │   ├── tor_proxy_resolver.h/.cc
│       │   ├── circuit_manager.h/.cc
│       │   ├── stream_isolator.h/.cc
│       │   ├── fingerprinting_protection.h/.cc
│       │   ├── content_blocker.h/.cc
│       │   └── BUILD.gn
│       └── build/config/
│           └── chrome_build.gni  # is_tux_browser flag
└── TUX_BROWSER_DESIGN.md         # Architecture documentation
```

---

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone
git clone https://github.com/yourusername/tux-browser.git
cd tux-browser

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes, test
./build_tux_browser.sh
python3 tests/rigorous/run_all_tests.py

# Submit PR
git push origin feature/amazing-feature
```

### Code Style
- Follow [Chromium C++ Style Guide](https://chromium.googlesource.com/chromium/src/+/main/styleguide/c++/c++.md)
- Use `clang-format` (config in `.clang-format`)
- Run `gn format` for GN files

### Testing Requirements
- All new features must include tests
- Run full test suite before PR
- Security features require rigorous attack testing

---

## 📄 License

Tux Browser is licensed under the **BSD 3-Clause License** - see [LICENSE](LICENSE) for details.

Chromium components retain their original licenses (BSD-style).
Tor components licensed under [Tor License](https://gitlab.torproject.org/tpo/core/tor/-/blob/main/LICENSE).

---

## 🔗 Links

- **Website**: https://tuxbrowser.org
- **Repository**: https://github.com/tuxbrowser/tux-browser
- **Releases**: https://github.com/tuxbrowser/tux-browser/releases
- **Issues**: https://github.com/tuxbrowser/tux-browser/issues
- **Documentation**: https://docs.tuxbrowser.org
- **Tor Project**: https://torproject.org

---

## ⚠️ Disclaimer

Tux Browser provides strong privacy protections but **no software can guarantee 100% anonymity**. Always:
- Use additional operational security (OpSec) practices
- Keep browser updated
- Be aware of browser fingerprinting risks
- Consider threat model appropriate for your use case

**Tux Browser is not affiliated with The Tor Project or Google/Chromium.**

---

*Built with ❤️ for privacy advocates everywhere. 🐧*