"""Verify PullData installation is complete.

Run this after: pip install -e .

Usage:
    python verify_install.py
"""

import sys
from pathlib import Path


def check_module(module_name, package_name=None):
    """Check if a module can be imported."""
    package_name = package_name or module_name
    try:
        __import__(module_name)
        print(f"  [OK] {package_name}")
        return True
    except ImportError as e:
        print(f"  [FAIL] {package_name} - {e}")
        return False


def check_file(file_path):
    """Check if a file exists."""
    path = Path(file_path)
    if path.exists():
        print(f"  [OK] {file_path}")
        return True
    else:
        print(f"  [FAIL] {file_path} not found")
        return False


def main():
    print("=" * 60)
    print("PullData Installation Verification")
    print("=" * 60)
    print()

    all_ok = True

    # Check core dependencies
    print("Checking Core Dependencies:")
    all_ok &= check_module("fitz", "PyMuPDF")
    all_ok &= check_module("pdfplumber")
    all_ok &= check_module("docx", "python-docx")
    all_ok &= check_module("sentence_transformers")
    all_ok &= check_module("faiss", "faiss-cpu")
    all_ok &= check_module("transformers")
    all_ok &= check_module("torch")
    all_ok &= check_module("openai")
    print()

    # Check storage
    print("Checking Storage Dependencies:")
    all_ok &= check_module("psycopg2")
    all_ok &= check_module("chromadb")
    print()

    # Check output formatters
    print("Checking Output Format Dependencies:")
    all_ok &= check_module("openpyxl")
    all_ok &= check_module("xlsxwriter")
    all_ok &= check_module("pptx", "python-pptx")
    all_ok &= check_module("markdown2")
    all_ok &= check_module("reportlab")
    print()

    # Check Web UI dependencies
    print("Checking Web UI Dependencies:")
    all_ok &= check_module("fastapi")
    all_ok &= check_module("uvicorn")
    print()

    # Check PullData modules
    print("Checking PullData Modules:")
    all_ok &= check_module("pulldata")
    all_ok &= check_module("pulldata.core")
    all_ok &= check_module("pulldata.parsing")
    all_ok &= check_module("pulldata.storage")
    all_ok &= check_module("pulldata.retrieval")
    all_ok &= check_module("pulldata.generation")
    all_ok &= check_module("pulldata.synthesis")
    all_ok &= check_module("pulldata.pipeline")
    all_ok &= check_module("pulldata.server")
    print()

    # Check important files
    print("Checking Important Files:")
    all_ok &= check_file("run_server.py")
    all_ok &= check_file("pulldata/server/api.py")
    all_ok &= check_file("pulldata/server/static/index.html")
    all_ok &= check_file("pulldata/server/static/app.js")
    all_ok &= check_file("pulldata/server/static/styles.css")
    all_ok &= check_file("docs/WEB_UI_GUIDE.md")
    print()

    # Summary
    print("=" * 60)
    if all_ok:
        print("SUCCESS! All components installed correctly.")
        print()
        print("Next Steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Start the Web UI: python run_server.py")
        print("  3. Open browser to http://localhost:8000/ui/")
        print()
        print("Or use the Python API:")
        print("  from pulldata import PullData")
        print("  pd = PullData(project='my_project')")
        print("=" * 60)
        sys.exit(0)
    else:
        print("FAILED! Some components are missing.")
        print()
        print("Try running:")
        print("  pip install -e .")
        print()
        print("Or:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
