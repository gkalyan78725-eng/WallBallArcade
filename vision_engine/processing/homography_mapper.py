"""
Homography-based coordinate transformation for camera-to-projector mapping.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from loguru import logger


class HomographyMapper:
    """
    Camera-to-projector coordinate transformation using homography.
    
    Features:
    - 4-point homography calibration
    - RANSAC for robust fitting
    - Bidirectional transformation (camera ↔ projector)
    - Batch transformation
    - Reprojection error calculation
    """
    
    def __init__(self):
        """Initialize homography mapper."""
        self.homography_matrix: Optional[np.ndarray] = None
        self.inverse_matrix: Optional[np.ndarray] = None
        self.camera_points: Optional[np.ndarray] = None
        self.wall_points: Optional[np.ndarray] = None
        self.reprojection_error: Optional[float] = None
        
        logger.info("HomographyMapper initialized")
    
    def calibrate(
        self,
        camera_points: List[Tuple[float, float]],
        wall_points: List[Tuple[float, float]]
    ) -> bool:
        """
        Calibrate homography from corresponding points.
        
        Args:
            camera_points: 4 points in camera coordinates [(x, y), ...]
            wall_points: 4 corresponding points in wall coordinates [(x, y), ...]
            
        Returns:
            True if calibration successful
        """
        if len(camera_points) != 4 or len(wall_points) != 4:
            logger.error("Need exactly 4 point pairs for calibration")
            return False
        
        try:
            # Convert to numpy arrays
            self.camera_points = np.array(camera_points, dtype=np.float32)
            self.wall_points = np.array(wall_points, dtype=np.float32)
            
            # Compute homography using RANSAC for robustness
            self.homography_matrix, mask = cv2.findHomography(
                self.camera_points,
                self.wall_points,
                cv2.RANSAC,
                5.0  # RANSAC reprojection threshold
            )
            
            if self.homography_matrix is None:
                logger.error("Failed to compute homography")
                return False
            
            # Compute inverse for bidirectional transformation
            self.inverse_matrix = np.linalg.inv(self.homography_matrix)
            
            # Calculate reprojection error
            self.reprojection_error = self._calculate_reprojection_error()
            
            logger.info(f"Homography calibrated (error: {self.reprojection_error:.2f} pixels)")
            return True
            
        except Exception as e:
            logger.error(f"Calibration error: {e}")
            return False
    
    def camera_to_wall(self, point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Transform point from camera to wall coordinates.
        
        Args:
            point: (x, y) in camera coordinates
            
        Returns:
            (x, y) in wall coordinates or None if not calibrated
        """
        if self.homography_matrix is None:
            logger.warning("Not calibrated")
            return None
        
        try:
            # Convert to homogeneous coordinates
            src_point = np.array([[point[0], point[1]]], dtype=np.float32)
            
            # Apply homography
            dst_point = cv2.perspectiveTransform(
                src_point.reshape(1, 1, 2),
                self.homography_matrix
            )
            
            result = dst_point[0, 0]
            return float(result[0]), float(result[1])
            
        except Exception as e:
            logger.debug(f"Transformation error: {e}")
            return None
    
    def wall_to_camera(self, point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Transform point from wall to camera coordinates.
        
        Args:
            point: (x, y) in wall coordinates
            
        Returns:
            (x, y) in camera coordinates or None if not calibrated
        """
        if self.inverse_matrix is None:
            logger.warning("Not calibrated")
            return None
        
        try:
            # Convert to homogeneous coordinates
            src_point = np.array([[point[0], point[1]]], dtype=np.float32)
            
            # Apply inverse homography
            dst_point = cv2.perspectiveTransform(
                src_point.reshape(1, 1, 2),
                self.inverse_matrix
            )
            
            result = dst_point[0, 0]
            return float(result[0]), float(result[1])
            
        except Exception as e:
            logger.debug(f"Inverse transformation error: {e}")
            return None
    
    def batch_transform(
        self,
        points: List[Tuple[float, float]],
        camera_to_wall: bool = True
    ) -> List[Optional[Tuple[float, float]]]:
        """
        Transform multiple points at once.
        
        Args:
            points: List of (x, y) points
            camera_to_wall: If True, transform camera→wall, else wall→camera
            
        Returns:
            List of transformed points
        """
        matrix = self.homography_matrix if camera_to_wall else self.inverse_matrix
        
        if matrix is None:
            return [None] * len(points)
        
        try:
            # Convert to numpy array
            src_points = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
            
            # Apply transformation
            dst_points = cv2.perspectiveTransform(src_points, matrix)
            
            # Convert back to list of tuples
            results = []
            for point in dst_points:
                results.append((float(point[0, 0]), float(point[0, 1])))
            
            return results
            
        except Exception as e:
            logger.debug(f"Batch transformation error: {e}")
            return [None] * len(points)
    
    def _calculate_reprojection_error(self) -> float:
        """
        Calculate mean reprojection error for calibration points.
        
        Returns:
            Mean error in pixels
        """
        if self.homography_matrix is None or self.camera_points is None:
            return float('inf')
        
        try:
            # Transform camera points to wall space
            transformed = cv2.perspectiveTransform(
                self.camera_points.reshape(-1, 1, 2),
                self.homography_matrix
            )
            
            # Calculate distances to actual wall points
            errors = []
            for i in range(len(self.wall_points)):
                dx = transformed[i, 0, 0] - self.wall_points[i, 0]
                dy = transformed[i, 0, 1] - self.wall_points[i, 1]
                error = np.sqrt(dx**2 + dy**2)
                errors.append(error)
            
            return float(np.mean(errors))
            
        except Exception as e:
            logger.debug(f"Error calculation failed: {e}")
            return float('inf')
    
    def is_calibrated(self) -> bool:
        """
        Check if mapper is calibrated.
        
        Returns:
            True if calibrated
        """
        return self.homography_matrix is not None
    
    def get_calibration_data(self) -> Optional[dict]:
        """
        Get calibration data for saving.
        
        Returns:
            Dictionary with calibration data or None
        """
        if not self.is_calibrated():
            return None
        
        return {
            "homography_matrix": self.homography_matrix.tolist(),
            "camera_points": self.camera_points.tolist(),
            "wall_points": self.wall_points.tolist(),
            "reprojection_error": float(self.reprojection_error) if self.reprojection_error else None
        }
    
    def load_calibration(self, calibration_data: dict) -> bool:
        """
        Load calibration from saved data.
        
        Args:
            calibration_data: Dictionary with calibration data
            
        Returns:
            True if loaded successfully
        """
        try:
            self.homography_matrix = np.array(calibration_data["homography_matrix"], dtype=np.float32)
            self.camera_points = np.array(calibration_data["camera_points"], dtype=np.float32)
            self.wall_points = np.array(calibration_data["wall_points"], dtype=np.float32)
            self.reprojection_error = calibration_data.get("reprojection_error")
            
            # Compute inverse
            self.inverse_matrix = np.linalg.inv(self.homography_matrix)
            
            logger.info("Calibration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False
