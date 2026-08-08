# Tux Browser - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete Tor integration in `//net/tor/` directory
- Embedded Tor process management
- Circuit isolation per origin (First-Party Isolation)
- Stream isolation for different security contexts
- Onion service (.onion) direct support
- Pluggable transports: obfs4, Snowflake, Conjure, meek, webtunnel
- 3-level fingerprinting protection (Standard/Safer/Safest)
- NoScript-like content blocking with per-site exceptions
- 13 fingerprinting vectors blocked in Safest mode
- WebRTC blocked in all security levels
- Branding: "Tux Browser" product name, org.tuxbrowser.TuxBrowser bundle ID
- Comprehensive test suites: IP leak, WebRTC leak, fingerprinting attacks
- Cross-platform build scripts (Linux/macOS/Windows)
- Platform-specific installers (Linux/Windows/macOS)
- AppImage, DEB, RPM, Flatpak, DMG, NSIS installer support

### Security
- All traffic forced through Tor SOCKS5 proxy (socks5h://127.0.0.1:9050)
- DNS leak protection via Tor remote DNS resolution
- HTTP Host/Referrer header leak prevention
- ETag/cache tracking protection
- Hardware concurrency/device memory masking
- Timezone/language standardization (UTC, en-US)
- Battery API, Sensor API, Media Devices blocking
- Performance/Resource timing randomization
- ClientRects protection

### Testing
- Rigorous IP leak attack tests (10 test vectors)
- WebRTC leak attack tests (8 test vectors + code verification)
- Fingerprinting attack tests (15 test vectors + code verification)
- Master test runner with JSON reporting
- All tests run in isolated Python virtual environment

## [0.1.0] - 2024-08-08

### Added
- Initial project structure
- Chromium source tree integration
- Tor Expert Bundle integration
- Basic branding and build configuration
- Design documentation

---

## Release Types

- **Major**: Breaking changes, significant architecture changes
- **Minor**: New features, significant improvements (backward compatible)
- **Patch**: Bug fixes, security patches (backward compatible)

## Version Numbering

```
MAJOR.MINOR.PATCH[-PRERELEASE]

Examples:
  1.0.0       - First stable release
  1.1.0       - New features
  1.1.1       - Bug fix
  2.0.0-beta  - Beta release with breaking changes
  1.2.0-rc1   - Release candidate
```

## Support Policy

| Version | Status | Supported Until |
|---------|--------|-----------------|
| 1.x     | Active | 2026-08-08      |
| 0.x     | EOL    | 2024-08-08      |

---

*For detailed commit history, see `git log --oneline --graph --all`*