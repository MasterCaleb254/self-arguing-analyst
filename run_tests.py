# run_tests.py
#!/usr/bin/env python
"""Test runner script"""
import sys
import subprocess
import argparse

def run_tests(test_path=None, verbose=False, coverage=False):
    """Run pytest with specified options"""
    cmd = [sys.executable, "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for Self-Arguing Multi-Agent Analyst")
    parser.add_argument("--path", help="Specific test file or directory to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    exit_code = run_tests(
        test_path=args.path,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)