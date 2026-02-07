"""
WebSocket connection manager for real-time updates
"""

from fastapi import WebSocket
from typing import Dict, List
import json
from datetime import datetime

class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
    async def send_personal_message(self, message: Dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
            
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                # Remove dead connections
                self.disconnect(client_id)
                
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
        
    async def disconnect_all(self):
        """Disconnect all clients"""
        for client_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[client_id].close()
            except Exception:
                pass
            self.disconnect(client_id)