#!/bin/bash

# Start REST API backend
printf "Starting REST API backend on http://localhost:8000 ...\n"
(cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000) &
REST_PID=$!

# Start WebSocket backend
printf "Starting WebSocket backend on ws://localhost:8766/ws ...\n"
(cd backend && python -m uvicorn websocket_server:app --host 0.0.0.0 --port 8766) &
WS_PID=$!

# Start frontend
printf "Starting frontend dev server ...\n"
npm --prefix frontend run dev &
FRONTEND_PID=$!

trap 'kill $REST_PID $WS_PID $FRONTEND_PID' SIGINT

wait $REST_PID $WS_PID $FRONTEND_PID 