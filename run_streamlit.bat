@echo off
REM ============================================================================
REM Streamlit Launcher with UTF-8 Encoding Support
REM 
REM This batch file sets the correct encoding and runs Streamlit
REM without Unicode errors on Windows.
REM
REM Double-click this file to run the app!
REM ============================================================================

echo.
echo ========================================
echo   Starting Streamlit App
echo ========================================
echo.

REM Set console to UTF-8 code page (65001)
chcp 65001 > nul

REM Set Python encoding environment variables
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat

REM Verify activation
if errorlevel 1 (
    echo ERROR: Could not activate virtual environment!
    echo Please make sure venv exists in this directory.
    pause
    exit /b 1
)

echo [2/3] Virtual environment activated!
echo.

REM Run Streamlit with UTF-8 mode
echo [3/3] Launching Streamlit...
echo.
echo ========================================
echo   App will open in your browser
echo   Press Ctrl+C to stop the server
echo ========================================
echo.

python -X utf8 -m streamlit run test_streamlit_mapper_safe.py

REM If Streamlit exits, pause so you can see any errors
echo.
echo ========================================
echo   Streamlit stopped
echo ========================================
pause