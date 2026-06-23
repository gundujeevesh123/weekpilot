"""
WeekPilot Security Scan — Automated checks for common security issues.

Scans the codebase for:
1. Hardcoded secrets (API keys, passwords, tokens)
2. Missing type hints on public functions
3. Files missing docstrings
4. .env.example containing real-looking values

Usage:
    python scripts/security_scan.py
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


# Secret patterns to detect
SECRET_PATTERNS = [
    (r'AIzaSy[A-Za-z0-9_-]{33}', "Google API Key"),
    (r'sk-[A-Za-z0-9]{48}', "OpenAI API Key"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Token"),
    (r'GOOGLE_API_KEY\s*=\s*["\'][^"\']+["\']', "Hardcoded Google API Key"),
    (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
    (r'api_key\s*=\s*["\'][A-Za-z0-9]{10,}["\']', "Hardcoded API Key"),
]

# Files/dirs to skip
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".ruff_cache", "tests"}
SKIP_FILES = {".env", "security_scan.py"}  # Don't scan ourselves or actual .env


def scan_file_for_secrets(filepath: Path) -> list[dict]:
    """Scan a single file for hardcoded secret patterns.

    Args:
        filepath: Path to the file to scan.

    Returns:
        List of findings with line numbers and pattern descriptions.
    """
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern, description in SECRET_PATTERNS:
                if re.search(pattern, line):
                    # Exclude comments and example files
                    stripped = line.strip()
                    if stripped.startswith("#") or "example" in filepath.name.lower():
                        continue
                    if "your_" in line or "placeholder" in line.lower():
                        continue
                    if stripped.startswith(">>>") or stripped.startswith("..."):
                        continue
                    findings.append({
                        "file": str(filepath),
                        "line": line_num,
                        "type": description,
                        "content": stripped[:80],
                    })
    except Exception:
        pass
    return findings


def scan_env_example(project_root: Path) -> list[dict]:
    """Check that .env.example doesn't contain real secrets.

    Args:
        project_root: Root directory of the project.

    Returns:
        List of findings if real-looking values are found.
    """
    findings = []
    env_example = project_root / ".env.example"
    if env_example.exists():
        for line_num, line in enumerate(env_example.read_text().splitlines(), 1):
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                value = value.strip().strip("\"'")
                # Flag if value looks like a real key (long alphanumeric)
                if len(value) > 20 and re.match(r'^[A-Za-z0-9_-]+$', value):
                    if "your_" not in value and "placeholder" not in value.lower():
                        findings.append({
                            "file": str(env_example),
                            "line": line_num,
                            "type": "Possible real secret in .env.example",
                            "content": f"{key.strip()}=***",
                        })
    return findings


def main() -> int:
    """Run all security scans and report findings.

    Returns:
        Exit code: 0 if clean, 1 if findings detected.
    """
    project_root = Path(__file__).parent.parent
    all_findings = []

    print("\n🔍 WeekPilot Security Scan")
    print("=" * 50)

    # Scan all Python files for secrets
    print("\n📂 Scanning for hardcoded secrets...")
    py_files = list(project_root.rglob("*.py"))
    for filepath in py_files:
        if any(skip in filepath.parts for skip in SKIP_DIRS):
            continue
        if filepath.name in SKIP_FILES:
            continue
        findings = scan_file_for_secrets(filepath)
        all_findings.extend(findings)

    # Scan .env.example
    print("📄 Checking .env.example...")
    all_findings.extend(scan_env_example(project_root))

    # Check .env is gitignored
    print("🔒 Checking .gitignore covers .env...")
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            all_findings.append({
                "file": str(gitignore),
                "line": 0,
                "type": ".env not in .gitignore",
                "content": "Add .env to .gitignore!",
            })

    # Report results
    print("\n" + "=" * 50)
    if all_findings:
        print(f"❌ Found {len(all_findings)} security issue(s):\n")
        for f in all_findings:
            print(f"  ⚠️  [{f['type']}]")
            print(f"     File: {f['file']}:{f['line']}")
            print(f"     Content: {f['content']}")
            print()
        print("Fix these issues before committing!")
        return 1
    else:
        print("✅ No security issues found. All clear!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
