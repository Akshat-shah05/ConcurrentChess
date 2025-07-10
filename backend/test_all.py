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
        moves = response.json().get("moves", [])
        print(f"Found {len(moves)} legal moves")
        if moves:
            print(f"First move: {moves[0]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Make a move (e2e4)
    print("\n6. Making move e2e4...")
    try:
        move_data = {
            "from_row": 6,
            "from_col": 4,
            "to_row": 4,
            "to_col": 4,
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
    
    return game_id

def test_tcp_socket():
    """Test TCP socket functionality."""
    print("\n=== Testing TCP Socket ===")
    
    client = ChessClient(SOCKET_HOST, SOCKET_PORT)
    
    try:
        # Get initial board state
        print("\n1. Getting initial board state...")
        response = client.get_board_state()
        print(f"Response: {json.dumps(response, indent=2)}")
        
        # Get legal moves
        print("\n2. Getting legal moves...")
        response = client.get_legal_moves()
        moves = response.get('moves', [])
        print(f"Found {len(moves)} legal moves")
        if moves:
            print(f"First move: {moves[0]}")
        
        # Get evaluation
        print("\n3. Getting position evaluation...")
        response = client.get_evaluation()
        print(f"Evaluation: {response.get('evaluation', 'N/A')}")
        
        # Make a move (e2e4)
        print("\n4. Making move e2e4...")
        move_data = {
            "from_row": 6, "from_col": 4,  # e2
            "to_row": 4, "to_col": 4,      # e4
            "promotion": None,
            "is_en_passant": False,
            "is_castling": False
        }
        response = client.make_move(move_data)
        print(f"Move response: {json.dumps(response, indent=2)}")
        
        # Get AI move
        print("\n5. Getting AI move...")
        response = client.get_ai_move(depth=3)
        print(f"AI move: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_socket_connection():
    """Test basic socket connectivity."""
    print("\n=== Testing Socket Connectivity ===")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((SOCKET_HOST, SOCKET_PORT))
        sock.close()
        
        if result == 0:
            print("✓ Socket server is running and accessible")
        else:
            print("✗ Socket server is not accessible")
    except Exception as e:
        print(f"✗ Socket connection error: {e}")

def main():
    """Run all tests."""
    print("Starting comprehensive chess backend tests...")
    print(f"API Base: {API_BASE}")
    print(f"Socket: {SOCKET_HOST}:{SOCKET_PORT}")
    
    # Test socket connectivity first
    test_socket_connection()
    
    # Test REST API
    game_id = test_rest_api()
    
    # Test TCP socket
    test_tcp_socket()
    
    print("\n=== Test Summary ===")
    print("✓ REST API tests completed")
    print("✓ TCP Socket tests completed")
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 