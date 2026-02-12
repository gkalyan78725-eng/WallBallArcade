"""
Physics-based hit detection with multiple confirmation methods.
"""

import time
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
from loguru import logger


@dataclass
class HitEvent:
    """Hit detection event."""
    position: Tuple[float, float]  # (x, y) in camera coordinates
    velocity: float  # Speed magnitude
    confidence: float
    timestamp: float
    wall_position: Optional[Tuple[float, float]] = None  # Transformed coordinates


class HitDetector:
    """
    Physics-based hit detection using multiple methods.
    
    Detection Methods:
    1. Velocity reversal - detect when ball velocity reverses (bounces)
    2. Direction change - detect significant angle change in trajectory
    3. Wall boundary proximity - confirm hit is near wall boundaries
    
    Features:
    - Multi-method confirmation for accuracy
    - Debounce logic to prevent duplicate hits
    - Configurable thresholds
    """
    
    def __init__(
        self,
        velocity_threshold: float = -50,
        direction_change_angle: float = 120,
        hit_confirmation_frames: int = 3,
        min_distance_to_wall: float = 20,
        debounce_time: float = 0.3,
        wall_bounds: Optional[Tuple[int, int, int, int]] = None
    ):
        """
        Initialize hit detector.
        
        Args:
            velocity_threshold: Velocity change threshold (negative for reversal)
            direction_change_angle: Minimum angle change in degrees
            hit_confirmation_frames: Frames needed to confirm hit
            min_distance_to_wall: Maximum distance from wall to count as hit
            debounce_time: Minimum time between hits in seconds
            wall_bounds: (x_min, y_min, x_max, y_max) wall boundaries
        """
        self.velocity_threshold = velocity_threshold
        self.direction_change_angle = direction_change_angle
        self.hit_confirmation_frames = hit_confirmation_frames
        self.min_distance_to_wall = min_distance_to_wall
        self.debounce_time = debounce_time
        self.wall_bounds = wall_bounds
        
        # State tracking
        self.previous_velocity: Optional[Tuple[float, float]] = None
        self.confirmation_counter = 0
        self.last_hit_time = 0.0
        self.potential_hit_position: Optional[Tuple[float, float]] = None
        
        logger.info("HitDetector initialized")
    
    def set_wall_bounds(self, bounds: Tuple[int, int, int, int]) -> None:
        """
        Set wall boundary coordinates.
        
        Args:
            bounds: (x_min, y_min, x_max, y_max)
        """
        self.wall_bounds = bounds
        logger.debug(f"Wall bounds set: {bounds}")
    
    def check_hit(
        self,
        position: Tuple[float, float],
        velocity: Tuple[float, float],
        confidence: float = 1.0
    ) -> Optional[HitEvent]:
        """
        Check for hit using multiple methods.
        
        Args:
            position: Current ball position (x, y)
            velocity: Current ball velocity (vx, vy)
            confidence: Tracking confidence
            
        Returns:
            HitEvent if hit detected, None otherwise
        """
        current_time = time.time()
        
        # Check debounce time
        if current_time - self.last_hit_time < self.debounce_time:
            return None
        
        # Method 1: Velocity reversal detection
        velocity_reversal = self._check_velocity_reversal(velocity)
        
        # Method 2: Direction change detection
        direction_change = self._check_direction_change(velocity)
        
        # Method 3: Wall proximity check
        near_wall = self._check_wall_proximity(position)
        
        # Require at least 2 methods to trigger
        detection_count = sum([velocity_reversal, direction_change, near_wall])
        
        if detection_count >= 2:
            self.confirmation_counter += 1
            self.potential_hit_position = position
            
            # Confirm hit after multiple frames
            if self.confirmation_counter >= self.hit_confirmation_frames:
                # Calculate velocity magnitude
                velocity_magnitude = np.sqrt(velocity[0]**2 + velocity[1]**2)
                
                # Create hit event
                hit = HitEvent(
                    position=position,
                    velocity=float(velocity_magnitude),
                    confidence=confidence,
                    timestamp=current_time
                )
                
                # Reset state
                self.confirmation_counter = 0
                self.last_hit_time = current_time
                self.potential_hit_position = None
                
                logger.info(f"Hit detected at {position} with velocity {velocity_magnitude:.1f}")
                return hit
        else:
            # Reset confirmation if detection fails
            self.confirmation_counter = max(0, self.confirmation_counter - 1)
        
        # Update previous velocity
        self.previous_velocity = velocity
        
        return None
    
    def _check_velocity_reversal(self, current_velocity: Tuple[float, float]) -> bool:
        """
        Check if velocity has reversed (bounce).
        
        Args:
            current_velocity: Current velocity (vx, vy)
            
        Returns:
            True if velocity reversed
        """
        if self.previous_velocity is None:
            return False
        
        # Calculate velocity change
        prev_vx, prev_vy = self.previous_velocity
        curr_vx, curr_vy = current_velocity
        
        # Check for velocity reversal in either axis
        delta_vx = curr_vx - prev_vx
        delta_vy = curr_vy - prev_vy
        
        # Significant negative change indicates reversal
        return delta_vx < self.velocity_threshold or delta_vy < self.velocity_threshold
    
    def _check_direction_change(self, current_velocity: Tuple[float, float]) -> bool:
        """
        Check if direction changed significantly.
        
        Args:
            current_velocity: Current velocity (vx, vy)
            
        Returns:
            True if direction changed beyond threshold
        """
        if self.previous_velocity is None:
            return False
        
        # Calculate angles
        prev_angle = np.arctan2(self.previous_velocity[1], self.previous_velocity[0])
        curr_angle = np.arctan2(current_velocity[1], current_velocity[0])
        
        # Calculate angle difference
        angle_diff = abs(curr_angle - prev_angle) * 180 / np.pi
        
        # Normalize to 0-180 range
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        return angle_diff > self.direction_change_angle
    
    def _check_wall_proximity(self, position: Tuple[float, float]) -> bool:
        """
        Check if position is near wall boundaries.
        
        Args:
            position: Current position (x, y)
            
        Returns:
            True if near wall
        """
        if self.wall_bounds is None:
            return True  # Assume near wall if bounds not set
        
        x, y = position
        x_min, y_min, x_max, y_max = self.wall_bounds
        
        # Check distance to each boundary
        dist_to_left = abs(x - x_min)
        dist_to_right = abs(x - x_max)
        dist_to_top = abs(y - y_min)
        dist_to_bottom = abs(y - y_max)
        
        min_dist = min(dist_to_left, dist_to_right, dist_to_top, dist_to_bottom)
        
        return min_dist <= self.min_distance_to_wall
    
    def reset(self) -> None:
        """Reset hit detector state."""
        self.previous_velocity = None
        self.confirmation_counter = 0
        self.potential_hit_position = None
        
        logger.debug("HitDetector reset")
