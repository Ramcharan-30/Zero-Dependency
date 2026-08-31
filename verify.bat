@echo off
echo ========================================
echo ZeroShrink - Zero Dependency Verification
echo ========================================
echo.

echo [1] Checking imports...
findstr /B "import from" zero_shrink.py
echo.

echo [2] Running sanity check...
python -c "import zero_shrink; print('✅ Module loads successfully!')"
echo.

echo [3] Running reproducible build...
python build.py
echo.

pause