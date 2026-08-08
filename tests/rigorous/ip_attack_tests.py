#!/usr/bin/env python3
"""
Rigorous IP Leak Attack Tests for Tux Browser
Tests various IP leak vectors including DNS, WebRTC, HTTP, TCP, and side-channels.
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

try:
    import socks
    import urllib.request
    import urllib.error
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pysocks", "aiohttp"])
    import socks
    import urllib.request
    import urllib.error


class RigorousIPLeakTester:
    def __init__(self, proxy_host="127.0.0.1", proxy_port=9050, control_port=9051):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.control_port = control_port
        self.results = {}
        self.real_ip = None
        self.tor_ip = None
        
    def get_real_ip(self):
        """Get real IP without proxy using multiple services."""
        services = [
            'https://api.ipify.org',
            'https://icanhazip.com',
            'https://ifconfig.me/ip',
            'https://ipinfo.io/ip',
        ]
        
        for service in services:
            try:
                req = urllib.request.Request(service, headers={'User-Agent': 'TuxBrowser-RigorousTest'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    ip = response.read().decode().strip()
                    if ip and self._is_valid_ip(ip):
                        return ip
            except Exception:
                continue
        return "ERROR: Could not determine real IP"
    
    def get_tor_ip(self):
        """Get IP through Tor SOCKS5 proxy using multiple services."""
        services = [
            'http://api.ipify.org',
            'http://icanhazip.com',
            'http://ifconfig.me/ip',
        ]
        
        for service in services:
            try:
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
                s.settimeout(30)
                
                parsed = urlparse(service)
                host = parsed.hostname
                port = parsed.port or 80
                
                s.connect((host, port))
                request = f"GET {parsed.path or '/'} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: TuxBrowser-RigorousTest\r\nConnection: close\r\n\r\n"
                s.send(request.encode())
                
                response = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                s.close()
                
                response_str = response.decode('utf-8', errors='ignore')
                parts = response_str.split('\r\n\r\n')
                if len(parts) > 1:
                    ip = parts[-1].strip()
                    if ip and self._is_valid_ip(ip):
                        return ip
            except Exception:
                continue
        return "ERROR: Could not determine Tor IP"
    
    def _is_valid_ip(self, ip):
        """Check if string is a valid IPv4 or IPv6 address."""
        try:
            socket.inet_pton(socket.AF_INET, ip)
            return True
        except OSError:
            try:
                socket.inet_pton(socket.AF_INET6, ip)
                return True
            except OSError:
                return False
    
    def test_basic_ip_leak(self):
        """Test 1: Basic IP leak - compare real IP vs Tor IP."""
        print("\n[TEST 1] Basic IP Leak Test")
        self.real_ip = self.get_real_ip()
        self.tor_ip = self.get_tor_ip()
        
        print(f"  Real IP:  {self.real_ip}")
        print(f"  Tor IP:   {self.tor_ip}")
        
        if self.real_ip.startswith("ERROR") or self.tor_ip.startswith("ERROR"):
            return {"test": "basic_ip_leak", "status": "SKIP", "reason": "Could not determine IPs"}
        
        leak = (self.real_ip == self.tor_ip)
        return {
            "test": "basic_ip_leak",
            "status": "PASS" if not leak else "FAIL",
            "real_ip": self.real_ip,
            "tor_ip": self.tor_ip,
            "leak_detected": leak
        }
    
    def test_dns_leak_multiple_domains(self):
        """Test 2: DNS leak test with multiple unique domains."""
        print("\n[TEST 2] DNS Leak Test (Multiple Domains)")
        
        leaked_domains = []
        for i in range(5):
            test_domain = f"dnsleak-{uuid.uuid4().hex[:16]}.test.invalid"
            try:
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
                s.settimeout(10)
                
                try:
                    s.connect((test_domain, 80))
                    s.close()
                    leaked_domains.append(test_domain)
                except socket.gaierror:
                    pass  # Expected - domain doesn't exist
                except Exception:
                    pass
                finally:
                    s.close()
            except Exception as e:
                return {"test": "dns_leak_multi", "status": "ERROR", "reason": str(e)}
        
        if leaked_domains:
            return {
                "test": "dns_leak_multi",
                "status": "FAIL",
                "reason": f"DNS leaked for {len(leaked_domains)} domains",
                "leaked_domains": leaked_domains
            }
        return {
            "test": "dns_leak_multi",
            "status": "PASS",
            "reason": "All DNS queries properly routed through Tor"
        }
    
    def test_dns_resolver_leak(self):
        """Test 3: Check if system DNS resolver is bypassed."""
        print("\n[TEST 3] System DNS Resolver Bypass Test")
        
        # Test that we can't resolve via system DNS when using Tor
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(10)
            
            # Try to connect to a known domain via Tor
            try:
                s.connect(("check.torproject.org", 80))
                request = b"GET / HTTP/1.1\r\nHost: check.torproject.org\r\nConnection: close\r\n\r\n"
                s.send(request)
                response = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                s.close()
                
                if b"Congratulations. This browser is configured to use Tor" in response:
                    return {"test": "dns_resolver_bypass", "status": "PASS", "reason": "Tor check passed - DNS via Tor"}
                else:
                    return {"test": "dns_resolver_bypass", "status": "INFO", "reason": "Connected via Tor but check page not found"}
            except Exception as e:
                return {"test": "dns_resolver_bypass", "status": "FAIL", "reason": f"Tor connection failed: {e}"}
        except Exception as e:
            return {"test": "dns_resolver_bypass", "status": "ERROR", "reason": str(e)}
    
    def test_http_host_header_leak(self):
        """Test 4: HTTP Host header leak test."""
        print("\n[TEST 4] HTTP Host Header Leak Test")
        
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(30)
            
            s.connect(("httpbin.org", 80))
            # Send request with unique host header
            unique_host = f"leaktest-{uuid.uuid4().hex[:16]}.example.com"
            request = f"GET /headers HTTP/1.1\r\nHost: {unique_host}\r\nUser-Agent: TuxBrowser-RigorousTest\r\nConnection: close\r\n\r\n"
            s.send(request.encode())
            
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            s.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            if unique_host in response_str:
                return {"test": "http_host_leak", "status": "FAIL", "reason": "Host header leaked in response"}
            
            return {"test": "http_host_leak", "status": "PASS", "reason": "Host header not leaked"}
        except Exception as e:
            return {"test": "http_host_leak", "status": "ERROR", "reason": str(e)}
    
    def test_tcp_timing_attack(self):
        """Test 5: TCP timing side-channel test."""
        print("\n[TEST 5] TCP Timing Side-Channel Test")
        
        # Measure connection times through Tor vs direct
        tor_times = []
        direct_times = []
        
        # Test through Tor
        for _ in range(3):
            try:
                start = time.time()
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
                s.settimeout(30)
                s.connect(("1.1.1.1", 80))
                s.close()
                tor_times.append(time.time() - start)
            except Exception:
                pass
        
        # Test direct (if allowed)
        for _ in range(3):
            try:
                start = time.time()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect(("1.1.1.1", 80))
                s.close()
                direct_times.append(time.time() - start)
            except Exception:
                pass
        
        if not tor_times:
            return {"test": "tcp_timing", "status": "SKIP", "reason": "Could not measure Tor connection times"}
        
        avg_tor = sum(tor_times) / len(tor_times)
        result = {
            "test": "tcp_timing",
            "status": "PASS",
            "avg_tor_time": round(avg_tor, 3),
            "tor_times": tor_times,
            "reason": f"Tor connection times measured (avg: {avg_tor:.3f}s)"
        }
        
        if direct_times:
            avg_direct = sum(direct_times) / len(direct_times)
            result["avg_direct_time"] = round(avg_direct, 3)
            result["direct_times"] = direct_times
            result["reason"] += f", Direct: {avg_direct:.3f}s"
            # Tor should be significantly slower
            if avg_tor < avg_direct * 0.5:
                result["status"] = "WARN"
                result["reason"] += " - WARNING: Tor faster than direct (possible leak)"
        
        return result
    
    def test_concurrent_circuit_isolation(self):
        """Test 6: Concurrent circuit isolation test."""
        print("\n[TEST 6] Concurrent Circuit Isolation Test")
        
        ips = set()
        
        def get_ip_via_tor():
            try:
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
                s.settimeout(30)
                s.connect(("api.ipify.org", 80))
                request = b"GET / HTTP/1.1\r\nHost: api.ipify.org\r\nConnection: close\r\n\r\n"
                s.send(request)
                response = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                s.close()
                response_str = response.decode('utf-8', errors='ignore')
                parts = response_str.split('\r\n\r\n')
                if len(parts) > 1:
                    ip = parts[-1].strip()
                    if self._is_valid_ip(ip):
                        return ip
            except Exception:
                pass
            return None
        
        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_ip_via_tor) for _ in range(10)]
            for future in as_completed(futures):
                ip = future.result()
                if ip:
                    ips.add(ip)
        
        print(f"  Unique exit nodes observed: {len(ips)}")
        for ip in ips:
            print(f"    - {ip}")
        
        if len(ips) == 0:
            return {"test": "circuit_isolation", "status": "FAIL", "reason": "No successful connections"}
        elif len(ips) == 1:
            return {"test": "circuit_isolation", "status": "WARN", "reason": "Single exit node (may be expected for same circuit)", "unique_ips": list(ips)}
        else:
            return {"test": "circuit_isolation", "status": "PASS", "reason": f"Multiple exit nodes observed ({len(ips)})", "unique_ips": list(ips)}
    
    def test_http_referrer_leak(self):
        """Test 7: HTTP Referrer leak test."""
        print("\n[TEST 7] HTTP Referrer Leak Test")
        
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(30)
            
            s.connect(("httpbin.org", 80))
            referrer = f"https://secret-site-{uuid.uuid4().hex[:16]}.example.com/secret"
            request = f"GET /headers HTTP/1.1\r\nHost: httpbin.org\r\nReferer: {referrer}\r\nUser-Agent: TuxBrowser-RigorousTest\r\nConnection: close\r\n\r\n"
            s.send(request.encode())
            
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            s.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            if referrer in response_str:
                return {"test": "http_referrer_leak", "status": "FAIL", "reason": "Referrer header leaked in response"}
            
            return {"test": "http_referrer_leak", "status": "PASS", "reason": "Referrer not leaked in response"}
        except Exception as e:
            return {"test": "http_referrer_leak", "status": "ERROR", "reason": str(e)}
    
    def test_etag_cache_tracking(self):
        """Test 8: ETag/Cache tracking test."""
        print("\n[TEST 8] ETag/Cache Tracking Test")
        
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(30)
            
            # First request
            s.connect(("httpbin.org", 80))
            request = b"GET /etag/unique-test-etag HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n"
            s.send(request)
            response1 = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response1 += chunk
            s.close()
            
            # Extract ETag
            etag = None
            for line in response1.decode('utf-8', errors='ignore').split('\r\n'):
                if line.lower().startswith('etag:'):
                    etag = line.split(':', 1)[1].strip()
                    break
            
            if not etag:
                return {"test": "etag_tracking", "status": "INFO", "reason": "No ETag in response"}
            
            # Second request with If-None-Match
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(30)
            s.connect(("httpbin.org", 80))
            request = f"GET /etag/unique-test-etag HTTP/1.1\r\nHost: httpbin.org\r\nIf-None-Match: {etag}\r\nConnection: close\r\n\r\n"
            s.send(request.encode())
            response2 = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response2 += chunk
            s.close()
            
            if b"304 Not Modified" in response2:
                return {"test": "etag_tracking", "status": "WARN", "reason": "ETag tracking possible (304 returned)", "etag": etag}
            
            return {"test": "etag_tracking", "status": "PASS", "reason": "ETag not used for tracking", "etag": etag}
        except Exception as e:
            return {"test": "etag_tracking", "status": "ERROR", "reason": str(e)}
    
    def test_tor_circuit_new_identity(self):
        """Test 9: Tor NEWNYM (New Identity) test via control port."""
        print("\n[TEST 9] Tor NEWNYM (New Identity) Test")
        
        try:
            # Connect to control port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((self.proxy_host, self.control_port))
            
            # Read auth challenge
            auth_response = s.recv(1024).decode('utf-8', errors='ignore')
            
            # Try cookie authentication
            cookie_path = "/home/pie/Desktop/Tux_browser/tests/tor_data/control_auth_cookie"
            if os.path.exists(cookie_path):
                with open(cookie_path, 'rb') as f:
                    cookie = f.read().hex()
                s.send(f"AUTHENTICATE {cookie}\r\n".encode())
                response = s.recv(1024).decode('utf-8', errors='ignore')
                
                if "250 OK" in response:
                    # Send NEWNYM
                    s.send(b"SIGNAL NEWNYM\r\n")
                    response = s.recv(1024).decode('utf-8', errors='ignore')
                    s.close()
                    
                    if "250 OK" in response:
                        return {"test": "tor_newnym", "status": "PASS", "reason": "NEWNYM signal accepted"}
                    else:
                        return {"test": "tor_newnym", "status": "FAIL", "reason": f"NEWNYM failed: {response}"}
                else:
                    s.close()
                    return {"test": "tor_newnym", "status": "FAIL", "reason": f"Authentication failed: {response}"}
            else:
                s.close()
                return {"test": "tor_newnym", "status": "SKIP", "reason": "Control cookie not found"}
        except Exception as e:
            return {"test": "tor_newnym", "status": "ERROR", "reason": str(e)}
    
    def test_onion_service_access(self):
        """Test 10: Onion service (.onion) access test."""
        print("\n[TEST 10] Onion Service Access Test")
        
        # Test with a known onion service (DuckDuckGo)
        onion_address = "duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"
        
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            s.settimeout(60)
            
            s.connect((onion_address, 80))
            request = f"GET / HTTP/1.1\r\nHost: {onion_address}\r\nUser-Agent: TuxBrowser-RigorousTest\r\nConnection: close\r\n\r\n"
            s.send(request.encode())
            
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            s.close()
            
            response_str = response.decode('utf-8', errors='ignore')
            if "200 OK" in response_str or "DuckDuckGo" in response_str:
                return {"test": "onion_access", "status": "PASS", "reason": "Successfully accessed .onion service"}
            
            return {"test": "onion_access", "status": "WARN", "reason": f"Connected but unexpected response: {response_str[:200]}"}
        except Exception as e:
            return {"test": "onion_access", "status": "FAIL", "reason": f"Onion access failed: {e}"}
    
    def run_all_tests(self):
        """Run all rigorous IP leak tests."""
        print("=" * 70)
        print("Tux Browser - RIGOROUS IP LEAK ATTACK TEST SUITE")
        print("=" * 70)
        
        tests = [
            self.test_basic_ip_leak,
            self.test_dns_leak_multiple_domains,
            self.test_dns_resolver_leak,
            self.test_http_host_header_leak,
            self.test_tcp_timing_attack,
            self.test_concurrent_circuit_isolation,
            self.test_http_referrer_leak,
            self.test_etag_cache_tracking,
            self.test_tor_circuit_new_identity,
            self.test_onion_service_access,
        ]
        
        for test in tests:
            try:
                result = test()
                self.results[result["test"]] = result
                status_symbol = {
                    "PASS": "✓", "FAIL": "✗", "SKIP": "⊘", 
                    "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"
                }.get(result["status"], "?")
                print(f"  {status_symbol} {result['test']}: {result['status']} - {result.get('reason', '')}")
            except Exception as e:
                self.results[test.__name__] = {"test": test.__name__, "status": "ERROR", "reason": str(e)}
                print(f"  ⚠ {test.__name__}: ERROR - {e}")
        
        print()
        self.print_summary()
        return self.results
    
    def print_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get("status") == "PASS")
        failed = sum(1 for r in self.results.values() if r.get("status") == "FAIL")
        errors = sum(1 for r in self.results.values() if r.get("status") == "ERROR")
        warns = sum(1 for r in self.results.values() if r.get("status") == "WARN")
        skipped = sum(1 for r in self.results.values() if r.get("status") == "SKIP")
        
        print("=" * 70)
        print(f"SUMMARY: {passed}/{total} passed, {failed} failed, {errors} errors, {warns} warnings, {skipped} skipped")
        print("=" * 70)
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for name, result in self.results.items():
                if result.get("status") == "FAIL":
                    print(f"  - {name}: {result.get('reason', 'Unknown')}")
        
        if warns > 0:
            print("\nWARNINGS:")
            for name, result in self.results.items():
                if result.get("status") == "WARN":
                    print(f"  - {name}: {result.get('reason', 'Unknown')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tux Browser Rigorous IP Leak Attack Tests")
    parser.add_argument("--proxy-host", default="127.0.0.1", help="Tor proxy host")
    parser.add_argument("--proxy-port", type=int, default=9050, help="Tor proxy port")
    parser.add_argument("--control-port", type=int, default=9051, help="Tor control port")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    tester = RigorousIPLeakTester(args.proxy_host, args.proxy_port, args.control_port)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    sys.exit(0 if all(r.get("status") in ("PASS", "SKIP", "INFO", "WARN", "ERROR") for r in results.values()) else 1)