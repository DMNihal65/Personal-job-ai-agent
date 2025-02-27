@echo off
echo Starting development environment...

:: Create and activate Python virtual environment for backend
cd Backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

:: Start backend
start cmd /k "python -m uvicorn api:app --host 0.0.0.0 --port 8000"

:: Wait for backend to start
timeout /t 5

:: Start frontend
cd ../Frontend/job_assistant
echo VITE_BACKEND_URL=http://localhost:8000 > .env
npm install
start cmd /k "npm run dev"

echo Development environment is running!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173 