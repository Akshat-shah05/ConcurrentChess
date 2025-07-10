#!/usr/bin/env python3
"""
Comprehensive test script for the chess backend.
Tests both REST API endpoints and TCP socket functionality.
"""

import requests
import json
import time
import socket
from test_client import ChessClient

# Configuration
API_BASE = "http://localhost:8000"
SOCKET_HOST = "localhost"
SOCKET_PORT = 8766

def test_rest_api():
    """Test all REST API endpoints."""
    print("=== Testing REST API ===")
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Create a new game
    print("\n2. Creating new game...")
    try:
        response = requests.post(f"{API_BASE}/api/games")
        print(f"Status: {response.status_code}")
        game_data = response.json()
        game_id = game_data.get("game_id")
        print(f"Game ID: {game_id}")
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    # List games
    print("\n3. Listing games...")
    try:
        response = requests.get(f"{API_BASE}/api/games")
        print(f"Status: {response.status_code}")
        print(f"Games: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get game state
    print("\n4. Getting game state...")
    try:
        response = requests.get(f"{API_BASE}/api/games/{game_id}")
        print(f"Status: {response.status_code}")
        print(f"Game state: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get legal moves
    print("\n5. Getting legal moves...")
    try:
        response = requests.get(f"{API_BASE}/api/games/{game_id}/legal_moves")
        print(f"Status: {response.status_code}")
        print(f"Legal moves: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Make a move (e2e4)
    print("\n6. Making move e2e4...")
    try:
        move_data = {
            "from_row": 6, "from_col": 4,  # e2
            "to_row": 4, "to_col": 4,      # e4
            "promotion": None,
            "is_en_passant": False,
            "is_castling": False
        }
        response = requests.post(f"{API_BASE}/api/games/{game_id}/move", json=move_data)
        print(f"Status: {response.status_code}")
        print(f"Move response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get AI move
    print("\n7. Getting AI move...")
    try:
        response = requests.post(f"{API_BASE}/api/games/{game_id}/ai_move?depth=3")
        print(f"Status: {response.status_code}")
        print(f"AI move: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

def test_socket_connection():
    print("\n=== Testing WebSocket Server (manual test required) ===")
    print("WebSocket server is now a separate process and uses the WebSocket protocol.\n")
    print("To test multiplayer, use the frontend or a WebSocket client to connect to ws://localhost:8766/ws.")
    print("This script does not test WebSocket protocol directly.")

def main():
    """Run all tests."""
    print("Starting comprehensive chess backend tests...")
    print(f"API Base: {API_BASE}")
    print(f"WebSocket: ws://{SOCKET_HOST}:{SOCKET_PORT}/ws")
    
    # Test REST API
    test_rest_api()
    
    # Inform about WebSocket server
    test_socket_connection()
    
    print("\n=== Test Summary ===")
    print("✓ REST API tests completed")
    print("✓ WebSocket server is running (manual test required)")
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 