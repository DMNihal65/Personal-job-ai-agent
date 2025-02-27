@echo off
echo Starting development environment...

:: Check for Python installation
python --version 2>NUL
if errorlevel 1 (
    echo Python is not installed! Please install Python 3.9 or later.
    exit /b 1
)

:: Check for Node.js installation
node --version 2>NUL
if errorlevel 1 (
    echo Node.js is not installed! Please install Node.js 20 or later.
    exit /b 1
)

:: Check for Chrome installation
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>&1
if errorlevel 1 (
    echo Google Chrome is not installed! Please install Chrome browser.
    exit /b 1
)

:: Create and activate Python virtual environment for backend
cd Backend
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing Python dependencies...
pip install -r requirements.txt

:: Ensure personal_resume_data.json exists
if not exist personal_resume_data.json (
    echo {} > personal_resume_data.json
)

:: Start backend
echo Starting backend server...
start cmd /k "python -m uvicorn api:app --host 0.0.0.0 --port 8000"

:: Wait for backend to start
timeout /t 5

:: Start frontend
cd ../Frontend/job_assistant
echo Setting up frontend environment...
echo VITE_BACKEND_URL=http://localhost:8000 > .env
echo Installing Node.js dependencies...
call npm install
echo Starting frontend development server...
start cmd /k "npm run dev"

echo Development environment is running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Press Ctrl+C in respective windows to stop the servers
pause 