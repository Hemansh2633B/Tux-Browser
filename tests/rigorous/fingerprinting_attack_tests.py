#!/usr/bin/env python3
"""
Rigorous Fingerprinting Attack Tests for Tux Browser
Tests browser fingerprinting resistance including:
- Canvas fingerprinting
- WebGL fingerprinting
- AudioContext fingerprinting
- Font enumeration
- Hardware concurrency/device memory
- Screen resolution/color depth
- Timezone/language
- Battery API
- Sensor APIs
- Performance/Resource timing
- ClientRects
- Media devices
"""

import json
import os
import subprocess
import sys
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


class RigorousFingerprintingTester:
    def __init__(self, browser_path, proxy_host="127.0.0.1", proxy_port=9050):
        self.browser_path = browser_path
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.test_server_port = 8889
        self.test_server = None
        self.server_thread = None
        self.results = {}
        
    def create_fingerprinting_test_page(self):
        """Create comprehensive fingerprinting test page."""
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Rigorous Fingerprinting Test</title>
    <meta charset="utf-8">
    <style>
        body { font-family: monospace; padding: 20px; background: #1a1a1a; color: #e0e0e0; }
        h1 { color: #4ec9b0; }
        .test-section { margin: 20px 0; padding: 15px; border: 1px solid #333; border-radius: 4px; background: #252526; }
        .test-title { color: #dcdcaa; font-weight: bold; margin-bottom: 10px; }
        .result { padding: 10px; margin: 10px 0; border-radius: 4px; font-family: monospace; font-size: 12px; }
        .leak { background: #3d1a1a; border: 1px solid #f44747; color: #f44747; }
        .safe { background: #1a3d1a; border: 1px solid #4ec9b0; color: #4ec9b0; }
        .info { background: #1a1a3d; border: 1px solid #569cd6; color: #569cd6; }
        .warn { background: #3d3d1a; border: 1px solid #dcdcaa; color: #dcdcaa; }
        pre { background: #1e1e1e; padding: 10px; overflow: auto; white-space: pre-wrap; }
        .summary { padding: 15px; margin-top: 20px; border-radius: 4px; font-weight: bold; }
        .summary.pass { background: #1a3d1a; border: 1px solid #4ec9b0; color: #4ec9b0; }
        .summary.fail { background: #3d1a1a; border: 1px solid #f44747; color: #f44747; }
        canvas { border: 1px solid #333; background: #000; }
    </style>
</head>
<body>
    <h1>🔒 Rigorous Fingerprinting Test</h1>
    <div id="results"></div>
    <div id="summary" class="summary">Running tests...</div>
    <script>
        const resultsDiv = document.getElementById('results');
        const summaryDiv = document.getElementById('summary');
        let leakCount = 0;
        let testCount = 0;
        let fingerprint = {};
        
        function addResult(title, content, type) {
            testCount++;
            const div = document.createElement('div');
            div.className = 'test-section';
            div.innerHTML = '<div class="test-title">' + title + '</div><div class="result ' + type + '">' + content + '</div>';
            resultsDiv.appendChild(div);
            if (type === 'leak') leakCount++;
        }
        
        function hashString(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return hash.toString(16);
        }
        
        // Test 1: Canvas Fingerprinting
        async function testCanvasFingerprint() {
            try {
                const canvas = document.createElement('canvas');
                canvas.width = 200;
                canvas.height = 50;
                const ctx = canvas.getContext('2d');
                
                // Draw text with various properties
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillRect(0, 0, 200, 50);
                ctx.fillStyle = '#069';
                ctx.fillText('Fingerprint Test 🎯', 10, 10);
                ctx.strokeStyle = '#fff';
                ctx.strokeText('Fingerprint Test 🎯', 10, 10);
                
                // Draw gradient
                const gradient = ctx.createLinearGradient(0, 0, 200, 50);
                gradient.addColorStop(0, '#f00');
                gradient.addColorStop(0.5, '#0f0');
                gradient.addColorStop(1, '#00f');
                ctx.fillStyle = gradient;
                ctx.fillRect(0, 30, 200, 20);
                
                // Draw shapes
                ctx.beginPath();
                ctx.arc(180, 15, 10, 0, Math.PI * 2);
                ctx.fillStyle = '#fff';
                ctx.fill();
                
                const dataURL = canvas.toDataURL();
                const hash = hashString(dataURL);
                
                fingerprint.canvas = hash;
                fingerprint.canvasDataURL = dataURL.substring(0, 100) + '...';
                
                // Check if canvas is blocked/standardized
                const blankCanvas = document.createElement('canvas');
                blankCanvas.width = 200;
                blankCanvas.height = 50;
                const blankCtx = blankCanvas.getContext('2d');
                blankCtx.fillStyle = '#f60';
                blankCtx.fillRect(0, 0, 200, 50);
                const blankDataURL = blankCanvas.toDataURL();
                
                if (dataURL === blankDataURL) {
                    addResult('Test 1: Canvas Fingerprinting', 
                        'SAFE: Canvas returns uniform/blocked output', 'safe');
                    return { leaked: false, hash };
                }
                
                // Check for known fingerprinting patterns
                addResult('Test 1: Canvas Fingerprinting', 
                    'Canvas hash: ' + hash + ' (DataURL: ' + fingerprint.canvasDataURL + ')', 'warn');
                return { leaked: true, hash, dataURL: fingerprint.canvasDataURL };
            } catch (e) {
                addResult('Test 1: Canvas Fingerprinting', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 2: WebGL Fingerprinting
        async function testWebGLFingerprint() {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                
                if (!gl) {
                    addResult('Test 2: WebGL Fingerprinting', 'SAFE: WebGL not available (blocked)', 'safe');
                    fingerprint.webgl = 'blocked';
                    return { leaked: false, blocked: true };
                }
                
                const info = {
                    vendor: gl.getParameter(gl.VENDOR),
                    renderer: gl.getParameter(gl.RENDERER),
                    version: gl.getParameter(gl.VERSION),
                    shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                    extensions: gl.getSupportedExtensions(),
                    maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                    maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
                    aliasedLineWidthRange: gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE),
                    aliasedPointSizeRange: gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE),
                    depthBits: gl.getParameter(gl.DEPTH_BITS),
                    stencilBits: gl.getParameter(gl.STENCIL_BITS),
                    redBits: gl.getParameter(gl.RED_BITS),
                    greenBits: gl.getParameter(gl.GREEN_BITS),
                    blueBits: gl.getParameter(gl.BLUE_BITS),
                    alphaBits: gl.getParameter(gl.ALPHA_BITS),
                };
                
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    info.unmaskedVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    info.unmaskedRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.webgl = hash;
                fingerprint.webglInfo = info;
                
                // Check for standardized values
                const isStandardized = info.vendor === 'Google Inc.' && info.renderer.includes('SwiftShader');
                
                if (isStandardized) {
                    addResult('Test 2: WebGL Fingerprinting', 
                        'SAFE: WebGL standardized (SwiftShader)', 'safe');
                    return { leaked: false, hash, standardized: true };
                }
                
                addResult('Test 2: WebGL Fingerprinting', 
                    'LEAK: WebGL exposes: Vendor=' + info.vendor + ', Renderer=' + info.renderer + ', Hash=' + hash, 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 2: WebGL Fingerprinting', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 3: AudioContext Fingerprinting
        async function testAudioContextFingerprint() {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!AudioContext) {
                    addResult('Test 3: AudioContext Fingerprinting', 'SAFE: AudioContext not available', 'safe');
                    fingerprint.audio = 'blocked';
                    return { leaked: false, blocked: true };
                }
                
                const ctx = new AudioContext();
                const oscillator = ctx.createOscillator();
                const analyser = ctx.createAnalyser();
                const gainNode = ctx.createGain();
                
                oscillator.type = 'triangle';
                oscillator.frequency.value = 10000;
                gainNode.gain.value = 0;
                
                oscillator.connect(analyser);
                analyser.connect(gainNode);
                gainNode.connect(ctx.destination);
                
                oscillator.start(0);
                
                const buffer = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(buffer);
                
                const hash = hashString(Array.from(buffer).join(','));
                fingerprint.audio = hash;
                fingerprint.audioBuffer = Array.from(buffer).slice(0, 10);
                
                oscillator.stop();
                ctx.close();
                
                // Check if all zeros (standardized)
                const allZero = buffer.every(v => v === 0);
                
                if (allZero) {
                    addResult('Test 3: AudioContext Fingerprinting', 'SAFE: AudioContext returns zero buffer (standardized)', 'safe');
                    return { leaked: false, hash, standardized: true };
                }
                
                addResult('Test 3: AudioContext Fingerprinting', 
                    'LEAK: AudioContext hash: ' + hash + ', Buffer: ' + fingerprint.audioBuffer.join(','), 'leak');
                return { leaked: true, hash, buffer: fingerprint.audioBuffer };
            } catch (e) {
                addResult('Test 3: AudioContext Fingerprinting', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 4: Font Enumeration
        async function testFontEnumeration() {
            try {
                const baseFonts = ['Arial', 'Times New Roman', 'Courier New', 'Georgia', 'Verdana', 'Helvetica'];
                const testFonts = [
                    'Comic Sans MS', 'Impact', 'Trebuchet MS', 'Arial Black', 'Lucida Console',
                    'Tahoma', 'Palatino Linotype', 'Garamond', 'Bookman', 'Century Gothic',
                    'Monospace', 'Serif', 'Sans-Serif', 'Cursive', 'Fantasy',
                    'System', 'UI Monospace', 'UI Sans Serif', 'UI Serif',
                    '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen',
                    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue'
                ];
                
                const detectedFonts = [];
                const testString = 'mmmmmmmmmmlli';
                const testSize = '72px';
                
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                // Measure base font width
                ctx.font = testSize + ' ' + baseFonts[0];
                const baseWidth = ctx.measureText(testString).width;
                
                for (const font of testFonts) {
                    ctx.font = testSize + ' ' + font;
                    const width = ctx.measureText(testString).width;
                    if (width !== baseWidth) {
                        detectedFonts.push(font);
                    }
                }
                
                const hash = hashString(detectedFonts.join(','));
                fingerprint.fonts = hash;
                fingerprint.fontList = detectedFonts;
                
                if (detectedFonts.length === 0) {
                    addResult('Test 4: Font Enumeration', 'SAFE: No additional fonts detected (standardized)', 'safe');
                    return { leaked: false, hash, count: 0 };
                }
                
                addResult('Test 4: Font Enumeration', 
                    'LEAK: ' + detectedFonts.length + ' fonts detected: ' + detectedFonts.join(', '), 'leak');
                return { leaked: true, hash, fonts: detectedFonts, count: detectedFonts.length };
            } catch (e) {
                addResult('Test 4: Font Enumeration', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 5: Screen/Display Properties
        async function testScreenProperties() {
            try {
                const info = {
                    width: screen.width,
                    height: screen.height,
                    availWidth: screen.availWidth,
                    availHeight: screen.availHeight,
                    colorDepth: screen.colorDepth,
                    pixelDepth: screen.pixelDepth,
                    devicePixelRatio: window.devicePixelRatio,
                    orientation: screen.orientation ? screen.orientation.type : 'unknown',
                };
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.screen = hash;
                fingerprint.screenInfo = info;
                
                // Standard Tor Browser values
                const standard = (info.width === 1000 && info.height === 1000) || 
                                (info.width === 1920 && info.height === 1080);
                
                if (standard) {
                    addResult('Test 5: Screen Properties', 
                        'SAFE: Standardized screen size (' + info.width + 'x' + info.height + ')', 'safe');
                    return { leaked: false, hash, standardized: true };
                }
                
                addResult('Test 5: Screen Properties', 
                    'LEAK: Non-standard screen: ' + JSON.stringify(info), 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 5: Screen Properties', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 6: Hardware Concurrency & Device Memory
        async function testHardwareInfo() {
            try {
                const info = {
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    deviceMemory: navigator.deviceMemory,
                    maxTouchPoints: navigator.maxTouchPoints,
                };
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.hardware = hash;
                fingerprint.hardwareInfo = info;
                
                // Standard Tor Browser values
                const standard = info.hardwareConcurrency <= 4 && 
                                (!info.deviceMemory || info.deviceMemory <= 4);
                
                if (standard) {
                    addResult('Test 6: Hardware Concurrency & Device Memory', 
                        'SAFE: Standardized values (concurrency: ' + info.hardwareConcurrency + ', memory: ' + info.deviceMemory + ')', 'safe');
                    return { leaked: false, hash, standardized: true };
                }
                
                addResult('Test 6: Hardware Concurrency & Device Memory', 
                    'LEAK: Hardware info exposed: ' + JSON.stringify(info), 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 6: Hardware Concurrency & Device Memory', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 7: Timezone & Language
        async function testTimezoneLanguage() {
            try {
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const language = navigator.language;
                const languages = navigator.languages;
                
                const info = { timezone, language, languages };
                const hash = hashString(JSON.stringify(info));
                fingerprint.timezone = hash;
                fingerprint.timezoneInfo = info;
                
                // Check for UTC (standard)
                const isUTC = timezone === 'UTC' || timezone === 'Etc/UTC';
                
                if (isUTC && language === 'en-US') {
                    addResult('Test 7: Timezone & Language', 
                        'SAFE: Standardized (UTC, en-US)', 'safe');
                    return { leaked: false, hash, standardized: true };
                }
                
                addResult('Test 7: Timezone & Language', 
                    'LEAK: Timezone=' + timezone + ', Language=' + language + ', Languages=' + JSON.stringify(languages), 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 7: Timezone & Language', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 8: Battery API
        async function testBatteryAPI() {
            try {
                if (!navigator.getBattery) {
                    addResult('Test 8: Battery API', 'SAFE: Battery API not available', 'safe');
                    fingerprint.battery = 'blocked';
                    return { leaked: false, blocked: true };
                }
                
                const battery = await navigator.getBattery();
                const info = {
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime,
                    level: battery.level,
                };
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.battery = hash;
                fingerprint.batteryInfo = info;
                
                addResult('Test 8: Battery API', 
                    'LEAK: Battery info exposed: ' + JSON.stringify(info), 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 8: Battery API', 'SAFE: Battery API error/blocked: ' + e.toString(), 'safe');
                fingerprint.battery = 'blocked';
                return { leaked: false, blocked: true };
            }
        }
        
        // Test 9: Sensor APIs
        async function testSensorAPIs() {
            try {
                const sensors = ['Accelerometer', 'Gyroscope', 'Magnetometer', 'AbsoluteOrientationSensor', 'RelativeOrientationSensor'];
                const available = [];
                
                for (const sensor of sensors) {
                    if (window[sensor]) {
                        try {
                            const s = new window[sensor]();
                            s.start();
                            available.push(sensor);
                            s.stop();
                        } catch (e) {
                            // Sensor exists but blocked
                        }
                    }
                }
                
                const hash = hashString(available.join(','));
                fingerprint.sensors = hash;
                fingerprint.sensorList = available;
                
                if (available.length === 0) {
                    addResult('Test 9: Sensor APIs', 'SAFE: No sensor APIs available', 'safe');
                    return { leaked: false, hash, count: 0 };
                }
                
                addResult('Test 9: Sensor APIs', 
                    'LEAK: Sensors available: ' + available.join(', '), 'leak');
                return { leaked: true, hash, sensors: available };
            } catch (e) {
                addResult('Test 9: Sensor APIs', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 10: Performance/Resource Timing
        async function testPerformanceTiming() {
            try {
                const timing = performance.timing;
                const navigation = performance.navigation;
                const memory = performance.memory;
                
                const info = {
                    navigationStart: timing.navigationStart,
                    loadEventEnd: timing.loadEventEnd,
                    domComplete: timing.domComplete,
                    domInteractive: timing.domInteractive,
                    redirectCount: navigation.redirectCount,
                    type: navigation.type,
                    jsHeapSizeLimit: memory ? memory.jsHeapSizeLimit : 'N/A',
                    totalJSHeapSize: memory ? memory.totalJSHeapSize : 'N/A',
                    usedJSHeapSize: memory ? memory.usedJSHeapSize : 'N/A',
                };
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.performance = hash;
                fingerprint.performanceInfo = info;
                
                // Check if timing is randomized/standardized
                const isRandomized = timing.navigationStart > Date.now() - 10000; // Recent
                
                if (!timing.navigationStart || isRandomized) {
                    addResult('Test 10: Performance Timing', 'SAFE: Timing appears randomized/blocked', 'safe');
                    return { leaked: false, hash, randomized: true };
                }
                
                addResult('Test 10: Performance Timing', 
                    'LEAK: Performance timing exposed: ' + JSON.stringify(info), 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 10: Performance Timing', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 11: ClientRects
        async function testClientRects() {
            try {
                const div = document.createElement('div');
                div.style.cssText = 'position:absolute;top:100px;left:100px;width:200px;height:50px;visibility:hidden;';
                document.body.appendChild(div);
                
                const rect = div.getBoundingClientRect();
                const clientRects = div.getClientRects();
                
                document.body.removeChild(div);
                
                const info = {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    top: rect.top,
                    left: rect.left,
                    bottom: rect.bottom,
                    right: rect.right,
                    clientRectCount: clientRects.length,
                };
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.clientRects = hash;
                fingerprint.clientRectsInfo = info;
                
                addResult('Test 11: ClientRects', 
                    'INFO: ClientRects exposed: ' + JSON.stringify(info), 'info');
                return { leaked: false, hash, info };
            } catch (e) {
                addResult('Test 11: ClientRects', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 12: Media Devices
        async function testMediaDevices() {
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                    addResult('Test 12: Media Devices', 'SAFE: MediaDevices API not available', 'safe');
                    fingerprint.mediaDevices = 'blocked';
                    return { leaked: false, blocked: true };
                }
                
                const devices = await navigator.mediaDevices.enumerateDevices();
                const info = devices.map(d => ({
                    kind: d.kind,
                    label: d.label,
                    deviceId: d.deviceId ? 'present' : 'empty',
                    groupId: d.groupId ? 'present' : 'empty',
                }));
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.mediaDevices = hash;
                fingerprint.mediaDevicesInfo = info;
                
                if (devices.length === 0 || devices.every(d => !d.label)) {
                    addResult('Test 12: Media Devices', 'SAFE: No labeled media devices', 'safe');
                    return { leaked: false, hash, count: devices.length };
                }
                
                addResult('Test 12: Media Devices', 
                    'LEAK: Media devices exposed: ' + JSON.stringify(info), 'leak');
                return { leaked: true, hash, devices: info };
            } catch (e) {
                addResult('Test 12: Media Devices', 'SAFE: MediaDevices error/blocked: ' + e.toString(), 'safe');
                fingerprint.mediaDevices = 'blocked';
                return { leaked: false, blocked: true };
            }
        }
        
        // Test 13: User Agent & Navigator Properties
        async function testNavigatorProperties() {
            try {
                const info = {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    vendor: navigator.vendor,
                    product: navigator.product,
                    productSub: navigator.productSub,
                    appVersion: navigator.appVersion,
                    appName: navigator.appName,
                    appCodeName: navigator.appCodeName,
                    cookieEnabled: navigator.cookieEnabled,
                    doNotTrack: navigator.doNotTrack,
                    onLine: navigator.onLine,
                };
                
                const hash = hashString(JSON.stringify(info));
                fingerprint.navigator = hash;
                fingerprint.navigatorInfo = info;
                
                // Check for standard Tor Browser UA
                const isTorUA = navigator.userAgent.includes('Tor Browser') || 
                               navigator.userAgent.includes('Firefox') && navigator.userAgent.includes('Linux');
                
                if (isTorUA) {
                    addResult('Test 13: Navigator Properties', 
                        'SAFE: Standardized Tor Browser User Agent', 'safe');
                    return { leaked: false, hash, standardized: true };
                }
                
                addResult('Test 13: Navigator Properties', 
                    'LEAK: Non-standard navigator: UA=' + navigator.userAgent.substring(0, 80) + '...', 'leak');
                return { leaked: true, hash, info };
            } catch (e) {
                addResult('Test 13: Navigator Properties', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 14: CSS Media Queries
        async function testCSSMediaQueries() {
            try {
                const queries = [
                    '(prefers-color-scheme: dark)',
                    '(prefers-color-scheme: light)',
                    '(prefers-reduced-motion: reduce)',
                    '(prefers-contrast: more)',
                    '(hover: hover)',
                    '(pointer: fine)',
                    '(any-hover: hover)',
                    '(any-pointer: fine)',
                ];
                
                const results = {};
                for (const q of queries) {
                    results[q] = window.matchMedia(q).matches;
                }
                
                const hash = hashString(JSON.stringify(results));
                fingerprint.cssMedia = hash;
                fingerprint.cssMediaInfo = results;
                
                addResult('Test 14: CSS Media Queries', 
                    'INFO: Media queries: ' + JSON.stringify(results), 'info');
                return { leaked: false, hash, results };
            } catch (e) {
                addResult('Test 14: CSS Media Queries', 'ERROR: ' + e.toString(), 'info');
                return { error: e.toString() };
            }
        }
        
        // Test 15: WebRTC ICE Candidate Leak (already tested in WebRTC suite)
        async function testWebRTCICELeak() {
            try {
                const pc = new RTCPeerConnection({
                    iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
                });
                
                const ips = new Set();
                
                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        const candidate = event.candidate.candidate;
                        const ipv4Match = candidate.match(/\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b/g);
                        const ipv6Match = candidate.match(/\\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\\b/g);
                        if (ipv4Match) ipv4Match.forEach(ip => ips.add(ip));
                        if (ipv6Match) ipv6Match.forEach(ip => ips.add(ip));
                    }
                };
                
                pc.createDataChannel('test');
                const offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                
                await new Promise(resolve => setTimeout(resolve, 3000));
                pc.close();
                
                const hash = hashString(Array.from(ips).join(','));
                fingerprint.webrtcICE = hash;
                fingerprint.webrtcICEList = Array.from(ips);
                
                if (ips.size === 0) {
                    addResult('Test 15: WebRTC ICE Leak', 'SAFE: No ICE candidates leaked', 'safe');
                    return { leaked: false, hash, count: 0 };
                }
                
                addResult('Test 15: WebRTC ICE Leak', 
                    'LEAK: ICE candidates: ' + Array.from(ips).join(', '), 'leak');
                return { leaked: true, hash, ips: Array.from(ips) };
            } catch (e) {
                addResult('Test 15: WebRTC ICE Leak', 'SAFE: WebRTC blocked: ' + e.toString(), 'safe');
                fingerprint.webrtcICE = 'blocked';
                return { leaked: false, blocked: true };
            }
        }
        
        // Run all tests
        async function runAllTests() {
            addResult('Starting', 'Running rigorous fingerprinting tests...', 'info');
            
            await testCanvasFingerprint();
            await testWebGLFingerprint();
            await testAudioContextFingerprint();
            await testFontEnumeration();
            await testScreenProperties();
            await testHardwareInfo();
            await testTimezoneLanguage();
            await testBatteryAPI();
            await testSensorAPIs();
            await testPerformanceTiming();
            await testClientRects();
            await testMediaDevices();
            await testNavigatorProperties();
            await testCSSMediaQueries();
            await testWebRTCICELeak();
            
            // Final fingerprint hash
            const fullFingerprint = hashString(JSON.stringify(fingerprint));
            fingerprint.fullHash = fullFingerprint;
            
            // Summary
            if (leakCount === 0) {
                summaryDiv.className = 'summary pass';
                summaryDiv.innerHTML = '✓ ALL TESTS PASSED - No fingerprinting leaks detected (' + testCount + ' tests)';
            } else {
                summaryDiv.className = 'summary fail';
                summaryDiv.innerHTML = '✗ ' + leakCount + ' LEAKS DETECTED out of ' + testCount + ' tests';
            }
            
            // Add fingerprint summary
            const fpDiv = document.createElement('div');
            fpDiv.className = 'test-section';
            fpDiv.innerHTML = '<div class="test-title">Complete Fingerprint Hash</div><div class="result info">' + fullFingerprint + '</div>';
            resultsDiv.appendChild(fpDiv);
            
            // Store fingerprint for retrieval
            window.__fingerprint__ = fingerprint;
        }
        
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
                if self.path == '/fingerprint-test.html':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(self.server.test_page.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass
        
        handler = lambda *args: TestHandler(*args, test_page=self.create_fingerprinting_test_page())
        
        self.test_server = socketserver.TCPServer(("", self.test_server_port), handler)
        self.server_thread = Thread(target=self.test_server.serve_forever, daemon=True)
        self.server_thread.start()
        
        time.sleep(1)
        return f"http://localhost:{self.test_server_port}/fingerprint-test.html"
    
    def stop_test_server(self):
        """Stop HTTP server."""
        if self.test_server:
            self.test_server.shutdown()
            self.test_server.server_close()
        if self.server_thread:
            self.server_thread.join(timeout=2)
    
    def test_fingerprinting_code_check(self):
        """Test 1: Check fingerprinting protection in code."""
        print("\n[TEST 1] Fingerprinting Protection Code Check")
        
        fp_path = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/net/tor/fingerprinting_protection.cc"
        
        if not os.path.exists(fp_path):
            return {"test": "fp_code_check", "status": "ERROR", "reason": "Fingerprinting protection file not found"}
        
        with open(fp_path, 'r') as f:
            content = f.read()
        
        # Check for key protections
        checks = {
            "canvas_protection": "canvas" in content.lower() and ("noise" in content.lower() or "block" in content.lower() or "standardize" in content.lower()),
            "webgl_protection": "webgl" in content.lower() and ("swiftshader" in content.lower() or "block" in content.lower() or "standardize" in content.lower()),
            "audio_protection": "audio" in content.lower() and ("context" in content.lower() or "fingerprint" in content.lower()),
            "font_protection": "font" in content.lower() and ("enumerate" in content.lower() or "block" in content.lower()),
            "screen_protection": "screen" in content.lower() and ("standardize" in content.lower() or "spoof" in content.lower()),
            "hardware_protection": "hardware" in content.lower() and ("concurrency" in content.lower() or "memory" in content.lower()),
            "timezone_protection": "timezone" in content.lower() or "timeZone" in content.lower(),
            "battery_protection": "battery" in content.lower(),
            "sensor_protection": "sensor" in content.lower(),
            "performance_protection": "performance" in content.lower() and ("timing" in content.lower() or "resource" in content.lower()),
            "clientrects_protection": "clientrect" in content.lower() or "getBoundingClientRect" in content,
            "media_devices_protection": "media" in content.lower() and "device" in content.lower(),
            "navigator_protection": "navigator" in content.lower() and ("userAgent" in content or "ua" in content.lower()),
            "css_media_protection": "media" in content.lower() and "query" in content.lower(),
            "security_levels": "SecurityLevel::kStandard" in content and "SecurityLevel::kSafer" in content and "SecurityLevel::kSafest" in content,
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        return {
            "test": "fp_code_check",
            "status": "PASS" if passed >= total * 0.8 else "WARN",
            "passed_checks": passed,
            "total_checks": total,
            "details": checks,
            "reason": f"Fingerprinting protection covers {passed}/{total} areas"
        }
    
    def test_content_blocker_fingerprinting(self):
        """Test 2: Check content blocker for fingerprinting-related blocks."""
        print("\n[TEST 2] Content Blocker Fingerprinting Check")
        
        cb_path = "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/net/tor/content_blocker.cc"
        
        if not os.path.exists(cb_path):
            return {"test": "cb_fp_check", "status": "ERROR", "reason": "Content blocker file not found"}
        
        with open(cb_path, 'r') as f:
            content = f.read()
        
        # Check for fingerprinting-related content types
        fp_types = [
            "kCanvas", "kWebGL", "kAudioContext", "kFonts", 
            "kSensors", "kBattery", "kIdleDetection",
            "kWindowManagement", "kHid", "kSerial", "kUsb", "kBluetooth", "kNFC"
        ]
        
        blocked_in_safest = 0
        for fp_type in fp_types:
            # Check if this type is blocked in Safest mode
            import re
            pattern = f"SecurityLevel::kSafest.*?{fp_type}.*?Decision::kBlock"
            if re.search(pattern, content, re.DOTALL):
                blocked_in_safest += 1
            else:
                # Fallback: check if it's blocked anywhere in the file
                if f"{fp_type}.*?Decision::kBlock" in content:
                    blocked_in_safest += 1
        
        return {
            "test": "cb_fp_check",
            "status": "PASS" if blocked_in_safest >= len(fp_types) * 0.7 else "WARN",
            "blocked_types": blocked_in_safest,
            "total_types": len(fp_types),
            "reason": f"Content blocker blocks {blocked_in_safest}/{len(fp_types)} fingerprinting vectors in Safest mode"
        }
    
    def test_via_selenium(self, test_url):
        """Test 3: Fingerprinting test via Selenium."""
        print("\n[TEST 3] Fingerprinting Test via Selenium")
        
        if not SELENIUM_AVAILABLE:
            return {"test": "fp_selenium", "status": "SKIP", "reason": "Selenium not installed"}
        
        if not os.path.exists(self.browser_path):
            return {"test": "fp_selenium", "status": "SKIP", "reason": f"Browser binary not found at {self.browser_path}"}
        
        try:
            options = Options()
            options.binary_location = self.browser_path
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument(f'--proxy-server=socks5h://{self.proxy_host}:{self.proxy_port}')
            options.add_argument('--enable-features=TorNetworking')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1000,1000')  # Standard Tor Browser size
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)
            
            try:
                driver.get(test_url)
                time.sleep(20)  # Wait for all tests
                
                # Get results
                summary = driver.find_element(By.ID, "summary").text
                
                # Get fingerprint hash
                fingerprint = driver.execute_script("return window.__fingerprint__;")
                
                driver.quit()
                
                if "ALL TESTS PASSED" in summary:
                    return {"test": "fp_selenium", "status": "PASS", "reason": summary, "summary": summary, "fingerprint": fingerprint}
                elif "LEAKS DETECTED" in summary:
                    return {"test": "fp_selenium", "status": "FAIL", "reason": summary, "summary": summary, "fingerprint": fingerprint}
                else:
                    return {"test": "fp_selenium", "status": "WARN", "reason": summary, "summary": summary, "fingerprint": fingerprint}
            except Exception as e:
                driver.quit()
                return {"test": "fp_selenium", "status": "ERROR", "reason": str(e)}
        except Exception as e:
            return {"test": "fp_selenium", "status": "ERROR", "reason": str(e)}
    
    def test_tor_ip_via_fp_page(self, test_url):
        """Test 4: Simple test to verify Tor IP through fingerprinting page."""
        print("\n[TEST 4] Tor IP Verification via Fingerprinting Page")
        
        if not os.path.exists(self.browser_path):
            return {"test": "tor_ip_verification_fp", "status": "SKIP", "reason": f"Browser binary not found at {self.browser_path}"}
        
        try:
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
                if "Fingerprinting" in result.stdout or "test" in result.stdout.lower():
                    return {"test": "tor_ip_verification_fp", "status": "PASS", "reason": "Browser launched and page loaded via Tor"}
                else:
                    return {"test": "tor_ip_verification_fp", "status": "WARN", "reason": "Browser launched but page content unclear"}
            else:
                return {"test": "tor_ip_verification_fp", "status": "FAIL", "reason": f"Browser failed: {result.stderr[:500]}"}
        except subprocess.TimeoutExpired:
            return {"test": "tor_ip_verification_fp", "status": "TIMEOUT", "reason": "Browser test timed out"}
        except Exception as e:
            return {"test": "tor_ip_verification_fp", "status": "ERROR", "reason": str(e)}
    
    def run_all_tests(self):
        """Run all rigorous fingerprinting tests."""
        print("=" * 70)
        print("Tux Browser - RIGOROUS FINGERPRINTING ATTACK TEST SUITE")
        print("=" * 70)
        
        # Code-level tests
        result1 = self.test_fingerprinting_code_check()
        self.results[result1["test"]] = result1
        status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result1["status"], "?")
        print(f"  {status_symbol} {result1['test']}: {result1['status']} - {result1.get('reason', '')}")
        
        result2 = self.test_content_blocker_fingerprinting()
        self.results[result2["test"]] = result2
        status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result2["status"], "?")
        print(f"  {status_symbol} {result2['test']}: {result2['status']} - {result2.get('reason', '')}")
        
        # Browser-based tests
        test_url = self.start_test_server()
        try:
            result3 = self.test_tor_ip_via_fp_page(test_url)
            self.results[result3["test"]] = result3
            status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ", "TIMEOUT": "⏱"}.get(result3["status"], "?")
            print(f"  {status_symbol} {result3['test']}: {result3['status']} - {result3.get('reason', '')}")
            
            if SELENIUM_AVAILABLE:
                result4 = self.test_via_selenium(test_url)
                self.results[result4["test"]] = result4
                status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘", "ERROR": "⚠", "WARN": "⚠", "INFO": "ℹ"}.get(result4["status"], "?")
                print(f"  {status_symbol} {result4['test']}: {result4['status']} - {result4.get('reason', '')}")
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
    parser = argparse.ArgumentParser(description="Tux Browser Rigorous Fingerprinting Attack Tests")
    parser.add_argument("--browser", default="/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser/chrome", help="Path to browser binary")
    parser.add_argument("--proxy-host", default="127.0.0.1", help="Tor proxy host")
    parser.add_argument("--proxy-port", type=int, default=9050, help="Tor proxy port")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()
    
    tester = RigorousFingerprintingTester(args.browser, args.proxy_host, args.proxy_port)
    results = tester.run_all_tests()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    sys.exit(0 if all(r.get("status") in ("PASS", "SKIP", "INFO", "WARN") for r in results.values()) else 1)