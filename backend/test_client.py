#!/usr/bin/env python3
"""
Simple test client for the chess backend.
Demonstrates TCP socket communication with the chess server.
"""

import socket
import json
import time

class ChessClient:
    def __init__(self, host='localhost', port=8766):
        self.host = host
        self.port = port
    
    def send_message(self, message_type, data=None):
        """Send a message to the server and receive response."""
        message = {"type": message_type}
        if data:
            message.update(data)
        
        message_str = json.dumps(message) + "\n"
        print(f"Sending: {message_str.strip()}")
        
        # Create a new connection for each message
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            sock.connect((self.host, self.port))
            sock.sendall(message_str.encode('utf-8'))
            
            # Receive response
            response_data = b""
            sock.settimeout(5)
            
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b'\n' in response_data:
                    break
            
            if not response_data:
                return {"error": "No response received"}
            
            response_str = response_data.decode('utf-8').strip()
            print(f"Received: {response_str}")
            
            if not response_str:
                return {"error": "Empty response"}
            
            return json.loads(response_str)
            
        except socket.timeout:
            return {"error": "Socket timeout"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {e}"}
        except Exception as e:
            return {"error": f"Socket error: {e}"}
        finally:
            sock.close()
    
    def get_board_state(self, game_id="default"):
        """Get the current board state."""
        return self.send_message("board_state", {"game_id": game_id})
    
    def get_legal_moves(self, game_id="default"):
        """Get legal moves for the current position."""
        return self.send_message("legal_moves", {"game_id": game_id})
    
    def make_move(self, move_data, game_id="default"):
        """Make a move."""
        return self.send_message("move", {
            "game_id": game_id,
            "move": move_data
        })
    
    def get_ai_move(self, game_id="default", depth=4):
        """Get an AI move."""
        return self.send_message("ai_move", {
            "game_id": game_id,
            "depth": depth
        })
    
    def get_evaluation(self, game_id="default"):
        """Get position evaluation."""
        return self.send_message("evaluation", {"game_id": game_id})

def test_basic_functionality():
    """Test basic chess functionality."""
    client = ChessClient()
    
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

def test_simple_connection():
    """Test simple connection and basic message."""
    print("\n=== Testing Simple Connection ===")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 8766))
        print("✓ Connected to socket server")
        
        # Send a simple board state request
        message = {"type": "board_state", "game_id": "test"}
        message_str = json.dumps(message) + "\n"
        print(f"Sending: {message_str.strip()}")
        
        sock.sendall(message_str.encode('utf-8'))
        
        # Receive response
        response = sock.recv(4096).decode('utf-8')
        print(f"Received: {response.strip()}")
        
        # Parse response
        try:
            parsed = json.loads(response.strip())
            print(f"Parsed response: {json.dumps(parsed, indent=2)}")
        except json.JSONDecodeError:
            print("Failed to parse response as JSON")
        
        sock.close()
        
    except Exception as e:
        print(f"✗ Connection test failed: {e}")

if __name__ == "__main__":
    print("Testing chess backend...")
    
    # Test simple connection first
    test_simple_connection()
    
    # Test full functionality
    test_basic_functionality()
    
    print("\nTest completed!") 