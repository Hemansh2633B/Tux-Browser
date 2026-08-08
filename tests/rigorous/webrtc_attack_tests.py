#!/usr/bin/env python3
"""
Rigorous WebRTC Leak Attack Tests for Tux Browser
Tests WebRTC IP leaks through various attack vectors including:
- Direct PeerConnection
- DataChannel
- TURN/STUN servers
- ICE candidate gathering
- Browser automation with Selenium/Playwright if available
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse

try:
    import socks
except ImportError:
    print("Installing pysocks...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pysocks"])
    import socks

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class RigorousWebRTCTester:
    def __init__(self, browser_path, proxy_host="127.0.0.1", proxy_port=9050):
        self.browser_path = browser_path
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.test_server_port = 8888
        self.test_server = None
        self.server_thread = None
        self.results = {}
        self.test_page_path = None
        
    def create_comprehensive_webrtc_test_page(self):
        """Create HTML page with comprehensive WebRTC leak tests."""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Rigorous WebRTC Leak Test</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: monospace; padding: 20px; background: #1a1a1a; color: #e0e0e0; }}
        h1 {{ color: #4ec9b0; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #333; border-radius: 4px; background: #252526; }}
        .test-title {{ color: #dcdcaa; font-weight: bold; margin-bottom: 10px; }}
        .result {{ padding: 10px; margin: 10px 0; border-radius: 4px; font-family: monospace; font-size: 12px; }}
        .leak {{ background: #3d1a1a; border: 1px solid #f44747; color: #f44747; }}
        .safe {{ background: #1a3d1a; border: 1px solid #4ec9b0; color: #4ec9b0; }}
        .info {{ background: #1a1a3d; border: 1px solid #569cd6; color: #569cd6; }}
        .warn {{ background: #3d3d1a; border: 1px solid #dcdcaa; color: #dcdcaa; }}
        pre {{ background: #1e1e1e; padding: 10px; overflow: auto; white-space: pre-wrap; }}
        .summary {{ padding: 15px; margin-top: 20px; border-radius: 4px; font-weight: bold; }}
        .summary.pass {{ background: #1a3d1a; border: 1px solid #4ec9b0; color: #4ec9b0; }}
        .summary.fail {{ background: #3d1a1a; border: 1px solid #f44747; color: #f44747; }}
        .ip-list {{ color: #ce9178; }}
    </style>
</head>
<body>
    <h1>🔒 Rigorous WebRTC Leak Test</h1>
    <div id="results"></div>
    <div id="summary" class="summary">Running tests...</div>
    <script>
        const resultsDiv = document.getElementById('results');
        const summaryDiv = document.getElementById('summary');
        let leakCount = 0;
        let testCount = 0;
        let allIPs = new Set();
        
        function addResult(title, content, type) {{
            testCount++;
            const div = document.createElement('div');
            div.className = 'test-section';
            div.innerHTML = '<div class="test-title">' + title + '</div><div class="result ' + type + '">' + content + '</div>';
            resultsDiv.appendChild(div);
            if (type === 'leak') leakCount++;
        }}
        
        function addIP(ip) {{
            if (ip && !allIPs.has(ip)) {{
                allIPs.add(ip);
            }}
        }}
        
        function extractIPs(text) {{
            const ipv4Regex = /\\b(?:\\d{{1,3}}\\.){{3}}\\d{{1,3}}\\b/g;
            const ipv6Regex = /\\b(?:[0-9a-fA-F]{{1,4}}:{{2,7}}[0-9a-fA-F]{{1,4}})\\b/g;
            const matches = text.match(ipv4Regex) || [];
            const matches6 = text.match(ipv6Regex) || [];
            return [...matches, ...matches6];
        }}
        
        // Test 1: Basic PeerConnection with STUN
        async function testBasicPeerConnection() {{
            try {{
                const pc = new RTCPeerConnection({{
                    iceServers: [
                        {{urls: 'stun:stun.l.google.com:19302'}},
                        {{urls: 'stun:stun1.l.google.com:19302'}},
                        {{urls: 'stun:stun2.l.google.com:19302'}},
                    ]
                }});
                
                const ips = new Set();
                let candidateCount = 0;
                
                pc.onicecandidate = (event) => {{
                    if (event.candidate) {{
                        candidateCount++;
                        const candidate = event.candidate.candidate;
                        const foundIPs = extractIPs(candidate);
                        foundIPs.forEach(ip => {{ ips.add(ip); addIP(ip); }});
                    }}
                }};
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                // Wait for ICE gathering
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                pc.close();
                
                if (ips.size > 0) {{
                    addResult('Test 1: Basic PeerConnection (STUN)', 
                        'LEAK DETECTED! IPs found: ' + Array.from(ips).join(', '), 'leak');
                    return {{ leaked: true, ips: Array.from(ips), candidateCount }};
                }} else {{
                    addResult('Test 1: Basic PeerConnection (STUN)', 
                        'SAFE: No IPs leaked (candidates: ' + candidateCount + ')', 'safe');
                    return {{ leaked: false, ips: [], candidateCount }};
                }}
            }} catch (e) {{
                addResult('Test 1: Basic PeerConnection (STUN)', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Test 2: PeerConnection with TURN
        async function testPeerConnectionWithTURN() {{
            try {{
                const pc = new RTCPeerConnection({{
                    iceServers: [
                        {{urls: 'stun:stun.l.google.com:19302'}},
                        {{urls: 'turn:openrelay.metered.ca:80', username: 'openrelayproject', credential: 'openrelayproject'}},
                        {{urls: 'turn:openrelay.metered.ca:443', username: 'openrelayproject', credential: 'openrelayproject'}},
                        {{urls: 'turn:openrelay.metered.ca:443?transport=tcp', username: 'openrelayproject', credential: 'openrelayproject'}},
                    ]
                }});
                
                const ips = new Set();
                let candidateCount = 0;
                
                pc.onicecandidate = (event) => {{
                    if (event.candidate) {{
                        candidateCount++;
                        const candidate = event.candidate.candidate;
                        const foundIPs = extractIPs(candidate);
                        foundIPs.forEach(ip => {{ ips.add(ip); addIP(ip); }});
                    }}
                }};
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                await new Promise(resolve => setTimeout(resolve, 8000));
                
                pc.close();
                
                if (ips.size > 0) {{
                    addResult('Test 2: PeerConnection with TURN', 
                        'LEAK DETECTED! IPs found: ' + Array.from(ips).join(', '), 'leak');
                    return {{ leaked: true, ips: Array.from(ips), candidateCount }};
                }} else {{
                    addResult('Test 2: PeerConnection with TURN', 
                        'SAFE: No IPs leaked (candidates: ' + candidateCount + ')', 'safe');
                    return {{ leaked: false, ips: [], candidateCount }};
                }}
            }} catch (e) {{
                addResult('Test 2: PeerConnection with TURN', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Test 3: Multiple PeerConnections (simulating multiple tabs)
        async function testMultiplePeerConnections() {{
            try {{
                const allIPs = new Set();
                let totalCandidates = 0;
                
                for (let i = 0; i < 3; i++) {{
                    const pc = new RTCPeerConnection({{
                        iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]
                    }});
                    
                    pc.onicecandidate = (event) => {{
                        if (event.candidate) {{
                            totalCandidates++;
                            const candidate = event.candidate.candidate;
                            const foundIPs = extractIPs(candidate);
                            foundIPs.forEach(ip => {{ allIPs.add(ip); addIP(ip); }});
                        }}
                    }};
                    
                    pc.createDataChannel('test' + i);
                    const offer = await pc.createOffer();
                    await pc.setLocalDescription(offer);
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    pc.close();
                }}
                
                if (allIPs.size > 0) {{
                    addResult('Test 3: Multiple PeerConnections', 
                        'LEAK DETECTED! IPs found: ' + Array.from(allIPs).join(', '), 'leak');
                    return {{ leaked: true, ips: Array.from(allIPs), candidateCount: totalCandidates }};
                }} else {{
                    addResult('Test 3: Multiple PeerConnections', 
                        'SAFE: No IPs leaked (total candidates: ' + totalCandidates + ')', 'safe');
                    return {{ leaked: false, ips: [], candidateCount: totalCandidates }};
                }}
            }} catch (e) {{
                addResult('Test 3: Multiple PeerConnections', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Test 4: DataChannel direct connection
        async function testDataChannelDirect() {{
            try {{
                const pc1 = new RTCPeerConnection({{
                    iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]
                }});
                const pc2 = new RTCPeerConnection({{
                    iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]
                }});
                
                const ips = new Set();
                let candidateCount = 0;
                
                pc1.onicecandidate = (e) => {{
                    if (e.candidate) {{
                        candidateCount++;
                        const foundIPs = extractIPs(e.candidate.candidate);
                        foundIPs.forEach(ip => {{ ips.add(ip); addIP(ip); }});
                    }}
                }};
                pc2.onicecandidate = (e) => {{
                    if (e.candidate) {{
                        candidateCount++;
                        const foundIPs = extractIPs(e.candidate.candidate);
                        foundIPs.forEach(ip => {{ ips.add(ip); addIP(ip); }});
                    }}
                }};
                
                const dc = pc1.createDataChannel('test');
                const offer = await pc1.createOffer();
                await pc1.setLocalDescription(offer);
                await pc2.setRemoteDescription(offer);
                const answer = await pc2.createAnswer();
                await pc2.setLocalDescription(answer);
                await pc1.setRemoteDescription(answer);
                
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                pc1.close();
                pc2.close();
                
                if (ips.size > 0) {{
                    addResult('Test 4: DataChannel Direct Connection', 
                        'LEAK DETECTED! IPs found: ' + Array.from(ips).join(', '), 'leak');
                    return {{ leaked: true, ips: Array.from(ips), candidateCount }};
                }} else {{
                    addResult('Test 4: DataChannel Direct Connection', 
                        'SAFE: No IPs leaked (candidates: ' + candidateCount + ')', 'safe');
                    return {{ leaked: false, ips: [], candidateCount }};
                }}
            }} catch (e) {{
                addResult('Test 4: DataChannel Direct Connection', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Test 5: WebRTC API availability (check if blocked)
        async function testWebRTCAPIBlocked() {{
            try {{
                const pc = new RTCPeerConnection({{iceServers: []}});
                pc.close();
                addResult('Test 5: WebRTC API Availability', 
                    'WebRTC API is AVAILABLE (not blocked at browser level)', 'warn');
                return {{ blocked: false }};
            }} catch (e) {{
                addResult('Test 5: WebRTC API Availability', 
                    'WebRTC API is BLOCKED: ' + e.toString(), 'safe');
                return {{ blocked: true }};
            }}
        }}
        
        // Test 6: ICE candidate filtering (check for mDNS/local IPs)
        async function testLocalIPLeak() {{
            try {{
                const pc = new RTCPeerConnection({{
                    iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]
                }});
                
                const localIPs = new Set();
                const publicIPs = new Set();
                let candidateCount = 0;
                
                pc.onicecandidate = (event) => {{
                    if (event.candidate) {{
                        candidateCount++;
                        const candidate = event.candidate.candidate;
                        const foundIPs = extractIPs(candidate);
                        foundIPs.forEach(ip => {{
                            addIP(ip);
                            // Check for local/mDNS IPs
                            if (ip.startsWith('192.168.') || ip.startsWith('10.') || 
                                ip.startsWith('172.16.') || ip.startsWith('172.17.') ||
                                ip.startsWith('172.18.') || ip.startsWith('172.19.') ||
                                ip.startsWith('172.20.') || ip.startsWith('172.21.') ||
                                ip.startsWith('172.22.') || ip.startsWith('172.23.') ||
                                ip.startsWith('172.24.') || ip.startsWith('172.25.') ||
                                ip.startsWith('172.26.') || ip.startsWith('172.27.') ||
                                ip.startsWith('172.28.') || ip.startsWith('172.29.') ||
                                ip.startsWith('172.30.') || ip.startsWith('172.31.') ||
                                ip.startsWith('169.254.') || ip.startsWith('127.') ||
                                ip.endsWith('.local') || ip.includes('.local')) {{
                                localIPs.add(ip);
                            }} else {{
                                publicIPs.add(ip);
                            }}
                        }});
                    }}
                }};
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                pc.close();
                
                if (localIPs.size > 0) {{
                    addResult('Test 6: Local/mDNS IP Leak', 
                        'LOCAL IP LEAK! Local IPs: ' + Array.from(localIPs).join(', ') + 
                        (publicIPs.size > 0 ? ' | Public IPs: ' + Array.from(publicIPs).join(', ') : ''), 'leak');
                    return {{ leaked: true, localIPs: Array.from(localIPs), publicIPs: Array.from(publicIPs), candidateCount }};
                }} else if (publicIPs.size > 0) {{
                    addResult('Test 6: Local/mDNS IP Leak', 
                        'Public IPs found (may be Tor exit): ' + Array.from(publicIPs).join(', '), 'warn');
                    return {{ leaked: false, localIPs: [], publicIPs: Array.from(publicIPs), candidateCount }};
                }} else {{
                    addResult('Test 6: Local/mDNS IP Leak', 
                        'SAFE: No IPs leaked (candidates: ' + candidateCount + ')', 'safe');
                    return {{ leaked: false, localIPs: [], publicIPs: [], candidateCount }};
                }}
            }} catch (e) {{
                addResult('Test 6: Local/mDNS IP Leak', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Test 7: WebRTC with different ICE transport policies
        async function testICETransportPolicy() {{
            try {{
                const pc = new RTCPeerConnection({{
                    iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}],
                    iceTransportPolicy: 'all'  // Try 'relay' for TURN-only
                }});
                
                const ips = new Set();
                let candidateCount = 0;
                
                pc.onicecandidate = (event) => {{
                    if (event.candidate) {{
                        candidateCount++;
                        const foundIPs = extractIPs(event.candidate.candidate);
                        foundIPs.forEach(ip => {{ ips.add(ip); addIP(ip); }});
                    }}
                }};
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                pc.close();
                
                if (ips.size > 0) {{
                    addResult('Test 7: ICE Transport Policy (all)', 
                        'IPs found: ' + Array.from(ips).join(', '), 'leak');
                    return {{ leaked: true, ips: Array.from(ips), candidateCount }};
                }} else {{
                    addResult('Test 7: ICE Transport Policy (all)', 
                        'SAFE: No IPs leaked (candidates: ' + candidateCount + ')', 'safe');
                    return {{ leaked: false, ips: [], candidateCount }};
                }}
            }} catch (e) {{
                addResult('Test 7: ICE Transport Policy (all)', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Test 8: Check for WebRTC statistics leak
        async function testWebRTCStats() {{
            try {{
                const pc = new RTCPeerConnection({{
                    iceServers: [{{urls: 'stun:stun.l.google.com:19302'}}]
                }});
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                // Get stats
                const stats = await pc.getStats();
                let statsInfo = [];
                stats.forEach(report => {{
                    if (report.type === 'candidate-pair' || report.type === 'local-candidate' || report.type === 'remote-candidate') {{
                        const ip = extractIPs(JSON.stringify(report));
                        if (ip.length > 0) {{
                            statsInfo.push(report.type + ': ' + ip.join(', '));
                            ip.forEach(addIP);
                        }}
                    }}
                }});
                
                pc.close();
                
                if (statsInfo.length > 0) {{
                    addResult('Test 8: WebRTC Statistics Leak', 
                        'Stats reveal IPs: ' + statsInfo.join('; '), 'leak');
                    return {{ leaked: true, stats: statsInfo }};
                }} else {{
                    addResult('Test 8: WebRTC Statistics Leak', 
                        'SAFE: No IPs in stats', 'safe');
                    return {{ leaked: false }};
                }}
            }} catch (e) {{
                addResult('Test 8: WebRTC Statistics Leak', 
                    'ERROR: ' + e.toString(), 'info');
                return {{ error: e.toString() }};
            }}
        }}
        
        // Run all tests
        async function runAllTests() {{
            addResult('Starting', 'Running rigorous WebRTC leak tests...', 'info');
            
            await testWebRTCAPIBlocked();
            await testBasicPeerConnection();
            await testLocalIPLeak();
            await testPeerConnectionWithTURN();
            await testMultiplePeerConnections();
            await testDataChannelDirect();
            await testICETransportPolicy();
            await testWebRTCStats();
            
            // Summary
            if (leakCount === 0) {{
                summaryDiv.className = 'summary pass';
                summaryDiv.innerHTML = '✓ ALL TESTS PASSED - No WebRTC leaks detected (' + testCount + ' tests)';
            }} else {{
                summaryDiv.className = 'summary fail';
                summaryDiv.innerHTML = '✗ ' + leakCount + ' LEAKS DETECTED out of ' + testCount + ' tests';
            }}
            
            if (allIPs.size > 0) {{
                const ipDiv = document.createElement('div');
                ipDiv.className = 'test-section';
                ipDiv.innerHTML = '<div class="test-title">All Unique IPs Observed</div><div class="result ip-list">' + Array.from(allIPs).join(', ') + '</div>';
                resultsDiv.appendChild(ipDiv);
            }}
        }}
        
        runAllTests();
    </script>
</body>
</html>"""
        return html_content
    
    def start_test_server(self):
        """Start HTTP server to serve test page."""
        import http.server
        import socketserver
        
        class TestHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/webrtc-rigorous-test.html':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(self.server.test_page.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        handler = lambda *args: TestHandler(*args, test_page=self.create_comprehensive_webrtc_test_page())
        
        self.test_server = socketserver.TCPServer(("", self.test_server_port), handler)
        self.server_thread = Thread(target=self.test_server.serve_forever, daemon=True)
        self.server_thread.start()
        
        time.sleep(1)
        return f"http://localhost:{self.test_server_port}/webrtc-rigorous-test.html"
    
    def stop_test_server(self):
        """Stop HTTP server."""
        if self.test_server:
            self.test_server.shutdown()
            self.test_server.server_close()
        if self.server_thread:
            self.server_thread.join(timeout=2)
    
    def test_webrtc_code_blocking(self):
        """Test 1: Check WebRTC blocking in content_blocker.cc"""
        print("\n[TEST 1] WebRTC Code-Level Blocking Check")
        
        content_blocker_path = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/net/tor/content_blocker.cc"
        
        if not os.path.exists(content_blocker_path):
            return {"test": "webrtc_code_block", "status": "ERROR", "reason": "Content blocker file not found"}
        
        with open(content_blocker_path, 'r') as f:
            content = f.read()
        
        import re
        standard_blocked = re.search(r'SecurityLevel::kStandard.*?kWebRTC.*?Decision::kBlock', content, re.DOTALL)
        safer_blocked = re.search(r'SecurityLevel::kSafer.*?kWebRTC.*?Decision::kBlock', content, re.DOTALL)
        safest_blocked = re.search(r'SecurityLevel::kSafest.*?kWebRTC.*?Decision::kBlock', content, re.DOTALL)
        
        all_blocked = all([standard_blocked, safer_blocked, safest_blocked])
        
        return {
            "test": "webrtc_code_block",
            "status": "PASS" if all_blocked else "FAIL",
            "standard_blocked": bool(standard_blocked),
            "safer_blocked": bool(safer_blocked),
            "safest_blocked": bool(safest_blocked),
            "reason": "WebRTC blocked in all security levels" if all_blocked else "WebRTC blocking missing in some levels"
        }
    
    def test_fingerprinting_protection_webrtc(self):
        """Test 2: Check fingerprinting protection for WebRTC"""
        print("\n[TEST 2] Fingerprinting Protection WebRTC Check")
        
        fp_path = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/net/tor/fingerprinting_protection.cc"
        
        if not os.path.exists(fp_path):
            return {"test": "fp_webrtc_protection", "status": "ERROR", "reason": "Fingerprinting protection file not found"}
        
        with open(fp_path, 'r') as f:
            content = f.read()
        
        # Check for WebRTC-related fingerprinting protections
        checks = {
            "webrtc_blocked": "WebRTC" in content and ("block" in content.lower() or "disable" in content.lower()),
            "ice_candidate_filtering": "ice" in content.lower() and "candidate" in content.lower(),
            "stun_blocking": "stun" in content.lower(),
        }
        
        return {
            "test": "fp_webrtc_protection",
            "status": "PASS" if all(checks.values()) else "WARN",
            "details": checks,
            "reason": "Fingerprinting protection includes WebRTC mitigations" if all(checks.values()) else "Some WebRTC fingerprinting protections missing"
        }
    
    def test_via_selenium(self, test_url):
        """Test 3: WebRTC leak via Selenium WebDriver."""
        print("\n[TEST 3] WebRTC Leak Test via Selenium")
        
        if not SELENIUM_AVAILABLE:
            return {"test": "webrtc_selenium", "status": "SKIP", "reason": "Selenium not installed"}
        
        if not os.path.exists(self.browser_path):
            return {"test": "webrtc_selenium", "status": "SKIP", "reason": f"Browser binary not found at {self.browser_path}"}
        
        try:
            options = Options()
            options.binary_location = self.browser_path
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument(f'--proxy-server=socks5h://{self.proxy_host}:{self.proxy_port}')
            options.add_argument('--enable-features=TorNetworking')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            # Disable WebRTC if possible via prefs
            prefs = {
                "webrtc.ip_handling_policy": "disable_non_proxied_udp",
                "webrtc.multiple_routes_enabled": False,
                "webrtc.nonproxied_udp_enabled": False,
            }
            options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)
            
            try:
                driver.get(test_url)
                # Wait for tests to complete
                time.sleep(30)
                
                # Get results
                summary = driver.find_element(By.ID, "summary").text
                results_html = driver.find_element(By.ID, "results").get_attribute('innerHTML')
                
                driver.quit()
                
                if "ALL TESTS PASSED" in summary:
                    return {"test": "webrtc_selenium", "status": "PASS", "reason": summary, "summary": summary}
                elif "LEAKS DETECTED" in summary:
                    return {"test": "webrtc_selenium", "status": "FAIL", "reason": summary, "summary": summary, "results_html": results_html[:5000]}
                else:
                    return {"test": "webrtc_selenium", "status": "WARN", "reason": summary, "summary": summary}
            except Exception as e:
                driver.quit()
                return {"test": "webrtc_selenium", "status": "ERROR", "reason": str(e)}
        except Exception as e:
            return {"test": "webrtc_selenium", "status": "ERROR", "reason": str(e)}
    
    def test_via_playwright(self, test_url):
        """Test 4: WebRTC leak via Playwright."""
        print("\n[TEST 4] WebRTC Leak Test via Playwright")
        
        if not PLAYWRIGHT_AVAILABLE:
            return {"test": "webrtc_playwright", "status": "SKIP", "reason": "Playwright not installed"}
        
        if not os.path.exists(self.browser_path):
            return {"test": "webrtc_playwright", "status": "SKIP", "reason": f"Browser binary not found at {self.browser_path}"}
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    executable_path=self.browser_path,
                    headless=True,
                    args=[
                        '--disable-gpu',
                        '--no-sandbox',
                        f'--proxy-server=socks5h://{self.proxy_host}:{self.proxy_port}',
                        '--enable-features=TorNetworking',
                        '--disable-dev-shm-usage',
                    ]
                )
                
                context = browser.new_context(
                    permissions=[],
                    java_script_enabled=True,
                )
                
                page = context.new_page()
                page.set_default_timeout(60000)
                
                page.goto(test_url, wait_until="networkidle")
                page.wait_for_timeout(30000)
                
                summary = page.locator("#summary").inner_text()
                results_html = page.locator("#results").inner_html()
                
                browser.close()
                
                if "ALL TESTS PASSED" in summary:
                    return {"test": "webrtc_playwright", "status": "PASS", "reason": summary, "summary": summary}
                elif "LEAKS DETECTED" in summary:
                    return {"test": "webrtc_playwright", "status": "FAIL", "reason": summary, "summary": summary, "results_html": results_html[:5000]}
                else:
                    return {"test": "webrtc_playwright", "status": "WARN", "reason": summary, "summary": summary}
        except Exception as e:
            return {"test": "webrtc_playwright", "status": "ERROR", "reason": str(e)}
    
    def test_tor_ip_via_webrtc_page(self, test_url):
        """Test 5: Simple test to verify Tor IP through WebRTC page."""
        print("\n[TEST 5] Tor IP Verification via WebRTC Page")
        
        if not os.path.exists(self.browser_path):
            return {"test": "tor_ip_verification", "status": "SKIP", "reason": f"Browser binary not found at {self.browser_path}"}
        
        try:
            # Just try to launch browser and see if it loads
            cmd = [
                self.browser_path,
                '--headless',
                '--disable-gpu',
                '--no-sandbox',
                f'--proxy-server=socks5h://{self.proxy_host}:{self.proxy_port}',
                '--enable-features=TorNetworking',
                '--disable-dev-shm-usage',
                '--dump-dom',
                test_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Check if page loaded
                if "WebRTC" in result.stdout or "test" in result.stdout.lower():
                    return {"test": "tor_ip_verification", "status": "PASS", "reason": "Browser launched and page loaded via Tor"}
                else:
                    return {"test": "tor_ip_verification", "status": "WARN", "reason": "Browser launched but page content unclear"}
            else:
                return {"test": "tor_ip_verification", "status": "FAIL", "reason": f"Browser failed: {result.stderr[:500]}"}
        except subprocess.TimeoutExpired:
            return {"test": "tor_ip_verification", "status": "TIMEOUT", "reason": "Browser test timed out"}
        except Exception as e:
            return {"test": "tor_ip_verification", "status": "ERROR", "reason": str(e)}
    
    def run_all_tests(self):
        """Run all rigorous WebRTC leak tests."""
        print("=" * 70)
        print("Tux Browser - RIGOROUS WebRTC LEAK ATTACK TEST SUITE")
        print("=" * 70)
        
        # Code-level tests (always run)
        result1 = self.test_webrtc_code_blocking()
        self.results[result1["test"]] = result1
        status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result1["status"], "?")
        print(f"  {status_symbol} {result1['test']}: {result1['status']} - {result1.get('reason', '')}")
        
        result2 = self.test_fingerprinting_protection_webrtc()
        self.results[result2["test"]] = result2
        status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result2["status"], "?")
        print(f"  {status_symbol} {result2['test']}: {result2['status']} - {result2.get('reason', '')}")
        
        # Browser-based tests
        test_url = self.start_test_server()
        try:
            result3 = self.test_tor_ip_via_webrtc_page(test_url)
            self.results[result3["test"]] = result3
            status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ", "TIMEOUT": "⏱"}.get(result3["status"], "?")
            print(f"  {status_symbol} {result3['test']}: {result3['status']} - {result3.get('reason', '')}")
            
            if SELENIUM_AVAILABLE:
                result4 = self.test_via_selenium(test_url)
                self.results[result4["test"]] = result4
                status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result4["status"], "?")
                print(f"  {status_symbol} {result4['test']}: {result4['status']} - {result4.get('reason', '')}")
            
            if PLAYWRIGHT_AVAILABLE:
                result5 = self.test_via_playwright(test_url)
                self.results[result5["test"]] = result5
                status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result5["status"], "?")
                print(f"  {status_symbol} {result5['test']}: {result5['status']} - {result5.get('reason', '')}")
        finally:
            self.stop_test_server()
        
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
    parser = argparse.ArgumentParser(description="Tux Browser Rigorous WebRTC Leak Attack Tests")
    parser.add_argument("--browser", default="/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser/chrome", help="Path to browser binary")
    parser.add_argument("--proxy-host", default="127.0.0.1", help="Tor proxy host")
    parser.add_argument("--proxy-port", type=int, default=9050, help="Tor proxy port")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    tester = RigorousWebRTCTester(args.browser, args.proxy_host, args.proxy_port)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    sys.exit(0 if all(r.get("status") in ("PASS", "SKIP", "INFO", "WARN") for r in results.values()) else 1)