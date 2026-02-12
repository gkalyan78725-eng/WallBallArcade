"""
Interactive wall calibration with mouse-based point selection.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Callable
from loguru import logger


class WallCalibrator:
    """
    Interactive calibration interface for wall mapping.
    
    Features:
    - Mouse-based 4-point selection
    - Visual feedback with points and lines
    - Point order: top-left, top-right, bottom-right, bottom-left
    - Homography computation
    - Test mode for coordinate validation
    """
    
    def __init__(
        self,
        wall_width: int = 1920,
        wall_height: int = 1080
    ):
        """
        Initialize wall calibrator.
        
        Args:
            wall_width: Projector/wall width in pixels
            wall_height: Projector/wall height in pixels
        """
        self.wall_width = wall_width
        self.wall_height = wall_height
        
        # Calibration points
        self.camera_points: List[Tuple[int, int]] = []
        self.wall_points = [
            (0, 0),                                    # Top-left
            (wall_width - 1, 0),                      # Top-right
            (wall_width - 1, wall_height - 1),        # Bottom-right
            (0, wall_height - 1)                      # Bottom-left
        ]
        
        # Display
        self.window_name = "Wall Calibration"
        self.frame: Optional[np.ndarray] = None
        self.display_frame: Optional[np.ndarray] = None
        
        # Callbacks
        self.on_calibration_complete: Optional[Callable] = None
        
        logger.info(f"WallCalibrator initialized ({wall_width}x{wall_height})")
    
    def calibrate(self, frame: np.ndarray) -> Optional[Tuple[List, List]]:
        """
        Start interactive calibration session.
        
        Args:
            frame: Camera frame to display
            
        Returns:
            Tuple of (camera_points, wall_points) if successful, None otherwise
        """
        self.frame = frame.copy()
        self.display_frame = frame.copy()
        self.camera_points.clear()
        
        # Create window and set mouse callback
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
        
        logger.info("Click 4 corners in order: top-left, top-right, bottom-right, bottom-left")
        logger.info("Press 'r' to reset, 'q' to cancel, points auto-accept when 4 selected")
        
        while True:
            # Update display
            self._draw_ui()
            cv2.imshow(self.window_name, self.display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                # Cancel calibration
                logger.info("Calibration cancelled")
                cv2.destroyWindow(self.window_name)
                return None
            
            elif key == ord('r'):
                # Reset points
                self.camera_points.clear()
                self.display_frame = self.frame.copy()
                logger.info("Points reset")
            
            # Auto-complete when 4 points selected
            if len(self.camera_points) == 4:
                logger.info("4 points selected, calibration complete")
                cv2.destroyWindow(self.window_name)
                return self.camera_points.copy(), self.wall_points.copy()
        
        return None
    
    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param) -> None:
        """
        Handle mouse events for point selection.
        
        Args:
            event: Mouse event type
            x, y: Mouse coordinates
            flags: Additional flags
            param: User data
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.camera_points) < 4:
                self.camera_points.append((x, y))
                logger.info(f"Point {len(self.camera_points)}: ({x}, {y})")
                
                # Update display
                self.display_frame = self.frame.copy()
    
    def _draw_ui(self) -> None:
        """Draw calibration UI on display frame."""
        if self.display_frame is None:
            return
        
        # Draw selected points
        colors = [
            (0, 0, 255),    # Red - top-left
            (0, 255, 0),    # Green - top-right
            (255, 0, 0),    # Blue - bottom-right
            (255, 255, 0)   # Cyan - bottom-left
        ]
        
        labels = ["TL", "TR", "BR", "BL"]
        
        for i, point in enumerate(self.camera_points):
            # Draw point
            cv2.circle(self.display_frame, point, 10, colors[i], -1)
            cv2.circle(self.display_frame, point, 12, (255, 255, 255), 2)
            
            # Draw label
            cv2.putText(
                self.display_frame,
                labels[i],
                (point[0] + 15, point[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                colors[i],
                2
            )
        
        # Draw lines between points
        if len(self.camera_points) >= 2:
            for i in range(len(self.camera_points) - 1):
                cv2.line(
                    self.display_frame,
                    self.camera_points[i],
                    self.camera_points[i + 1],
                    (0, 255, 255),
                    2
                )
        
        # Close the quadrilateral
        if len(self.camera_points) == 4:
            cv2.line(
                self.display_frame,
                self.camera_points[3],
                self.camera_points[0],
                (0, 255, 255),
                2
            )
        
        # Draw instructions
        instructions = [
            f"Select {4 - len(self.camera_points)} more corner(s)",
            "Order: TL → TR → BR → BL",
            "Press 'r' to reset, 'q' to cancel"
        ]
        
        y_offset = 30
        for instruction in instructions:
            cv2.putText(
                self.display_frame,
                instruction,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            y_offset += 30
    
    def test_calibration(
        self,
        frame: np.ndarray,
        homography_mapper
    ) -> None:
        """
        Test mode to validate calibration.
        
        Args:
            frame: Camera frame
            homography_mapper: HomographyMapper instance
        """
        test_frame = frame.copy()
        window_name = "Calibration Test"
        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        def test_mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Transform point
                wall_point = homography_mapper.camera_to_wall((x, y))
                
                if wall_point:
                    display = test_frame.copy()
                    
                    # Draw click point
                    cv2.circle(display, (x, y), 5, (0, 255, 0), -1)
                    
                    # Display coordinates
                    text = f"Camera: ({x}, {y}) → Wall: ({wall_point[0]:.0f}, {wall_point[1]:.0f})"
                    cv2.putText(
                        display,
                        text,
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2
                    )
                    
                    cv2.imshow(window_name, display)
                    logger.info(text)
        
        cv2.setMouseCallback(window_name, test_mouse_callback)
        
        logger.info("Click on frame to test coordinate transformation")
        logger.info("Press any key to exit test mode")
        
        cv2.imshow(window_name, test_frame)
        cv2.waitKey(0)
        cv2.destroyWindow(window_name)
    
    def visualize_calibration_grid(
        self,
        frame: np.ndarray,
        camera_points: List[Tuple[int, int]]
    ) -> np.ndarray:
        """
        Draw calibration grid overlay.
        
        Args:
            frame: Input frame
            camera_points: 4 calibration points
            
        Returns:
            Frame with grid overlay
        """
        display = frame.copy()
        
        if len(camera_points) != 4:
            return display
        
        # Draw calibrated region
        pts = np.array(camera_points, dtype=np.int32)
        cv2.polylines(display, [pts], True, (0, 255, 0), 2)
        
        # Draw grid lines
        grid_lines = 10
        
        # Horizontal lines
        for i in range(1, grid_lines):
            t = i / grid_lines
            start = (
                int(camera_points[0][0] + t * (camera_points[3][0] - camera_points[0][0])),
                int(camera_points[0][1] + t * (camera_points[3][1] - camera_points[0][1]))
            )
            end = (
                int(camera_points[1][0] + t * (camera_points[2][0] - camera_points[1][0])),
                int(camera_points[1][1] + t * (camera_points[2][1] - camera_points[1][1]))
            )
            cv2.line(display, start, end, (0, 255, 255), 1)
        
        # Vertical lines
        for i in range(1, grid_lines):
            t = i / grid_lines
            start = (
                int(camera_points[0][0] + t * (camera_points[1][0] - camera_points[0][0])),
                int(camera_points[0][1] + t * (camera_points[1][1] - camera_points[0][1]))
            )
            end = (
                int(camera_points[3][0] + t * (camera_points[2][0] - camera_points[3][0])),
                int(camera_points[3][1] + t * (camera_points[2][1] - camera_points[3][1]))
            )
            cv2.line(display, start, end, (0, 255, 255), 1)
        
        return display
