#!/usr/bin/env python3
"""
Tux Browser - WebRTC Leak Test
Tests for WebRTC IP leaks (local and public IPs).
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse

class WebRTCLeakTester:
    def __init__(self, browser_path, proxy_host="127.0.0.1", proxy_port=9050):
        self.browser_path = browser_path
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.test_server_port = 8888
        self.test_server = None
        self.server_thread = None
        self.results = {}
    
    def create_webrtc_test_page(self):
        """Create HTML page that tests WebRTC IP leaks."""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>WebRTC Leak Test</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        .result { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .leak { background: #ffcccc; border: 1px solid #ff0000; }
        .safe { background: #ccffcc; border: 1px solid #00aa00; }
        .info { background: #ccccff; border: 1px solid #0000aa; }
        pre { background: #f5f5f5; padding: 10px; overflow: auto; }
    </style>
</head>
<body>
    <h1>WebRTC Leak Test</h1>
    <div id="results"></div>
    <script>
        const resultsDiv = document.getElementById('results');
        
        function addResult(title, content, type) {
            const div = document.createElement('div');
            div.className = 'result ' + type;
            div.innerHTML = '<h3>' + title + '</h3><pre>' + content + '</pre>';
            resultsDiv.appendChild(div);
        }
        
        // Test 1: WebRTC PeerConnection
        async function testWebRTC() {
            try {
                const pc = new RTCPeerConnection({
                    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
                });
                
                const ips = new Set();
                
                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        const candidate = event.candidate.candidate;
                        const ipMatch = candidate.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/);
                        if (ipMatch) {
                            ips.add(ipMatch[1]);
                        }
                        // Also check for IPv6
                        const ipv6Match = candidate.match(/([0-9a-fA-F:]+):/);
                        if (ipv6Match) {
                            ips.add(ipv6Match[1]);
                        }
                    }
                };
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                // Wait for ICE candidates
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                pc.close();
                
                if (ips.size > 0) {
                    addResult('WebRTC ICE Candidates (LEAK)', Array.from(ips).join(', '), 'leak');
                    return { leaked: true, ips: Array.from(ips) };
                } else {
                    addResult('WebRTC ICE Candidates', 'No IPs found (SAFE)', 'safe');
                    return { leaked: false, ips: [] };
                }
            } catch (e) {
                addResult('WebRTC Test Error', e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 2: DataChannel direct
        async function testDataChannel() {
            try {
                const pc1 = new RTCPeerConnection({
                    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
                });
                const pc2 = new RTCPeerConnection({
                    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
                });
                
                const ips = new Set();
                
                pc1.onicecandidate = (e) => {
                    if (e.candidate) {
                        const m = e.candidate.candidate.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/);
                        if (m) ips.add(m[1]);
                    }
                };
                pc2.onicecandidate = (e) => {
                    if (e.candidate) {
                        const m = e.candidate.candidate.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/);
                        if (m) ips.add(m[1]);
                    }
                };
                
                const dc = pc1.createDataChannel('test');
                const offer = await pc1.createOffer();
                await pc1.setLocalDescription(offer);
                await pc2.setRemoteDescription(offer);
                const answer = await pc2.createAnswer();
                await pc2.setLocalDescription(answer);
                await pc1.setRemoteDescription(answer);
                
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                pc1.close();
                pc2.close();
                
                if (ips.size > 0) {
                    addResult('DataChannel ICE Candidates (LEAK)', Array.from(ips).join(', '), 'leak');
                    return { leaked: true, ips: Array.from(ips) };
                } else {
                    addResult('DataChannel ICE Candidates', 'No IPs found (SAFE)', 'safe');
                    return { leaked: false, ips: [] };
                }
            } catch (e) {
                addResult('DataChannel Test Error', e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 3: Check if WebRTC is blocked
        async function testWebRTCBlocked() {
            try {
                const pc = new RTCPeerConnection();
                pc.close();
                addResult('WebRTC API', 'Available (not blocked)', 'info');
                return { blocked: false };
            } catch (e) {
                addResult('WebRTC API', 'Blocked: ' + e.toString(), 'safe');
                return { blocked: true };
            }
        }
        
        // Run all tests
        async function runTests() {
            addResult('Starting Tests', 'Testing WebRTC leak protection...', 'info');
            
            await testWebRTCBlocked();
            await testWebRTC();
            await testDataChannel();
            
            addResult('Tests Complete', 'Check results above', 'info');
        }
        
        runTests();
    </script>
</body>
</html>
"""
        return html_content
    
    def start_test_server(self):
        """Start HTTP server to serve test page."""
        import http.server
        import socketserver
        
        class TestHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/webrtc-test.html':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(self.server.test_page.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        handler = lambda *args: TestHandler(*args, test_page=self.create_webrtc_test_page())
        
        self.test_server = socketserver.TCPServer(("", self.test_server_port), handler)
        self.server_thread = Thread(target=self.test_server.serve_forever, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)
        return f"http://localhost:{self.test_server_port}/webrtc-test.html"
    
    def stop_test_server(self):
        """Stop HTTP server."""
        if self.test_server:
            self.test_server.shutdown()
            self.test_server.server_close()
        if self.server_thread:
            self.server_thread.join(timeout=2)
    
    def test_webrtc_via_browser(self, test_url):
        """Test WebRTC leak via headless browser."""
        print(f"Testing WebRTC leak at {test_url}...")
        
        # Launch browser with proxy and test page
        # We'll use a simplified approach - just check if browser can be launched
        # In a real test, this would use Selenium/Playwright or similar
        
        if not os.path.exists(self.browser_path):
            return {
                "test": "webrtc_leak",
                "status": "SKIP",
                "reason": f"Browser binary not found at {self.browser_path} (build required)"
            }
        
        cmd = [
            self.browser_path,
            '--headless',
            '--disable-gpu',
            '--no-sandbox',
            f'--proxy-server=socks5h://{self.proxy_host}:{self.proxy_port}',
            '--enable-features=TorNetworking',
            test_url
        ]
        
        try:
            # Run with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "test": "webrtc_leak",
                "status": "MANUAL",
                "reason": "Requires browser automation (Selenium/Playwright) for full test",
                "browser_exit_code": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:500] if result.stderr else ""
            }
        except subprocess.TimeoutExpired:
            return {
                "test": "webrtc_leak",
                "status": "TIMEOUT",
                "reason": "Browser test timed out"
            }
        except Exception as e:
            return {
                "test": "webrtc_leak",
                "status": "ERROR",
                "reason": str(e)
            }
    
    def test_webrtc_blocked_in_code(self):
        """Test if WebRTC is blocked at code level (check our content blocker)."""
        print("Checking WebRTC blocking in content blocker...")
        
        # Check our content_blocker.cc for WebRTC blocking
        content_blocker_path = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/net/tor/content_blocker.cc"
        
        if os.path.exists(content_blocker_path):
            with open(content_blocker_path, 'r') as f:
                content = f.read()
            
            # Check for WebRTC blocking in security levels
            checks = {
                "Standard": "ContentType::kWebRTC.*Decision::kBlock" in content or "kWebRTC.*kBlock" in content,
                "Safer": "kWebRTC.*kBlock" in content,
                "Safest": "kWebRTC.*kBlock" in content,
            }
            
            # More precise check
            import re
            standard_blocked = re.search(r'SecurityLevel::kStandard.*?kWebRTC.*?Decision::kBlock', content, re.DOTALL)
            safer_blocked = re.search(r'SecurityLevel::kSafer.*?kWebRTC.*?Decision::kBlock', content, re.DOTALL)
            safest_blocked = re.search(r'SecurityLevel::kSafest.*?kWebRTC.*?Decision::kBlock', content, re.DOTALL)
            
            return {
                "test": "webrtc_code_block",
                "status": "PASS" if all([standard_blocked, safer_blocked, safest_blocked]) else "FAIL",
                "standard_blocked": bool(standard_blocked),
                "safer_blocked": bool(safer_blocked),
                "safest_blocked": bool(safest_blocked),
                "details": "WebRTC blocking found in all security levels" if all([standard_blocked, safer_blocked, safest_blocked]) else "WebRTC blocking missing in some levels"
            }
        
        return {
            "test": "webrtc_code_block",
            "status": "ERROR",
            "reason": "Content blocker file not found"
        }
    
    def run_all_tests(self):
        """Run all WebRTC leak tests."""
        print("=" * 60)
        print("Tux Browser - WebRTC Leak Test Suite")
        print("=" * 60)
        
        # Test 1: Code-level blocking
        result1 = self.test_webrtc_blocked_in_code()
        self.results[result1["test"]] = result1
        status_symbol = {"PASS": "✓", "FAIL": "✗", "ERROR": "⚠"}.get(result1["status"], "?")
        print(f"  {status_symbol} {result1['test']}: {result1['status']} - {result1.get('details', '')}")
        
        # Test 2: Browser-based test (manual/requires automation)
        test_url = self.start_test_server()
        try:
            result2 = self.test_webrtc_via_browser(test_url)
            self.results[result2["test"]] = result2
            status_symbol = {"PASS": "✓", "FAIL": "✗", "MANUAL": "⚙", "TIMEOUT": "⏱", "ERROR": "⚠"}.get(result2["status"], "?")
            print(f"  {status_symbol} {result2['test']}: {result2['status']} - {result2.get('reason', '')}")
        finally:
            self.stop_test_server()
        
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
    parser = argparse.ArgumentParser(description="Tux Browser WebRTC Leak Tests")
    parser.add_argument("--browser", default="/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser/chrome", help="Path to browser binary")
    parser.add_argument("--proxy-host", default="127.0.0.1", help="Tor proxy host")
    parser.add_argument("--proxy-port", type=int, default=9050, help="Tor proxy port")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    tester = WebRTCLeakTester(args.browser, args.proxy_host, args.proxy_port)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    sys.exit(0 if all(r.get("status") in ("PASS", "MANUAL") for r in results.values()) else 1)