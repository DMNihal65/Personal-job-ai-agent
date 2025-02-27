#!/bin/bash
echo "Starting development environment..."

# Create and activate Python virtual environment for backend
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start backend
python -m uvicorn api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
cd ../Frontend/job_assistant
echo "VITE_BACKEND_URL=http://localhost:8000" > .env
npm install
npm run dev &
FRONTEND_PID=$!

echo "Development environment is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"

# Handle cleanup on script termination
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait 