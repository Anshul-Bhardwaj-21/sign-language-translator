#!/usr/bin/env python3
"""
Verification script for applied fixes
Run this to verify all fixes are working correctly
"""

import sys
from pathlib import Path

def check_imports():
    """Verify critical imports work"""
    print("🔍 Checking Python imports...")
    
    try:
        import numpy as np
        print(f"  ✅ NumPy {np.__version__} imported successfully")
        
        # Check NumPy version is < 2.0
        major_version = int(np.__version__.split('.')[0])
        if major_version >= 2:
            print(f"  ⚠️  WARNING: NumPy {np.__version__} may not be compatible with MediaPipe")
            return False
        
    except ImportError as e:
        print(f"  ❌ NumPy import failed: {e}")
        return False
    
    try:
        import mediapipe as mp
        print(f"  ✅ MediaPipe {mp.__version__} imported successfully")
    except ImportError as e:
        print(f"  ❌ MediaPipe import failed: {e}")
        return False
    
    try:
        from pydantic import BaseModel, field_validator
        print(f"  ✅ Pydantic v2 imports work")
    except ImportError as e:
        print(f"  ❌ Pydantic v2 imports failed: {e}")
        print(f"     Make sure you have Pydantic >= 2.0 installed")
        return False
    
    return True


def check_files():
    """Verify all modified files exist and have correct content"""
    print("\n🔍 Checking modified files...")
    
    files_to_check = [
        ("requirements.txt", "numpy>=1.23.0,<2.0.0"),
        ("requirements-minimal.txt", "numpy>=1.23.0,<2.0.0"),
        ("frontend/src/services/FrameCaptureManager.ts", "rafId: number | null"),
        ("frontend/src/services/api.ts", "const controller = new AbortController()"),
        ("frontend/src/pages/VideoCallPage.tsx", "initializingRef"),
        ("backend/enhanced_server.py", "field_validator"),
        ("backend/server.py", 'allow_methods=["GET", "POST", "OPTIONS"]'),
    ]
    
    all_good = True
    for filepath, expected_content in files_to_check:
        path = Path(filepath)
        if not path.exists():
            print(f"  ❌ {filepath} not found")
            all_good = False
            continue
        
        content = path.read_text(encoding='utf-8')
        if expected_content in content:
            print(f"  ✅ {filepath} - Fix verified")
        else:
            print(f"  ⚠️  {filepath} - Expected content not found")
            all_good = False
    
    return all_good


def check_backend_syntax():
    """Check backend Python files for syntax errors"""
    print("\n🔍 Checking backend syntax...")
    
    backend_files = [
        "backend/server.py",
        "backend/enhanced_server.py",
    ]
    
    all_good = True
    for filepath in backend_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                compile(f.read(), filepath, 'exec')
            print(f"  ✅ {filepath} - No syntax errors")
        except SyntaxError as e:
            print(f"  ❌ {filepath} - Syntax error: {e}")
            all_good = False
    
    return all_good


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("🔧 VERIFICATION SCRIPT FOR APPLIED FIXES")
    print("=" * 60)
    
    results = []
    
    # Check 1: Imports
    results.append(("Python Imports", check_imports()))
    
    # Check 2: Files
    results.append(("Modified Files", check_files()))
    
    # Check 3: Syntax
    results.append(("Backend Syntax", check_backend_syntax()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED!")
        print("\nYour application is ready to run:")
        print("  1. Backend: python backend/server.py")
        print("  2. Frontend: cd frontend && npm run dev")
        print("\n✅ All critical fixes have been successfully applied!")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED")
        print("\nPlease review the errors above and:")
        print("  1. Check FIXES_APPLIED.md for detailed instructions")
        print("  2. Verify all files were modified correctly")
        print("  3. Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
