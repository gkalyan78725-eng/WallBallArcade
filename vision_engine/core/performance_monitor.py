"""
Performance monitoring for FPS, frame time, and resource utilization.
"""

import time
import psutil
from typing import List, Optional
from loguru import logger

try:
    import torch
except ImportError:
    torch = None
    logger.warning("torch not available, GPU monitoring disabled")


class PerformanceMonitor:
    """
    Monitor system and application performance.
    
    Features:
    - FPS tracking with rolling average
    - Frame time measurement
    - GPU utilization (if CUDA available)
    - Memory monitoring
    - Latency tracking
    """
    
    def __init__(self, window_size: int = 60, target_fps: int = 60):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Number of samples for rolling average
            target_fps: Target FPS for performance comparison
        """
        self.window_size = window_size
        self.target_fps = target_fps
        
        # FPS tracking
        self.frame_times: List[float] = []
        self.last_frame_time = time.time()
        
        # Statistics
        self.total_frames = 0
        self.start_time = time.time()
        
        # GPU availability
        self.gpu_available = torch is not None and torch.cuda.is_available()
        
        logger.info(f"PerformanceMonitor initialized (GPU: {self.gpu_available})")
    
    def start_frame(self) -> None:
        """Mark the start of a new frame."""
        self.last_frame_time = time.time()
    
    def end_frame(self) -> None:
        """Mark the end of a frame and update statistics."""
        current_time = time.time()
        frame_time = current_time - self.last_frame_time
        
        self.frame_times.append(frame_time)
        self.total_frames += 1
        
        # Keep only last window_size measurements
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)
        
        self.last_frame_time = current_time
    
    def get_fps(self) -> float:
        """
        Get current FPS.
        
        Returns:
            Average FPS over window
        """
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
    
    def get_frame_time_ms(self) -> float:
        """
        Get average frame time in milliseconds.
        
        Returns:
            Average frame time in ms
        """
        if not self.frame_times:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return avg_frame_time * 1000
    
    def get_gpu_utilization(self) -> Optional[float]:
        """
        Get GPU utilization percentage.
        
        Returns:
            GPU utilization (0-100) or None if not available
        """
        if not self.gpu_available:
            return None
        
        try:
            # Get GPU memory usage as a proxy for utilization
            memory_allocated = torch.cuda.memory_allocated(0)
            memory_reserved = torch.cuda.memory_reserved(0)
            
            if memory_reserved > 0:
                return (memory_allocated / memory_reserved) * 100
            return 0.0
        except Exception as e:
            logger.debug(f"GPU utilization error: {e}")
            return None
    
    def get_memory_usage(self) -> dict:
        """
        Get system memory usage.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
                "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                "percent": process.memory_percent()
            }
        except Exception as e:
            logger.debug(f"Memory usage error: {e}")
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}
    
    def get_gpu_memory(self) -> Optional[dict]:
        """
        Get GPU memory usage.
        
        Returns:
            Dictionary with GPU memory statistics or None
        """
        if not self.gpu_available:
            return None
        
        try:
            allocated = torch.cuda.memory_allocated(0) / 1024 / 1024  # MB
            reserved = torch.cuda.memory_reserved(0) / 1024 / 1024    # MB
            
            return {
                "allocated_mb": allocated,
                "reserved_mb": reserved,
                "free_mb": reserved - allocated
            }
        except Exception as e:
            logger.debug(f"GPU memory error: {e}")
            return None
    
    def get_overall_stats(self) -> dict:
        """
        Get comprehensive performance statistics.
        
        Returns:
            Dictionary with all performance metrics
        """
        elapsed_time = time.time() - self.start_time
        overall_fps = self.total_frames / elapsed_time if elapsed_time > 0 else 0
        
        stats = {
            "current_fps": self.get_fps(),
            "overall_fps": overall_fps,
            "frame_time_ms": self.get_frame_time_ms(),
            "total_frames": self.total_frames,
            "elapsed_time": elapsed_time,
            "target_fps": self.target_fps,
            "fps_ratio": self.get_fps() / self.target_fps if self.target_fps > 0 else 0,
            "memory": self.get_memory_usage()
        }
        
        # Add GPU stats if available
        gpu_util = self.get_gpu_utilization()
        if gpu_util is not None:
            stats["gpu_utilization"] = gpu_util
        
        gpu_memory = self.get_gpu_memory()
        if gpu_memory is not None:
            stats["gpu_memory"] = gpu_memory
        
        return stats
    
    def is_performance_adequate(self, threshold: float = 0.8) -> bool:
        """
        Check if performance meets target.
        
        Args:
            threshold: Minimum ratio of current FPS to target FPS (0-1)
            
        Returns:
            True if performance is adequate
        """
        current_fps = self.get_fps()
        return (current_fps / self.target_fps) >= threshold if self.target_fps > 0 else True
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.frame_times.clear()
        self.total_frames = 0
        self.start_time = time.time()
        self.last_frame_time = time.time()
        
        logger.debug("Performance monitor reset")
    
    def log_stats(self) -> None:
        """Log current performance statistics."""
        stats = self.get_overall_stats()
        
        logger.info(
            f"Performance: {stats['current_fps']:.1f} FPS "
            f"({stats['frame_time_ms']:.2f}ms) | "
            f"Memory: {stats['memory']['rss_mb']:.1f}MB"
        )
        
        if "gpu_memory" in stats:
            logger.info(
                f"GPU Memory: {stats['gpu_memory']['allocated_mb']:.1f}MB allocated, "
                f"{stats['gpu_memory']['reserved_mb']:.1f}MB reserved"
            )
