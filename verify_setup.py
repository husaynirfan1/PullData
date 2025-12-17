#!/usr/bin/env python
"""
Verification script for PullData project setup.
Run this to ensure all components are properly configured.
"""

import os
import sys
from pathlib import Path


def check_file(path: str, description: str) -> bool:
    """Check if a file exists."""
    if Path(path).exists():
        print(f"[OK] {description}: {path}")
        return True
    else:
        print(f"[MISSING] {description}: {path}")
        return False


def check_directory(path: str, description: str) -> bool:
    """Check if a directory exists."""
    if Path(path).is_dir():
        print(f"[OK] {description}: {path}")
        return True
    else:
        print(f"[MISSING] {description}: {path}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("PullData Project Setup Verification")
    print("=" * 60)

    checks = []

    print("\n[Core Files]")
    checks.append(check_file("pyproject.toml", "Project configuration"))
    checks.append(check_file("README.md", "README"))
    checks.append(check_file("LICENSE", "License"))
    checks.append(check_file(".gitignore", "Git ignore"))
    checks.append(check_file("requirements.txt", "Requirements"))

    print("\n[Configuration]")
    checks.append(check_file("configs/default.yaml", "Default config"))
    checks.append(check_file("configs/models.yaml", "Models config"))
    checks.append(check_file(".env.example", "Environment template"))

    print("\n[Core Modules]")
    modules = [
        "pulldata",
        "pulldata/core",
        "pulldata/parsing",
        "pulldata/embedding",
        "pulldata/storage",
        "pulldata/retrieval",
        "pulldata/generation",
        "pulldata/synthesis",
        "pulldata/synthesis/formatters",
        "pulldata/pipeline",
        "pulldata/cli",
    ]

    for module in modules:
        checks.append(check_directory(module, f"Module: {module}"))
        checks.append(check_file(f"{module}/__init__.py", f"Init: {module}"))

    print("\n[Project Structure]")
    dirs = ["tests", "benchmarks", "examples", "docs", "data", "configs/templates"]
    for directory in dirs:
        checks.append(check_directory(directory, f"Directory: {directory}"))

    print("\n[Development Files]")
    checks.append(check_file("Makefile", "Makefile"))
    checks.append(check_file(".pre-commit-config.yaml", "Pre-commit config"))
    checks.append(check_file("CONTRIBUTING.md", "Contributing guide"))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100

    if passed == total:
        print(f"[SUCCESS] All checks passed! ({passed}/{total})")
        print("=" * 60)
        print("\nProject setup is complete!")
        print("\nNext steps:")
        print("  1. Create virtual environment: python -m venv venv")
        print("  2. Activate: source venv/bin/activate (or venv\\Scripts\\activate on Windows)")
        print("  3. Install: pip install -e .")
        print("  4. Verify: python -c 'import pulldata; print(pulldata.__version__)'")
        return 0
    else:
        failed = total - passed
        print(f"[WARNING] {failed} checks failed ({passed}/{total} passed, {percentage:.1f}%)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
