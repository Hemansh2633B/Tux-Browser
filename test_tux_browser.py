#!/usr/bin/env python3
# Tux Browser Integration Test
# 
# This script verifies that the Tux Browser Tor integration is properly configured.

import os
import sys
import subprocess
import json

CHROMIUM_SRC = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main"
OUT_DIR = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser"

def check_file_exists(path, description):
    """Check if a file exists."""
    full_path = os.path.join(CHROMIUM_SRC, path)
    if os.path.exists(full_path):
        print(f"  ✓ {description}: {path}")
        return True
    else:
        print(f"  ✗ {description}: {path} (NOT FOUND)")
        return False

def check_build_args():
    """Check if build args are configured correctly."""
    args_file = os.path.join(OUT_DIR, "args.gn")
    if not os.path.exists(args_file):
        print(f"  ✗ Build args file not found: {args_file}")
        return False
    
    with open(args_file, 'r') as f:
        content = f.read()
    
    required_args = [
        "is_tux_browser = true",
        "enable_tor = true",
        "enable_tor_networking = true",
        "enable_google_services = false",
        "enable_metrics_reporting = false",
        "enable_crash_reporter = false",
    ]
    
    all_found = True
    for arg in required_args:
        if arg in content:
            print(f"  ✓ Build arg: {arg}")
        else:
            print(f"  ✗ Build arg missing: {arg}")
            all_found = False
    
    return all_found

def check_tor_source_files():
    """Check if all Tor source files exist."""
    files = [
        ("net/tor/tor_client.h", "Tor Client Header"),
        ("net/tor/tor_client.cc", "Tor Client Implementation"),
        ("net/tor/tor_proxy_resolver.h", "Tor Proxy Resolver Header"),
        ("net/tor/tor_proxy_resolver.cc", "Tor Proxy Resolver Implementation"),
        ("net/tor/circuit_manager.h", "Circuit Manager Header"),
        ("net/tor/circuit_manager.cc", "Circuit Manager Implementation"),
        ("net/tor/stream_isolator.h", "Stream Isolator Header"),
        ("net/tor/stream_isolator.cc", "Stream Isolator Implementation"),
        ("net/tor/fingerprinting_protection.h", "Fingerprinting Protection Header"),
        ("net/tor/fingerprinting_protection.cc", "Fingerprinting Protection Implementation"),
        ("net/tor/content_blocker.h", "Content Blocker Header"),
        ("net/tor/content_blocker.cc", "Content Blocker Implementation"),
        ("net/tor/BUILD.gn", "Tor BUILD.gn"),
    ]
    
    all_found = True
    for path, desc in files:
        if not check_file_exists(path, desc):
            all_found = False
    
    return all_found

def check_branding():
    """Check if branding is updated."""
    branding_file = os.path.join(CHROMIUM_SRC, "chrome/app/theme/chromium/BRANDING")
    if not os.path.exists(branding_file):
        print(f"  ✗ Branding file not found: {branding_file}")
        return False
    
    with open(branding_file, 'r') as f:
        content = f.read()
    
    required_branding = [
        "PRODUCT_FULLNAME=Tux Browser",
        "PRODUCT_SHORTNAME=Tux Browser",
        "COMPANY_FULLNAME=The Tux Browser Authors",
        "MAC_BUNDLE_ID=org.tuxbrowser.TuxBrowser",
    ]
    
    all_found = True
    for brand in required_branding:
        if brand in content:
            print(f"  ✓ Branding: {brand}")
        else:
            print(f"  ✗ Branding missing: {brand}")
            all_found = False
    
    # Check tux theme directory
    tux_branding = os.path.join(CHROMIUM_SRC, "chrome/app/theme/tux/BRANDING")
    if os.path.exists(tux_branding):
        print(f"  ✓ Tux theme directory exists")
    else:
        print(f"  ✗ Tux theme directory missing")
        all_found = False
    
    return all_found

def check_build_config():
    """Check if build configuration includes Tor."""
    chrome_build = os.path.join(CHROMIUM_SRC, "build/config/chrome_build.gni")
    if not os.path.exists(chrome_build):
        print(f"  ✗ chrome_build.gni not found")
        return False
    
    with open(chrome_build, 'r') as f:
        content = f.read()
    
    required_config = [
        "is_tux_browser = false",
        "branding_path_component = \"tux\"",
        "branding_path_product = \"tux\"",
    ]
    
    all_found = True
    for config in required_config:
        if config in content:
            print(f"  ✓ Build config: {config}")
        else:
            print(f"  ✗ Build config missing: {config}")
            all_found = False
    
    return all_found

def check_net_features():
    """Check if net/features.gni includes Tor flag."""
    net_features = os.path.join(CHROMIUM_SRC, "net/features.gni")
    if not os.path.exists(net_features):
        print(f"  ✗ net/features.gni not found")
        return False
    
    with open(net_features, 'r') as f:
        content = f.read()
    
    if "enable_tor_networking = is_tux_browser" in content:
        print(f"  ✓ Tor networking flag in net/features.gni")
        return True
    else:
        print(f"  ✗ Tor networking flag missing from net/features.gni")
        return False

def check_net_build():
    """Check if net/BUILD.gn includes Tor sources."""
    net_build = os.path.join(CHROMIUM_SRC, "net/BUILD.gn")
    if not os.path.exists(net_build):
        print(f"  ✗ net/BUILD.gn not found")
        return False
    
    with open(net_build, 'r') as f:
        content = f.read()
    
    required_includes = [
        "tor/tor_client.cc",
        "tor/tor_client.h",
        "tor/tor_proxy_resolver.cc",
        "tor/tor_proxy_resolver.h",
        ":tor",
    ]
    
    all_found = True
    for include in required_includes:
        if include in content:
            print(f"  ✓ Net BUILD includes: {include}")
        else:
            print(f"  ✗ Net BUILD missing: {include}")
            all_found = False
    
    return all_found

def run_gn_check():
    """Run gn check to verify build configuration."""
    try:
        result = subprocess.run(
            ["gn", "check", OUT_DIR, "//net/tor:tor"],
            capture_output=True,
            text=True,
            cwd=CHROMIUM_SRC,
            timeout=60
        )
        if result.returncode == 0:
            print(f"  ✓ GN check passed for //net/tor:tor")
            return True
        else:
            print(f"  ✗ GN check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ GN check timed out")
        return False
    except FileNotFoundError:
        print(f"  ⚠ GN not found, skipping check")
        return True
    except Exception as e:
        print(f"  ✗ GN check error: {e}")
        return False

def main():
    print("==========================================")
    print("Tux Browser Integration Test")
    print("==========================================")
    print("")
    
    all_passed = True
    
    print("Checking Tor source files...")
    if not check_tor_source_files():
        all_passed = False
    print("")
    
    print("Checking branding...")
    if not check_branding():
        all_passed = False
    print("")
    
    print("Checking build configuration...")
    if not check_build_config():
        all_passed = False
    print("")
    
    print("Checking net/features.gni...")
    if not check_net_features():
        all_passed = False
    print("")
    
    print("Checking net/BUILD.gn...")
    if not check_net_build():
        all_passed = False
    print("")
    
    print("Checking build args...")
    if not check_build_args():
        all_passed = False
    print("")
    
    print("Running GN check...")
    if not run_gn_check():
        all_passed = False
    print("")
    
    print("==========================================")
    if all_passed:
        print("ALL TESTS PASSED! ✓")
        print("==========================================")
        return 0
    else:
        print("SOME TESTS FAILED! ✗")
        print("==========================================")
        return 1

if __name__ == "__main__":
    sys.exit(main())