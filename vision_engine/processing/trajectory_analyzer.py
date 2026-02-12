"""
Trajectory analysis with polynomial fitting and impact prediction.
"""

import numpy as np
from typing import List, Tuple, Optional
from loguru import logger


class TrajectoryAnalyzer:
    """
    Analyze ball trajectory for prediction and smoothing.
    
    Features:
    - Polynomial curve fitting
    - Impact point prediction
    - Speed calculation
    - Trajectory smoothing
    - Parabolic motion modeling
    """
    
    def __init__(
        self,
        min_points: int = 5,
        polynomial_degree: int = 2,
        smoothing_window: int = 3
    ):
        """
        Initialize trajectory analyzer.
        
        Args:
            min_points: Minimum points needed for analysis
            polynomial_degree: Degree of polynomial fit (2 for parabolic)
            smoothing_window: Window size for moving average smoothing
        """
        self.min_points = min_points
        self.polynomial_degree = polynomial_degree
        self.smoothing_window = smoothing_window
        
        logger.info("TrajectoryAnalyzer initialized")
    
    def fit_trajectory(
        self,
        trajectory: List[Tuple[float, float]]
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Fit polynomial curve to trajectory.
        
        Args:
            trajectory: List of (x, y) points
            
        Returns:
            Tuple of (x_coeffs, y_coeffs) or None if insufficient points
        """
        if len(trajectory) < self.min_points:
            return None
        
        try:
            # Extract x and y coordinates
            points = np.array(trajectory)
            
            # Use time index as independent variable
            t = np.arange(len(trajectory))
            
            # Fit polynomials for x(t) and y(t)
            x_coeffs = np.polyfit(t, points[:, 0], self.polynomial_degree)
            y_coeffs = np.polyfit(t, points[:, 1], self.polynomial_degree)
            
            return x_coeffs, y_coeffs
            
        except Exception as e:
            logger.debug(f"Trajectory fitting error: {e}")
            return None
    
    def predict_impact_point(
        self,
        trajectory: List[Tuple[float, float]],
        wall_y: float
    ) -> Optional[Tuple[float, float]]:
        """
        Predict where ball will hit the wall.
        
        Args:
            trajectory: List of (x, y) points
            wall_y: Y-coordinate of wall
            
        Returns:
            Predicted (x, y) impact point or None
        """
        fit_result = self.fit_trajectory(trajectory)
        if fit_result is None:
            return None
        
        x_coeffs, y_coeffs = fit_result
        
        try:
            # Find t where y(t) = wall_y
            # Solve polynomial equation: y_coeffs[0]*t^2 + y_coeffs[1]*t + (y_coeffs[2] - wall_y) = 0
            adjusted_coeffs = y_coeffs.copy()
            adjusted_coeffs[-1] -= wall_y
            
            # Solve for t
            roots = np.roots(adjusted_coeffs)
            
            # Filter for positive real roots (future time)
            real_roots = roots[np.isreal(roots)].real
            positive_roots = real_roots[real_roots > len(trajectory)]
            
            if len(positive_roots) == 0:
                return None
            
            # Use nearest future root
            t_impact = positive_roots[0]
            
            # Calculate x at impact
            x_impact = np.polyval(x_coeffs, t_impact)
            
            return float(x_impact), float(wall_y)
            
        except Exception as e:
            logger.debug(f"Impact prediction error: {e}")
            return None
    
    def calculate_speed(
        self,
        trajectory: List[Tuple[float, float]],
        fps: float = 60
    ) -> Optional[float]:
        """
        Calculate average speed over trajectory.
        
        Args:
            trajectory: List of (x, y) points
            fps: Frames per second for time conversion
            
        Returns:
            Speed in pixels per second or None
        """
        if len(trajectory) < 2:
            return None
        
        try:
            points = np.array(trajectory)
            
            # Calculate distances between consecutive points
            deltas = np.diff(points, axis=0)
            distances = np.sqrt(np.sum(deltas**2, axis=1))
            
            # Average distance per frame
            avg_distance_per_frame = np.mean(distances)
            
            # Convert to pixels per second
            speed = avg_distance_per_frame * fps
            
            return float(speed)
            
        except Exception as e:
            logger.debug(f"Speed calculation error: {e}")
            return None
    
    def smooth_trajectory(
        self,
        trajectory: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        Smooth trajectory using moving average.
        
        Args:
            trajectory: List of (x, y) points
            
        Returns:
            Smoothed trajectory
        """
        if len(trajectory) < self.smoothing_window:
            return trajectory
        
        try:
            points = np.array(trajectory)
            smoothed = []
            
            for i in range(len(points)):
                # Calculate window bounds
                start_idx = max(0, i - self.smoothing_window // 2)
                end_idx = min(len(points), i + self.smoothing_window // 2 + 1)
                
                # Average points in window
                window_points = points[start_idx:end_idx]
                avg_point = np.mean(window_points, axis=0)
                
                smoothed.append((float(avg_point[0]), float(avg_point[1])))
            
            return smoothed
            
        except Exception as e:
            logger.debug(f"Trajectory smoothing error: {e}")
            return trajectory
    
    def calculate_velocity_at_point(
        self,
        trajectory: List[Tuple[float, float]],
        index: int,
        fps: float = 60
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate velocity at a specific point using finite differences.
        
        Args:
            trajectory: List of (x, y) points
            index: Index of point
            fps: Frames per second
            
        Returns:
            (vx, vy) velocity components or None
        """
        if index <= 0 or index >= len(trajectory):
            return None
        
        try:
            # Use central difference if possible
            if index < len(trajectory) - 1:
                # Forward difference
                dx = trajectory[index + 1][0] - trajectory[index][0]
                dy = trajectory[index + 1][1] - trajectory[index][1]
            else:
                # Backward difference
                dx = trajectory[index][0] - trajectory[index - 1][0]
                dy = trajectory[index][1] - trajectory[index - 1][1]
            
            # Convert to velocity (pixels per second)
            vx = dx * fps
            vy = dy * fps
            
            return float(vx), float(vy)
            
        except Exception as e:
            logger.debug(f"Velocity calculation error: {e}")
            return None
    
    def estimate_parabolic_motion(
        self,
        trajectory: List[Tuple[float, float]],
        gravity_pixels_per_sec2: float = 980
    ) -> Optional[dict]:
        """
        Estimate parabolic motion parameters.
        
        Args:
            trajectory: List of (x, y) points
            gravity_pixels_per_sec2: Gravity in pixels/sec^2
            
        Returns:
            Dictionary with motion parameters or None
        """
        if len(trajectory) < self.min_points:
            return None
        
        try:
            points = np.array(trajectory)
            
            # Fit parabola: y = ax^2 + bx + c
            x = points[:, 0]
            y = points[:, 1]
            
            coeffs = np.polyfit(x, y, 2)
            a, b, c = coeffs
            
            # Vertex of parabola (apex of trajectory)
            vertex_x = -b / (2 * a)
            vertex_y = np.polyval(coeffs, vertex_x)
            
            return {
                "coefficients": coeffs.tolist(),
                "vertex": (float(vertex_x), float(vertex_y)),
                "opening": "down" if a < 0 else "up"
            }
            
        except Exception as e:
            logger.debug(f"Parabolic estimation error: {e}")
            return None
