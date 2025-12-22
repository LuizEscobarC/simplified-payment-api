#!/usr/bin/env python3
"""
Security Scanner for Sensitive Data.

Scans the codebase for potential security issues like:
- Hard-coded passwords, API keys, tokens
- Files that shouldn't be committed
- Environment variables with sensitive data
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set

class SecurityScanner:
    """Security scanner for sensitive data in codebase."""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues: List[Dict] = []
        self.scanned_files = 0

        # Patterns for sensitive data
        self.sensitive_patterns = {
            'password': re.compile(r'\b(password|PASSWORD)\s*[=:]\s*["\']?([^"\s\';,]+)["\']?', re.IGNORECASE),
            'api_key': re.compile(r'\b(api_key|API_KEY|apikey|APIKEY)\s*[=:]\s*["\']?([^"\s\';,]+)["\']?', re.IGNORECASE),
            'secret': re.compile(r'\b(secret|SECRET)\s*[=:]\s*["\']?([^"\s\';,]+)["\']?', re.IGNORECASE),
            'token': re.compile(r'\b(token|TOKEN|auth_token|AUTH_TOKEN)\s*[=:]\s*["\']?([^"\s\';,]+)["\']?', re.IGNORECASE),
            'private_key': re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE),
            'aws_key': re.compile(r'\b(AKIA[0-9A-Z]{16})\b'),
            'generic_key': re.compile(r'\b(key|KEY)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.IGNORECASE),
        }

        # Files to exclude from scanning
        self.exclude_patterns = [
            '.git/',
            '__pycache__/',
            '.venv/',
            'node_modules/',
            '*.pyc',
            '*.pyo',
            '*.log',
            '.env.example',
            'README.md',
            'CHANGELOG.md',
        ]

        # Known safe values (false positives to ignore)
        self.safe_values = {
            'password', 'your_password_here', 'your_mysql_password_here',
            'your_mongo_password_here', 'your_redis_password_here',
            'changeme', 'example', 'placeholder', 'dummy', 'test',
            'localhost', '127.0.0.1', 'payment-mysql', 'payment-redis', 'payment-mongo'
        }

    def should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned."""
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in str(file_path):
                return False

        # Only scan text files
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:  # Binary file
                    return False
        except (IOError, OSError):
            return False

        return True

    def scan_file(self, file_path: Path) -> None:
        """Scan a single file for sensitive data."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern in self.sensitive_patterns.items():
                    matches = pattern.findall(line)
                    for match in matches:
                        if isinstance(match, tuple):
                            key, value = match
                        else:
                            key, value = pattern_name, match

                        # Skip if value is in safe list or too short
                        if (len(value) < 8 or
                            value.lower() in self.safe_values or
                            value in self.safe_values):
                            continue

                        self.issues.append({
                            'file': str(file_path),
                            'line': line_num,
                            'type': pattern_name,
                            'key': key,
                            'value': value[:20] + '...' if len(value) > 20 else value,
                            'severity': 'HIGH' if pattern_name in ['private_key', 'aws_key'] else 'MEDIUM'
                        })

        except Exception as e:
            self.issues.append({
                'file': str(file_path),
                'line': 0,
                'type': 'error',
                'key': 'scan_error',
                'value': str(e),
                'severity': 'LOW'
            })

    def scan_directory(self) -> None:
        """Scan entire directory recursively."""
        for root, dirs, files in os.walk(self.root_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in os.path.join(root, d) for pattern in self.exclude_patterns)]

            for file in files:
                file_path = Path(root) / file
                if self.should_scan_file(file_path):
                    self.scan_file(file_path)
                    self.scanned_files += 1

    def print_report(self) -> None:
        """Print security scan report."""
        print("🔍 Security Scan Report")
        print("=" * 50)
        print(f"Files scanned: {self.scanned_files}")
        print(f"Issues found: {len(self.issues)}")
        print()

        if not self.issues:
            print("✅ No security issues found!")
            return

        # Group by severity
        high_issues = [i for i in self.issues if i['severity'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['severity'] == 'MEDIUM']
        low_issues = [i for i in self.issues if i['severity'] == 'LOW']

        for severity, issues in [("HIGH", high_issues), ("MEDIUM", medium_issues), ("LOW", low_issues)]:
            if issues:
                print(f"🚨 {severity} SEVERITY ISSUES:")
                for issue in issues:
                    print(f"  📁 {issue['file']}:{issue['line']}")
                    print(f"     {issue['type']}: {issue['key']} = {issue['value']}")
                print()

    def run_scan(self) -> bool:
        """Run complete security scan."""
        print("🔍 Starting security scan...")
        self.scan_directory()
        self.print_report()
        return len([i for i in self.issues if i['severity'] in ['HIGH', 'MEDIUM']]) == 0


def main():
    """Main function."""
    scanner = SecurityScanner()
    success = scanner.run_scan()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()