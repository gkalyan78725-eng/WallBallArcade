"""
Debug visualization for development and troubleshooting.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from loguru import logger


class DebugVisualizer:
    """
    Debug visualization overlay.
    
    Features:
    - Bounding boxes with labels
    - Trajectory lines
    - Hit markers
    - FPS overlay
    - Calibration grid
    - Information panel
    """
    
    def __init__(
        self,
        show_bounding_box: bool = True,
        show_trajectory: bool = True,
        show_fps: bool = True,
        show_info: bool = True
    ):
        """
        Initialize debug visualizer.
        
        Args:
            show_bounding_box: Show detection bounding boxes
            show_trajectory: Show trajectory lines
            show_fps: Show FPS counter
            show_info: Show information panel
        """
        self.show_bounding_box = show_bounding_box
        self.show_trajectory = show_trajectory
        self.show_fps = show_fps
        self.show_info = show_info
        
        # Display state
        self.hit_markers: List[Tuple[Tuple[int, int], float]] = []  # (position, timestamp)
        self.hit_marker_duration = 1.0  # seconds
        
        logger.info("DebugVisualizer initialized")
    
    def draw_detection(
        self,
        frame: np.ndarray,
        bbox: Tuple[float, float, float, float],
        confidence: float,
        label: str = "Ball"
    ) -> np.ndarray:
        """
        Draw detection bounding box.
        
        Args:
            frame: Input frame
            bbox: Bounding box (x1, y1, x2, y2)
            confidence: Detection confidence
            label: Label text
            
        Returns:
            Frame with overlay
        """
        if not self.show_bounding_box:
            return frame
        
        x1, y1, x2, y2 = map(int, bbox)
        
        # Draw box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw label
        text = f"{label} {confidence:.2f}"
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        
        cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w, y1), (0, 255, 0), -1)
        cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def draw_trajectory(
        self,
        frame: np.ndarray,
        trajectory: List[Tuple[float, float]],
        color: Tuple[int, int, int] = (255, 0, 0)
    ) -> np.ndarray:
        """
        Draw trajectory line.
        
        Args:
            frame: Input frame
            trajectory: List of (x, y) points
            color: Line color (B, G, R)
            
        Returns:
            Frame with overlay
        """
        if not self.show_trajectory or len(trajectory) < 2:
            return frame
        
        # Draw lines between consecutive points
        points = [(int(x), int(y)) for x, y in trajectory]
        
        for i in range(len(points) - 1):
            # Fade older points
            alpha = (i + 1) / len(points)
            point_color = tuple(int(c * alpha) for c in color)
            
            thickness = max(1, int(3 * alpha))
            cv2.line(frame, points[i], points[i + 1], point_color, thickness)
        
        # Draw current position
        if points:
            cv2.circle(frame, points[-1], 5, (0, 255, 255), -1)
        
        return frame
    
    def add_hit_marker(self, position: Tuple[float, float], timestamp: float) -> None:
        """
        Add hit marker for display.
        
        Args:
            position: Hit position (x, y)
            timestamp: Hit timestamp
        """
        self.hit_markers.append(((int(position[0]), int(position[1])), timestamp))
    
    def draw_hit_markers(self, frame: np.ndarray, current_time: float) -> np.ndarray:
        """
        Draw hit markers with fade effect.
        
        Args:
            frame: Input frame
            current_time: Current timestamp
            
        Returns:
            Frame with overlay
        """
        # Remove old markers
        self.hit_markers = [
            (pos, t) for pos, t in self.hit_markers
            if current_time - t < self.hit_marker_duration
        ]
        
        # Draw markers
        for position, timestamp in self.hit_markers:
            age = current_time - timestamp
            alpha = 1.0 - (age / self.hit_marker_duration)
            
            # Draw expanding circle
            radius = int(10 + 30 * (1 - alpha))
            color_intensity = int(255 * alpha)
            
            cv2.circle(frame, position, radius, (0, 0, color_intensity), 2)
            cv2.circle(frame, position, 5, (0, 0, 255), -1)
        
        return frame
    
    def draw_fps(
        self,
        frame: np.ndarray,
        fps: float,
        position: Tuple[int, int] = (10, 30)
    ) -> np.ndarray:
        """
        Draw FPS counter.
        
        Args:
            frame: Input frame
            fps: Current FPS
            position: Text position
            
        Returns:
            Frame with overlay
        """
        if not self.show_fps:
            return frame
        
        text = f"FPS: {fps:.1f}"
        
        # Draw background
        (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(frame, (position[0] - 5, position[1] - text_h - 5),
                     (position[0] + text_w + 5, position[1] + 5), (0, 0, 0), -1)
        
        # Draw text
        color = (0, 255, 0) if fps >= 30 else (0, 165, 255) if fps >= 15 else (0, 0, 255)
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        return frame
    
    def draw_info_panel(
        self,
        frame: np.ndarray,
        info: dict,
        position: Tuple[int, int] = (10, 70)
    ) -> np.ndarray:
        """
        Draw information panel.
        
        Args:
            frame: Input frame
            info: Dictionary with information to display
            position: Panel position
            
        Returns:
            Frame with overlay
        """
        if not self.show_info:
            return frame
        
        y_offset = position[1]
        line_height = 25
        
        for key, value in info.items():
            text = f"{key}: {value}"
            
            # Draw background
            (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (position[0] - 5, y_offset - text_h - 5),
                         (position[0] + text_w + 5, y_offset + 5), (0, 0, 0), -1)
            
            # Draw text
            cv2.putText(frame, text, (position[0], y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            y_offset += line_height
        
        return frame
    
    def draw_calibration_grid(
        self,
        frame: np.ndarray,
        camera_points: List[Tuple[int, int]],
        grid_lines: int = 10
    ) -> np.ndarray:
        """
        Draw calibration grid overlay.
        
        Args:
            frame: Input frame
            camera_points: 4 corner points
            grid_lines: Number of grid lines
            
        Returns:
            Frame with overlay
        """
        if len(camera_points) != 4:
            return frame
        
        # Draw boundary
        pts = np.array(camera_points, dtype=np.int32)
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
        
        # Draw grid
        for i in range(1, grid_lines):
            t = i / grid_lines
            
            # Horizontal lines
            start = (
                int(camera_points[0][0] + t * (camera_points[3][0] - camera_points[0][0])),
                int(camera_points[0][1] + t * (camera_points[3][1] - camera_points[0][1]))
            )
            end = (
                int(camera_points[1][0] + t * (camera_points[2][0] - camera_points[1][0])),
                int(camera_points[1][1] + t * (camera_points[2][1] - camera_points[1][1]))
            )
            cv2.line(frame, start, end, (0, 255, 255), 1)
            
            # Vertical lines
            start = (
                int(camera_points[0][0] + t * (camera_points[1][0] - camera_points[0][0])),
                int(camera_points[0][1] + t * (camera_points[1][1] - camera_points[0][1]))
            )
            end = (
                int(camera_points[3][0] + t * (camera_points[2][0] - camera_points[3][0])),
                int(camera_points[3][1] + t * (camera_points[2][1] - camera_points[3][1]))
            )
            cv2.line(frame, start, end, (0, 255, 255), 1)
        
        return frame
    
    def create_visualization(
        self,
        frame: np.ndarray,
        detection: Optional[Tuple] = None,
        trajectory: Optional[List] = None,
        fps: float = 0.0,
        info: Optional[dict] = None,
        current_time: float = 0.0
    ) -> np.ndarray:
        """
        Create complete visualization overlay.
        
        Args:
            frame: Input frame
            detection: Detection tuple (bbox, confidence, label)
            trajectory: Trajectory points
            fps: Current FPS
            info: Information dictionary
            current_time: Current timestamp
            
        Returns:
            Frame with all overlays
        """
        display = frame.copy()
        
        # Draw detection
        if detection and self.show_bounding_box:
            bbox, confidence, label = detection
            display = self.draw_detection(display, bbox, confidence, label)
        
        # Draw trajectory
        if trajectory and self.show_trajectory:
            display = self.draw_trajectory(display, trajectory)
        
        # Draw hit markers
        if current_time > 0:
            display = self.draw_hit_markers(display, current_time)
        
        # Draw FPS
        if self.show_fps:
            display = self.draw_fps(display, fps)
        
        # Draw info panel
        if info and self.show_info:
            display = self.draw_info_panel(display, info)
        
        return display
