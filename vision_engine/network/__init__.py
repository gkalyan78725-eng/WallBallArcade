"""
Vision Engine Network Package
"""

__version__ = "1.0.0"
__all__ = ["UDPSender", "WebSocketSender"]

from .udp_sender import UDPSender
from .websocket_sender import WebSocketSender
