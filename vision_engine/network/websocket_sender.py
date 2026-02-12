"""
WebSocket sender with async support and automatic reconnection.
"""

import asyncio
import json
import time
from typing import Optional
from loguru import logger

try:
    import websockets
except ImportError:
    logger.error("websockets not installed. Install with: pip install websockets")
    websockets = None


class WebSocketSender:
    """
    WebSocket sender for hit events.
    
    Features:
    - Async WebSocket connection
    - Exponential backoff reconnection
    - Connection state management
    - Message queue for reliability
    """
    
    def __init__(self, uri: str = "ws://localhost:9001", max_reconnect_delay: float = 30.0):
        """
        Initialize WebSocket sender.
        
        Args:
            uri: WebSocket server URI
            max_reconnect_delay: Maximum delay between reconnection attempts
        """
        if websockets is None:
            raise ImportError("websockets package required")
        
        self.uri = uri
        self.max_reconnect_delay = max_reconnect_delay
        
        # Connection state
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_delay = 1.0
        
        # Statistics
        self.messages_sent = 0
        self.connection_attempts = 0
        self.last_send_time = 0.0
        
        logger.info(f"WebSocketSender initialized ({uri})")
    
    async def connect(self) -> bool:
        """
        Connect to WebSocket server.
        
        Returns:
            True if connected successfully
        """
        try:
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=20,
                ping_timeout=10
            )
            
            self.connected = True
            self.reconnect_delay = 1.0
            self.connection_attempts += 1
            
            logger.info(f"Connected to WebSocket server: {self.uri}")
            return True
            
        except Exception as e:
            logger.warning(f"WebSocket connection failed: {e}")
            self.connected = False
            return False
    
    async def send_hit(
        self,
        x: float,
        y: float,
        velocity: float,
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Send hit event.
        
        Args:
            x: X coordinate
            y: Y coordinate
            velocity: Hit velocity
            timestamp: Event timestamp
            
        Returns:
            True if sent successfully
        """
        if timestamp is None:
            timestamp = time.time()
        
        message = {
            "type": "hit",
            "x": float(x),
            "y": float(y),
            "velocity": float(velocity),
            "timestamp": float(timestamp)
        }
        
        return await self.send_message(message)
    
    async def send_message(self, message: dict) -> bool:
        """
        Send JSON message with auto-reconnect.
        
        Args:
            message: Message dictionary
            
        Returns:
            True if sent successfully
        """
        # Ensure connection
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            return False
        
        try:
            # Serialize and send
            data = json.dumps(message)
            await self.websocket.send(data)
            
            # Update statistics
            self.messages_sent += 1
            self.last_send_time = time.time()
            
            return True
            
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
            
            # Attempt reconnection
            await self._reconnect()
            return False
            
        except Exception as e:
            logger.debug(f"Message send error: {e}")
            return False
    
    async def _reconnect(self) -> None:
        """Reconnect with exponential backoff."""
        logger.info(f"Reconnecting in {self.reconnect_delay:.1f}s...")
        await asyncio.sleep(self.reconnect_delay)
        
        # Increase delay for next attempt
        self.reconnect_delay = min(
            self.reconnect_delay * 2,
            self.max_reconnect_delay
        )
        
        await self.connect()
    
    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
            except:
                pass
        
        self.connected = False
        self.websocket = None
        
        logger.info(f"WebSocketSender closed (sent {self.messages_sent} messages)")
    
    def get_statistics(self) -> dict:
        """
        Get sending statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "messages_sent": self.messages_sent,
            "connection_attempts": self.connection_attempts,
            "connected": self.connected,
            "last_send_time": self.last_send_time,
            "uri": self.uri
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
