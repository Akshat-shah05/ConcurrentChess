#!/bin/bash

# Start the backend server
echo "Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start the frontend server
echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "Servers started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "WebSocket: ws://localhost:8766"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for interrupt signal
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Keep script running
wait 