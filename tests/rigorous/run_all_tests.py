#!/usr/bin/env python3
"""
Master Test Runner for Tux Browser Rigorous Attack Tests
Runs all attack test suites and generates a comprehensive report.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime


def run_test_script(script_path, args=None, timeout=120):
    """Run a test script and return results."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    print(f"\n{'='*70}")
    print(f"Running: {script_path}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "script": script_path,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "script": script_path,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Test timed out after {timeout} seconds",
            "success": False
        }
    except Exception as e:
        return {
            "script": script_path,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }


def main():
    print("=" * 70)
    print("Tux Browser - MASTER RIGOROUS ATTACK TEST RUNNER")
    print("=" * 70)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Test scripts to run
    test_scripts = [
        {
            "path": "/home/pie/Desktop/Tux_browser/tests/rigorous/ip_attack_tests.py",
            "name": "IP Leak Attack Tests",
            "args": ["--proxy-host", "127.0.0.1", "--proxy-port", "9050", "--control-port", "9051"],
            "timeout": 180
        },
        {
            "path": "/home/pie/Desktop/Tux_browser/tests/rigorous/webrtc_attack_tests.py",
            "name": "WebRTC Leak Attack Tests",
            "args": ["--browser", "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser/chrome", "--proxy-host", "127.0.0.1", "--proxy-port", "9050"],
            "timeout": 180
        },
        {
            "path": "/home/pie/Desktop/Tux_browser/tests/rigorous/fingerprinting_attack_tests.py",
            "name": "Fingerprinting Attack Tests",
            "args": ["--browser", "/home/pie/Desktop/Tux_browser/chromium-main/chromium-main/out/tux_browser/chrome", "--proxy-host", "127.0.0.1", "--proxy-port", "9050"],
            "timeout": 180
        },
    ]
    
    all_results = {}
    overall_start = time.time()
    
    for test in test_scripts:
        print(f"\n>>> Starting {test['name']} <<<")
        result = run_test_script(test["path"], test["args"], test["timeout"])
        all_results[test["name"]] = result
        
        if result["success"]:
            print(f">>> {test['name']}: COMPLETED SUCCESSFULLY <<<")
        else:
            print(f">>> {test['name']}: FAILED (exit code: {result['exit_code']}) <<<")
            if result["stderr"]:
                print(f"STDERR: {result['stderr'][:500]}")
    
    overall_time = time.time() - overall_start
    
    # Summary
    print("\n" + "=" * 70)
    print("MASTER TEST SUMMARY")
    print("=" * 70)
    print(f"Total time: {overall_time:.1f}s")
    print(f"Tests run: {len(test_scripts)}")
    
    for name, result in all_results.items():
        status = "PASS" if result["success"] else "FAIL"
        print(f"  {status}: {name}")
    
    # Save comprehensive report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_time_seconds": overall_time,
        "test_results": all_results
    }
    
    report_path = "/home/pie/Desktop/Tux_browser/tests/rigorous/master_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFull report saved to: {report_path}")
    
    # Exit code
    all_passed = all(r["success"] for r in all_results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()