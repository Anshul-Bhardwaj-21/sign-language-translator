@echo off
echo ============================================================
echo FIXING NUMPY VERSION FOR MEDIAPIPE COMPATIBILITY
echo ============================================================
echo.

echo Step 1: Uninstalling NumPy 2.x...
pip uninstall -y numpy

echo.
echo Step 2: Installing NumPy 1.26.4 (compatible with MediaPipe)...
pip install "numpy>=1.23.0,<2.0.0"

echo.
echo Step 3: Verifying installation...
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"

echo.
echo Step 4: Testing MediaPipe import...
python -c "import mediapipe; print('MediaPipe imported successfully!')"

echo.
echo ============================================================
echo DONE! NumPy version fixed.
echo ============================================================
echo.
echo You can now run: python verify_fixes.py
pause
