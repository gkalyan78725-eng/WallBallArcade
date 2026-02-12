"""
Kalman filter-based ball tracker with trajectory prediction.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from loguru import logger

try:
    from filterpy.kalman import KalmanFilter
except ImportError:
    logger.error("filterpy not installed. Install with: pip install filterpy")
    raise


@dataclass
class TrackState:
    """Current tracking state."""
    position: Tuple[float, float]  # (x, y)
    velocity: Tuple[float, float]  # (vx, vy)
    confidence: float
    age: int  # Number of frames tracked
    trajectory: List[Tuple[float, float]] = field(default_factory=list)


class BallTracker:
    """
    Kalman filter tracker for ball tracking with physics-based prediction.
    
    Features:
    - 4-state Kalman filter (x, y, vx, vy)
    - Constant velocity motion model
    - Trajectory history
    - Velocity calculation
    - Future position prediction
    """
    
    def __init__(
        self,
        process_noise: float = 0.01,
        measurement_noise: float = 0.1,
        max_disappear_frames: int = 10,
        min_hit_confidence: float = 0.6,
        trajectory_history_size: int = 30
    ):
        """
        Initialize ball tracker.
        
        Args:
            process_noise: Process noise covariance
            measurement_noise: Measurement noise covariance
            max_disappear_frames: Maximum frames to keep track without detection
            min_hit_confidence: Minimum confidence for hit detection
            trajectory_history_size: Maximum trajectory points to keep
        """
        self.max_disappear_frames = max_disappear_frames
        self.min_hit_confidence = min_hit_confidence
        self.trajectory_history_size = trajectory_history_size
        
        # Initialize Kalman filter
        # State: [x, y, vx, vy]
        # Measurement: [x, y]
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        
        # State transition matrix (constant velocity model)
        dt = 1.0  # Time step (will be updated dynamically)
        self.kf.F = np.array([
            [1, 0, dt, 0],   # x = x + vx*dt
            [0, 1, 0, dt],   # y = y + vy*dt
            [0, 0, 1, 0],    # vx = vx
            [0, 0, 0, 1]     # vy = vy
        ])
        
        # Measurement matrix (we observe position only)
        self.kf.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Process noise covariance
        self.kf.Q *= process_noise
        
        # Measurement noise covariance
        self.kf.R *= measurement_noise
        
        # Initial state covariance
        self.kf.P *= 1000
        
        # Tracking state
        self.is_tracking = False
        self.frames_since_update = 0
        self.track_age = 0
        self.trajectory: List[Tuple[float, float]] = []
        self.last_confidence = 0.0
        
        logger.info("BallTracker initialized")
    
    def initialize(self, position: Tuple[float, float], confidence: float = 1.0) -> None:
        """
        Initialize tracker with first detection.
        
        Args:
            position: Initial (x, y) position
            confidence: Detection confidence
        """
        self.kf.x = np.array([position[0], position[1], 0, 0])
        self.is_tracking = True
        self.frames_since_update = 0
        self.track_age = 0
        self.trajectory = [position]
        self.last_confidence = confidence
        
        logger.debug(f"Tracker initialized at position {position}")
    
    def update(self, position: Tuple[float, float], confidence: float = 1.0) -> None:
        """
        Update tracker with new detection.
        
        Args:
            position: Measured (x, y) position
            confidence: Detection confidence
        """
        if not self.is_tracking:
            self.initialize(position, confidence)
            return
        
        # Predict
        self.kf.predict()
        
        # Update with measurement
        z = np.array([position[0], position[1]])
        self.kf.update(z)
        
        # Update tracking state
        self.frames_since_update = 0
        self.track_age += 1
        self.last_confidence = confidence
        
        # Add to trajectory
        current_pos = (float(self.kf.x[0]), float(self.kf.x[1]))
        self.trajectory.append(current_pos)
        
        # Limit trajectory size
        if len(self.trajectory) > self.trajectory_history_size:
            self.trajectory.pop(0)
    
    def predict(self) -> None:
        """Predict next state without measurement."""
        if not self.is_tracking:
            return
        
        self.kf.predict()
        self.frames_since_update += 1
        self.track_age += 1
        
        # Check if track is lost
        if self.frames_since_update > self.max_disappear_frames:
            self.is_tracking = False
            logger.debug("Track lost")
    
    def get_state(self) -> Optional[TrackState]:
        """
        Get current tracking state.
        
        Returns:
            TrackState or None if not tracking
        """
        if not self.is_tracking:
            return None
        
        position = (float(self.kf.x[0]), float(self.kf.x[1]))
        velocity = (float(self.kf.x[2]), float(self.kf.x[3]))
        
        return TrackState(
            position=position,
            velocity=velocity,
            confidence=self.last_confidence,
            age=self.track_age,
            trajectory=self.trajectory.copy()
        )
    
    def predict_position(self, frames_ahead: int) -> Tuple[float, float]:
        """
        Predict future position.
        
        Args:
            frames_ahead: Number of frames to predict ahead
            
        Returns:
            Predicted (x, y) position
        """
        if not self.is_tracking:
            return (0, 0)
        
        # Use constant velocity model
        dt = frames_ahead
        predicted_x = self.kf.x[0] + self.kf.x[2] * dt
        predicted_y = self.kf.x[1] + self.kf.x[3] * dt
        
        return (float(predicted_x), float(predicted_y))
    
    def get_velocity_magnitude(self) -> float:
        """
        Get velocity magnitude.
        
        Returns:
            Speed in pixels per frame
        """
        if not self.is_tracking:
            return 0.0
        
        vx, vy = self.kf.x[2], self.kf.x[3]
        return float(np.sqrt(vx**2 + vy**2))
    
    def get_velocity_angle(self) -> float:
        """
        Get velocity direction angle.
        
        Returns:
            Angle in degrees (0-360)
        """
        if not self.is_tracking:
            return 0.0
        
        vx, vy = self.kf.x[2], self.kf.x[3]
        angle = np.arctan2(vy, vx) * 180 / np.pi
        return float(angle)
    
    def reset(self) -> None:
        """Reset tracker state."""
        self.is_tracking = False
        self.frames_since_update = 0
        self.track_age = 0
        self.trajectory.clear()
        self.last_confidence = 0.0
        
        logger.debug("Tracker reset")
