#!/bin/bash

# Quick test script for chess backend
# Make sure the server is running: python main.py

echo "=== Chess Backend Quick Tests ==="
echo "Make sure the server is running: python main.py"
echo ""

# Test REST API endpoints
echo "1. Testing REST API endpoints..."

echo "Root endpoint:"
curl -s http://localhost:8000/ | jq .

echo ""
echo "Create game:"
curl -s -X POST http://localhost:8000/api/games | jq .

echo ""
echo "List games:"
curl -s http://localhost:8000/api/games | jq .

# Get the game ID from the create response
GAME_ID=$(curl -s -X POST http://localhost:8000/api/games | jq -r '.game_id')
echo ""
echo "Using game ID: $GAME_ID"

echo ""
echo "Get game state:"
curl -s http://localhost:8000/api/games/$GAME_ID | jq .

echo ""
echo "Get legal moves:"
curl -s http://localhost:8000/api/games/$GAME_ID/legal_moves | jq .

echo ""
echo "Make move e2e4:"
curl -s -X POST http://localhost:8000/api/games/$GAME_ID/move \
  -H "Content-Type: application/json" \
  -d '{
    "from_row": 6,
    "from_col": 4,
    "to_row": 4,
    "to_col": 4,
    "promotion": null,
    "is_en_passant": false,
    "is_castling": false
  }' | jq .

echo ""
echo "Get AI move:"
curl -s -X POST http://localhost:8000/api/games/$GAME_ID/ai_move?depth=3 | jq .

echo ""
echo "=== TCP Socket Tests ==="
echo "Testing socket connection..."
python test_client.py

echo ""
echo "=== Manual Socket Tests ==="
echo "You can also test manually with netcat:"
echo "echo '{\"type\": \"board_state\", \"game_id\": \"test\"}' | nc localhost 8766"
echo "echo '{\"type\": \"legal_moves\", \"game_id\": \"test\"}' | nc localhost 8766"
echo "echo '{\"type\": \"move\", \"game_id\": \"test\", \"move\": {\"from_row\": 6, \"from_col\": 4, \"to_row\": 4, \"to_col\": 4, \"promotion\": null, \"is_en_passant\": false, \"is_castling\": false}}' | nc localhost 8766"
echo "echo '{\"type\": \"ai_move\", \"game_id\": \"test\", \"depth\": 3}' | nc localhost 8766"

echo ""
echo "=== Test Complete ===" 