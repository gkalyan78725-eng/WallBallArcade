"""
Multi-threaded camera capture with queue management for low-latency video processing.
"""

import cv2
import threading
import queue
import time
from typing import Optional, Tuple
from loguru import logger


class CameraManager:
    """
    Multi-threaded camera capture manager with automatic frame dropping.
    
    Features:
    - Background thread for continuous capture
    - Queue with maxsize for low latency
    - Automatic frame dropping when queue full
    - Statistics tracking (total frames, dropped frames)
    - Support for multiple backends (DSHOW, V4L2, MSMF)
    - Context manager support
    """
    
    def __init__(
        self,
        camera_index: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 60,
        buffer_size: int = 1,
        backend: str = "DSHOW"
    ):
        """
        Initialize camera manager.
        
        Args:
            camera_index: Camera device index
            width: Frame width
            height: Frame height
            fps: Target frames per second
            buffer_size: Internal buffer size (1-2 recommended for low latency)
            backend: Camera backend (DSHOW for Windows, V4L2 for Linux, MSMF)
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.buffer_size = buffer_size
        self.backend = backend
        
        # Thread management
        self.capture_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
        
        # Statistics
        self.total_frames = 0
        self.dropped_frames = 0
        self.start_time = time.time()
        
        # OpenCV capture object
        self.cap: Optional[cv2.VideoCapture] = None
        
        logger.info(f"CameraManager initialized: {width}x{height}@{fps}fps")
    
    def start(self) -> bool:
        """
        Start camera capture.
        
        Returns:
            True if successful, False otherwise
        """
        # Select backend
        backend_map = {
            "DSHOW": cv2.CAP_DSHOW,
            "V4L2": cv2.CAP_V4L2,
            "MSMF": cv2.CAP_MSMF,
            "ANY": cv2.CAP_ANY
        }
        backend_code = backend_map.get(self.backend, cv2.CAP_ANY)
        
        # Open camera
        self.cap = cv2.VideoCapture(self.camera_index, backend_code)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
        
        # Verify settings
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Camera opened: {actual_width}x{actual_height}@{actual_fps}fps")
        
        # Start capture thread
        self.stop_event.clear()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        logger.info("Camera capture thread started")
        return True
    
    def _capture_loop(self) -> None:
        """Background thread for continuous frame capture."""
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning("Failed to read frame from camera")
                continue
            
            self.total_frames += 1
            
            # Try to add frame to queue, drop if full
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                self.dropped_frames += 1
                # Drop oldest frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame)
                except:
                    pass
    
    def get_frame(self, timeout: float = 0.1) -> Optional[Tuple[bool, any]]:
        """
        Get the latest frame from queue.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            Tuple of (success, frame) or None if timeout
        """
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return True, frame
        except queue.Empty:
            return False, None
    
    def stop(self) -> None:
        """Stop camera capture and cleanup resources."""
        logger.info("Stopping camera capture...")
        
        # Signal thread to stop
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Camera capture stopped")
    
    def get_statistics(self) -> dict:
        """
        Get capture statistics.
        
        Returns:
            Dictionary with statistics
        """
        elapsed_time = time.time() - self.start_time
        avg_fps = self.total_frames / elapsed_time if elapsed_time > 0 else 0
        drop_rate = (self.dropped_frames / self.total_frames * 100) if self.total_frames > 0 else 0
        
        return {
            "total_frames": self.total_frames,
            "dropped_frames": self.dropped_frames,
            "drop_rate": drop_rate,
            "avg_fps": avg_fps,
            "elapsed_time": elapsed_time
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
