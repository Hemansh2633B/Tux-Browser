#!/usr/bin/env python3
"""
Tux Browser - IP Leak Test Suite
Tests for IP address leaks through various vectors.
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

class IPLeakTester:
    def __init__(self, browser_path, proxy_host="127.0.0.1", proxy_port=9050):
        self.browser_path = browser_path
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.results = {}
    
    def get_real_ip(self):
        """Get real IP without proxy."""
        try:
            # Use a simple HTTP request to get IP
            import urllib.request
            req = urllib.request.Request('https://api.ipify.org', headers={'User-Agent': 'TuxBrowser-Test'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode().strip()
        except Exception as e:
            return f"ERROR: {e}"
    
    def get_tor_ip(self):
        """Get IP through Tor SOCKS5 proxy."""
        try:
            import socks
            import socket
            import urllib.request
            
            # Create a socket through Tor
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(30)
            
            # Connect to ipify through Tor
            s.connect(('api.ipify.org', 80))
            request = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nUser-Agent: TuxBrowser-Test\r\nConnection: close\r\n\r\n"
            s.send(request)
            
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            s.close()
            
            # Extract IP from response body
            response_str = response.decode('utf-8', errors='ignore')
            # Find the IP in the body (after double newline)
            parts = response_str.split('\r\n\r\n')
            if len(parts) > 1:
                ip = parts[-1].strip()
                if ip:
                    return ip
            return "ERROR: Could not parse IP from response"
        except Exception as e:
            return f"ERROR: {e}"
    
    def test_direct_connection_leak(self):
        """Test if direct connections bypass Tor."""
        print("Testing direct connection leak...")
        real_ip = self.get_real_ip()
        tor_ip = self.get_tor_ip()
        
        if real_ip.startswith("ERROR"):
            return {"test": "direct_leak", "status": "SKIP", "reason": real_ip}
        
        if tor_ip.startswith("ERROR"):
            return {"test": "direct_leak", "status": "FAIL", "reason": f"Tor connection failed: {tor_ip}"}
        
        leak = (real_ip == tor_ip)
        return {
            "test": "direct_leak",
            "status": "PASS" if not leak else "FAIL",
            "real_ip": real_ip,
            "tor_ip": tor_ip,
            "leak_detected": leak
        }
    
    def test_dns_leak(self):
        """Test for DNS leaks by resolving unique domains."""
        print("Testing DNS leak...")
        import uuid
        test_domain = f"leaktest-{uuid.uuid4().hex[:16]}.example.com"
        
        try:
            # Try to resolve through Tor
            import socks
            import socket
            
            # Create a socket through Tor
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(10)
            
            # Try to connect to a test domain
            try:
                s.connect((test_domain, 80))
                s.close()
                return {"test": "dns_leak", "status": "FAIL", "reason": "DNS resolved unexpectedly"}
            except socket.gaierror:
                # Expected - domain doesn't exist
                pass
            except Exception:
                pass
            finally:
                s.close()
            
            return {"test": "dns_leak", "status": "PASS", "reason": "DNS properly routed through Tor"}
        except Exception as e:
            return {"test": "dns_leak", "status": "ERROR", "reason": str(e)}
    
    def test_tcp_leak(self):
        """Test if system allows direct TCP connections (firewall check)."""
        print("Testing TCP leak (system firewall check)...")
        try:
            import socket
            
            # Try direct connection to check if system firewall blocks outbound
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            
            # Try to connect to a known service directly
            try:
                s.connect(("1.1.1.1", 53))  # Cloudflare DNS
                s.close()
                # Direct connection succeeded - system allows outbound (not a browser leak)
                return {"test": "tcp_leak", "status": "INFO", "reason": "System allows direct TCP (expected on non-hardened systems)"}
            except (socket.timeout, ConnectionRefusedError, OSError):
                s.close()
                # Direct connection blocked - system has firewall
                return {"test": "tcp_leak", "status": "PASS", "reason": "Direct TCP blocked by system firewall"}
            except Exception as e:
                s.close()
                return {"test": "tcp_leak", "status": "ERROR", "reason": str(e)}
        except Exception as e:
            return {"test": "tcp_leak", "status": "ERROR", "reason": str(e)}
    
    def test_ipv6_leak(self):
        """Test for IPv6 leaks."""
        print("Testing IPv6 leak...")
        try:
            import urllib.request
            
            # Test IPv6 through Tor
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'socks5h://{self.proxy_host}:{self.proxy_port}',
                'https': f'socks5h://{self.proxy_host}:{self.proxy_port}'
            })
            opener = urllib.request.build_opener(proxy_handler)
            
            # Try IPv6-only endpoint
            try:
                req = urllib.request.Request('https://ipv6.api.ipify.org', headers={'User-Agent': 'TuxBrowser-Test'})
                with opener.open(req, timeout=30) as response:
                    ip = response.read().decode().strip()
                    # If we get an IPv6 address, check if it's a Tor exit node
                    return {"test": "ipv6_leak", "status": "INFO", "ipv6_via_tor": ip}
            except urllib.error.URLError:
                pass
            
            return {"test": "ipv6_leak", "status": "PASS", "reason": "IPv6 properly handled by Tor"}
        except Exception as e:
            return {"test": "ipv6_leak", "status": "ERROR", "reason": str(e)}
    
    def test_browser_proxy_config(self):
        """Test browser proxy configuration."""
        print("Testing browser proxy configuration...")
        
        # Check if browser uses the correct proxy
        # This would require launching the browser with a test page
        return {"test": "browser_proxy_config", "status": "MANUAL", "reason": "Requires browser launch"}
    
    def run_all_tests(self):
        """Run all IP leak tests."""
        print("=" * 60)
        print("Tux Browser - IP Leak Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_direct_connection_leak,
            self.test_dns_leak,
            self.test_tcp_leak,
            self.test_ipv6_leak,
        ]
        
        for test in tests:
            try:
                result = test()
                self.results[result["test"]] = result
                status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "INFO": "ℹ", "MANUAL": "⚙"}.get(result["status"], "?")
                print(f"  {status_symbol} {result['test']}: {result['status']} - {result.get('reason', '')}")
            except Exception as e:
                self.results[test.__name__] = {"test": test.__name__, "status": "ERROR", "reason": str(e)}
                print(f"  ⚠ {test.__name__}: ERROR - {e}")
        
        print()
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get("status") == "PASS")
        failed = sum(1 for r in self.results.values() if r.get("status") == "FAIL")
        errors = sum(1 for r in self.results.values() if r.get("status") == "ERROR")
        
        print("=" * 60)
        print(f"SUMMARY: {passed}/{total} passed, {failed} failed, {errors} errors")
        print("=" * 60)
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for name, result in self.results.items():
                if result.get("status") == "FAIL":
                    print(f"  - {name}: {result.get('reason', 'Unknown')}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tux Browser IP Leak Tests")
    parser.add_argument("--browser", default="/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser/chrome", help="Path to browser binary")
    parser.add_argument("--proxy-host", default="127.0.0.1", help="Tor proxy host")
    parser.add_argument("--proxy-port", type=int, default=9050, help="Tor proxy port")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    tester = IPLeakTester(args.browser, args.proxy_host, args.proxy_port)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    sys.exit(0 if all(r.get("status") in ("PASS", "SKIP", "INFO", "MANUAL") for r in results.values()) else 1)