# Tux Browser Design Document

## Overview
Tux Browser is a privacy-focused browser built on Chromium with integrated Tor network security layers. The browser routes all traffic through the Tor network while maintaining Chromium's performance and compatibility.

## Architecture

### Integration Approach: "Chromium + Embedded Tor"

Instead of the traditional Tor Browser approach (modified Firefox + external Tor process), Tux Browser embeds Tor directly into Chromium's network stack:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Tux Browser                              │
├─────────────────────────────────────────────────────────────────┤
│  Chromium UI Layer (tabs, bookmarks, settings, extensions)     │
├─────────────────────────────────────────────────────────────────┤
│  Content Layer (Blink renderer, V8, Web APIs)                  │
├─────────────────────────────────────────────────────────────────┤
│  Network Layer (Modified //net stack)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tor Integration Layer                                   │   │
│  │  - SOCKS5 proxy to embedded Tor process                 │   │
│  │  - Circuit isolation per origin (First-Party Isolation)│   │
│  │  - Stream isolation for different security contexts    │   │
│  │  - Onion service (.onion) direct support               │   │
│  │  - Pluggable transports (obfs4, snowflake, conjure)    │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Embedded Tor Process (libtor)                                 │
│  - Circuit management                                           │
│  - Onion routing                                                │
│  - Directory authorities                                        │
│  - Bridge support                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Tor Network Integration (`//net/tor/`)
New directory in Chromium's net stack for Tor-specific code:

```
net/tor/
├── tor_client.h/.cc           # Embedded Tor client wrapper
├── tor_proxy_resolver.h/.cc   # Custom proxy resolver for Tor
├── circuit_manager.h/.cc      # Circuit isolation per origin
├── stream_isolator.h/.cc      # Stream isolation logic
├── onion_resolver.h/.cc       # .onion address resolution
├── pluggable_transport.h/.cc  # Transport plugin management
└── tor_network_delegate.h/.cc # Network delegate for Tor events
```

### 2. Proxy Configuration
- Default proxy: `socks5h://127.0.0.1:9050` (Tor SOCKS5 with remote DNS)
- All traffic forced through Tor proxy (no bypass)
- Separate SOCKS ports for different isolation contexts:
  - Port 9050: General browsing
  - Port 9051: Control port (for circuit management)
  - Port 9150: Isolated contexts (different circuit per origin)

### 3. Circuit Isolation (First-Party Isolation)
Each top-level origin gets its own Tor circuit:
- `example.com` → Circuit A
- `tracker.com` (embedded in example.com) → Circuit B
- Prevents correlation attacks

### 4. Stream Isolation
Different security contexts use different streams:
- Normal browsing
- Private/Incognito mode
- Onion service connections
- Bridge connections

### 5. Pluggable Transports
Support for censorship circumvention:
- obfs4
- snowflake
- conjure (from tor-browser)
- meek
- webtunnel

## Branding Changes

### Product Names
- `PRODUCT_FULLNAME` = "Tux Browser"
- `PRODUCT_SHORTNAME` = "Tux Browser"
- `PRODUCT_INSTALLER_FULLNAME` = "Tux Browser Installer"
- `PRODUCT_INSTALLER_SHORTNAME` = "Tux Browser Installer"

### Visual Identity
- New product logo (tux penguin theme)
- Custom theme colors (dark mode default)
- Modified chrome:// URLs to tux:// (optional)

### MAC Bundle ID
- `org.tuxbrowser.TuxBrowser`

## Security Features

### 1. Fingerprinting Resistance
- Canvas fingerprinting protection
- WebGL fingerprinting protection
- AudioContext fingerprinting protection
- Client rects protection
- Font enumeration protection
- Hardware concurrency masking
- Battery status API blocking

### 2. NoScript-like Content Blocking
- JavaScript blocking by default (configurable per-site)
- WebAssembly blocking
- WebRTC blocking (prevents IP leaks)
- WebGL blocking
- Canvas API blocking

### 3. Privacy Enhancements
- No telemetry/metrics
- No crash reporting to Google
- No safe browsing (or use local lists)
- No network prediction/prefetch
- No DNS prefetching
- No autocomplete suggestions
- No password manager (or encrypted local only)
- Automatic HTTPS enforcement
- Referrer policy: strict-origin-when-cross-origin

### 4. Tor-Specific
- New identity (new circuit) button
- New circuit for this site
- Security slider (Standard/Safer/Safest)
- Onion service detection UI
- Circuit display UI

## Build Configuration

### GN Args
```gn
# Tux Browser specific
is_tux_browser = true
tux_browser_enable_tor = true
tux_browser_embed_tor = true
tux_browser_branding = "tux"

# Disable Google services
enable_google_services = false
enable_chrome_extensions = true
enable_widevine = false
proprietary_codecs = false
ffmpeg_branding = "Chrome"

# Privacy
enable_metrics_reporting = false
enable_crash_reporter = false
safe_browsing_mode = 0
```

### New GN Targets
- `//chrome:tux_browser` - Main browser target
- `//net/tor:tor_client` - Embedded Tor library
- `//chrome/installer:tux_browser_installer` - Installer

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
1. Create `//net/tor/` directory structure
2. Implement Tor process launcher/manager
3. Basic SOCKS5 proxy configuration
4. Branding changes (product names, logos)

### Phase 2: Network Integration (Week 3-4)
1. Custom proxy resolver for Tor
2. Circuit isolation per origin
3. Stream isolation
4. .onion address resolution

### Phase 3: Privacy Features (Week 5-6)
1. Fingerprinting resistance
2. Content blocking (JS, WebRTC, etc.)
3. Security slider UI
4. Circuit display UI

### Phase 4: Pluggable Transports (Week 7-8)
1. obfs4 integration
2. Snowflake integration
3. Conjure integration
4. Bridge configuration UI

### Phase 5: Testing & Hardening (Week 9-10)
1. Leak testing (DNS, WebRTC, IP)
2. Fingerprinting test (panopticlick, amiunique)
3. Performance optimization
4. Security audit

## Tor Process Management

### Embedded Tor (Preferred)
- Link against libtor (if available as library)
- Or spawn tor binary as child process
- Manage lifecycle (start/stop/restart)
- Control port communication for circuit management

### External Tor (Fallback)
- Use system tor if available
- Connect via control port (9051)
- Less integrated but easier to develop

## Configuration Files

### torrc (Generated at Runtime)
```
# Tux Browser Tor Configuration
SOCKSPort 9050
ControlPort 9051
CookieAuthentication 1
DataDirectory <profile>/tor
Log notice stdout
AvoidDiskWrites 1
ClientTransportPlugin obfs4 exec <path>/obfs4proxy
ClientTransportPlugin snowflake exec <path>/snowflake-client
ClientTransportPlugin conjure exec <path>/conjure-client
```

### Preferences (tux://settings/privacy)
```json
{
  "tor.enabled": true,
  "tor.security_level": "standard",
  "tor.bridges": [],
  "tor.pluggable_transports": ["obfs4", "snowflake"],
  "privacy.fingerprinting_resistance": true,
  "privacy.block_javascript": true,
  "privacy.block_webrtc": true,
  "privacy.block_webgl": false,
  "privacy.https_only": true
}
```

## Testing Strategy

### Automated Tests
- Net stack unit tests for Tor integration
- Proxy resolver tests
- Circuit isolation tests
- Onion resolution tests

### Integration Tests
- Full browser launch with Tor
- Traffic verification (all via Tor)
- Leak tests (DNS, WebRTC, IPv6)
- Fingerprinting resistance verification

### Manual Testing
- Tor Project's check.torproject.org
- IP leak tests
- Onion service access
- Bridge connectivity
- Performance benchmarks

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tor binary size | Use embedded libtor or minimal tor build |
| Performance | Circuit reuse, connection pooling |
| Compatibility | Security slider for progressive enhancement |
| Updates | Separate Tor component updates |
| Legal | Clear disclaimer, no logging policy |

## Future Enhancements

1. **Arti Integration** - Rust Tor implementation (when stable)
2. **Onion-Location Header** - Auto-redirect to .onion
3. **Tor Browser Parity** - Match all TB security features
4. **Mobile Support** - Android/iOS ports
5. **Enterprise Policy** - Group policy for Tor settings

## References

- Tor Browser Design: https://tb-manual.torproject.org/design/
- Chromium Network Stack: https://www.chromium.org/developers/design-documents/network-stack
- Tor Specifications: https://spec.torproject.org/
- Pluggable Transports: https://github.com/pluggable-transports