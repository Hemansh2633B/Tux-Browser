# Contributing to Tux Browser

Thank you for your interest in contributing to Tux Browser! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch Linux
- **Windows**: Windows 10/11, Visual Studio 2022, Windows 10 SDK
- **macOS**: macOS 12+, Xcode Command Line Tools

### Development Setup

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/tux-browser.git
cd tux-browser

# Add upstream remote
git remote add upstream https://github.com/tuxbrowser/tux-browser.git

# Create feature branch
git checkout -b feature/your-feature-name

# Install build dependencies (Linux)
sudo apt install git python3 gn ninja-build nodejs npm clang lld

# Build
./build_tux_browser.sh --clean
```

## Development Workflow

### 1. Making Changes

- Create a new branch for each feature/fix
- Follow Chromium's C++ style guide
- Write tests for new functionality
- Update documentation as needed

### 2. Code Style

- **C++**: Follow [Chromium C++ Style Guide](https://chromium.googlesource.com/chromium/src/+/main/styleguide/c++/c++.md)
- **Python**: Follow PEP 8 (use `black` formatter)
- **GN**: Use `gn format` for build files
- **Markdown**: Use consistent formatting

### 3. Testing

Run the full test suite before submitting:

```bash
# Activate test environment
source test_env/bin/activate

# Integration tests
python3 test_tux_browser.py

# Rigorous attack tests
python3 tests/rigorous/run_all_tests.py

# Build verification
./build_tux_browser.sh  # Incremental build
```

### 4. Commit Messages

Follow conventional commit format:

```
type(scope): brief description

Detailed explanation if needed.

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(tor): add Snowflake bridge support
fix(fingerprinting): prevent canvas leak in Safest mode
docs(readme): update Windows installation instructions
test(ip-leak): add DNS leak test for multiple domains
```

### 5. Pull Request Process

1. Ensure all tests pass
2. Update CHANGELOG.md with your changes
3. Request review from maintainers
4. Address review comments
5. Squash commits if requested
6. Merge after approval

## Areas for Contribution

### High Priority
- **Tor Integration**: Circuit management, stream isolation
- **Fingerprinting Resistance**: Canvas, WebGL, AudioContext protection
- **Content Blocking**: NoScript-like per-site controls
- **Pluggable Transports**: obfs4, Snowflake, Conjure integration
- **UI/UX**: Security slider, circuit display, onion indicator

### Medium Priority
- **Build System**: GN args, cross-platform builds
- **Installers**: Linux packages, Windows installer, macOS DMG
- **Testing**: Automated leak tests, fingerprinting verification
- **Documentation**: User guides, developer docs

### Good First Issues
- Fix typos in documentation
- Add test cases for existing features
- Improve error messages
- Update dependencies

## Security

### Reporting Vulnerabilities

**Do not** report security vulnerabilities via public issues.

Email: security@tuxbrowser.org

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Security Review

All changes to security-critical code require:
- Security review by maintainers
- Additional testing
- Threat model consideration

## Project Structure

```
tux-browser/
├── build_tux_browser.sh          # Build script
├── tux_browser_args.gn           # GN arguments
├── test_tux_browser.py           # Integration tests
├── tests/
│   ├── leak_tests/               # IP/WebRTC leak tests
│   ├── rigorous/                 # Attack test suites
│   └── torrc                     # Tor configuration
├── chromium-main/
│   └── chromium-main/
│       ├── chrome/app/theme/tux/ # Branding
│       ├── net/tor/              # Tor integration
│       └── build/config/         # Build flags
└── install_*.sh/ps1              # Platform installers
```

## Tor Integration Development

When working on Tor integration:

1. **Test with real Tor**: Use `tor -f tests/torrc`
2. **Verify leaks**: Run IP/WebRTC leak tests
3. **Check circuits**: Use control port (9051) to verify isolation
4. **Test bridges**: Configure obfs4/Snowflake in torrc

## Fingerprinting Protection

When adding fingerprinting protections:

1. **Implement in `fingerprinting_protection.cc`**: JavaScript injection
2. **Add content blocking in `content_blocker.cc`**: Per-security-level
3. **Test thoroughly**: Use amiunique.org, panopticlick.eff.org
4. **Verify all levels**: Standard, Safer, Safest

## Building for Distribution

### Linux
```bash
./build_tux_browser.sh --clean
./install_linux.sh --prefix=/opt/tux-browser
# Create AppImage, DEB, RPM
```

### Windows
```powershell
.\build_tux_browser.ps1 -Clean
.\install_windows.ps1
# Create NSIS installer
```

### macOS
```bash
./build_tux_browser.sh --clean
./install_macos.sh --dmg
# Notarize with Apple
```

## Communication

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Discord**: Real-time chat (invite in repo)
- **Mailing List**: tuxbrowser-dev@googlegroups.com

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- About dialog in browser

## License

By contributing, you agree that your contributions will be licensed under the BSD 3-Clause License (see LICENSE).

---

**Thank you for contributing to Tux Browser!** 🐧