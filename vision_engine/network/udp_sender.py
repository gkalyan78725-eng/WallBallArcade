"""
UDP network sender for low-latency hit event transmission.
"""

import socket
import json
import time
from typing import Optional, Tuple
from loguru import logger


class UDPSender:
    """
    UDP sender for hit events.
    
    Features:
    - Non-blocking UDP socket
    - JSON message serialization
    - Automatic error handling
    - Connection monitoring
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9000):
        """
        Initialize UDP sender.
        
        Args:
            host: Target host address
            port: Target port number
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        
        # Statistics
        self.messages_sent = 0
        self.errors = 0
        self.last_send_time = 0.0
        
        self._initialize_socket()
        
        logger.info(f"UDPSender initialized ({host}:{port})")
    
    def _initialize_socket(self) -> bool:
        """
        Initialize UDP socket.
        
        Returns:
            True if successful
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Set non-blocking mode
            self.socket.setblocking(False)
            
            # Set socket options
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
            logger.debug("UDP socket initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize socket: {e}")
            return False
    
    def send_hit(
        self,
        x: float,
        y: float,
        velocity: float,
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Send hit event.
        
        Args:
            x: X coordinate (normalized 0-1 or pixel coordinate)
            y: Y coordinate (normalized 0-1 or pixel coordinate)
            velocity: Hit velocity magnitude
            timestamp: Event timestamp (uses current time if None)
            
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
        
        return self.send_message(message)
    
    def send_message(self, message: dict) -> bool:
        """
        Send generic JSON message.
        
        Args:
            message: Message dictionary
            
        Returns:
            True if sent successfully
        """
        if self.socket is None:
            logger.warning("Socket not initialized")
            return False
        
        try:
            # Serialize to JSON
            data = json.dumps(message).encode('utf-8')
            
            # Send via UDP
            self.socket.sendto(data, (self.host, self.port))
            
            # Update statistics
            self.messages_sent += 1
            self.last_send_time = time.time()
            
            return True
            
        except socket.error as e:
            # Non-blocking socket may raise errors
            if e.errno != socket.errno.EWOULDBLOCK:
                logger.debug(f"UDP send error: {e}")
                self.errors += 1
            return False
            
        except Exception as e:
            logger.debug(f"Message send error: {e}")
            self.errors += 1
            return False
    
    def get_statistics(self) -> dict:
        """
        Get sending statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "error_rate": self.errors / self.messages_sent if self.messages_sent > 0 else 0,
            "last_send_time": self.last_send_time,
            "host": self.host,
            "port": self.port
        }
    
    def close(self) -> None:
        """Close socket and cleanup."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        logger.info(f"UDPSender closed (sent {self.messages_sent} messages)")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
