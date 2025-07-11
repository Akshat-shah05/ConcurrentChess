import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8766/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Test creating a game
            create_message = {"type": "create_game"}
            await websocket.send(json.dumps(create_message))
            print("Sent create_game message")
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
            # Test getting games list
            get_games_message = {"type": "get_games"}
            await websocket.send(json.dumps(get_games_message))
            print("Sent get_games message")
            
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 