"""
Configuration management with JSON save/load and validation.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger
import yaml


class ConfigManager:
    """
    Configuration file management.
    
    Features:
    - JSON and YAML support
    - Configuration validation
    - Default settings
    - Save/load calibration data
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.calibration_file = self.config_dir / "calibration.json"
        self.settings_file = self.config_dir / "settings.yaml"
        
        logger.info(f"ConfigManager initialized (dir: {config_dir})")
    
    def save_calibration(self, calibration_data: dict) -> bool:
        """
        Save calibration data to JSON file.
        
        Args:
            calibration_data: Dictionary with calibration data
            
        Returns:
            True if saved successfully
        """
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            
            logger.info(f"Calibration saved to {self.calibration_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
    
    def load_calibration(self) -> Optional[dict]:
        """
        Load calibration data from JSON file.
        
        Returns:
            Calibration data dictionary or None if not found
        """
        if not self.calibration_file.exists():
            logger.warning(f"Calibration file not found: {self.calibration_file}")
            return None
        
        try:
            with open(self.calibration_file, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Calibration loaded from {self.calibration_file}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return None
    
    def calibration_exists(self) -> bool:
        """
        Check if calibration file exists.
        
        Returns:
            True if calibration file exists
        """
        return self.calibration_file.exists()
    
    def load_settings(self, settings_file: Optional[str] = None) -> Optional[dict]:
        """
        Load settings from YAML file.
        
        Args:
            settings_file: Path to settings file (optional)
            
        Returns:
            Settings dictionary or None
        """
        file_path = Path(settings_file) if settings_file else self.settings_file
        
        if not file_path.exists():
            logger.warning(f"Settings file not found: {file_path}")
            return self.get_default_settings()
        
        try:
            with open(file_path, 'r') as f:
                settings = yaml.safe_load(f)
            
            logger.info(f"Settings loaded from {file_path}")
            return settings
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self.get_default_settings()
    
    def save_settings(self, settings: dict, settings_file: Optional[str] = None) -> bool:
        """
        Save settings to YAML file.
        
        Args:
            settings: Settings dictionary
            settings_file: Path to settings file (optional)
            
        Returns:
            True if saved successfully
        """
        file_path = Path(settings_file) if settings_file else self.settings_file
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(settings, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Settings saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_default_settings(self) -> dict:
        """
        Get default settings.
        
        Returns:
            Default settings dictionary
        """
        return {
            "camera": {
                "index": 0,
                "width": 1280,
                "height": 720,
                "fps": 60,
                "buffer_size": 1,
                "backend": "DSHOW"
            },
            "detection": {
                "model": "yolov8n.pt",
                "confidence_threshold": 0.45,
                "iou_threshold": 0.4,
                "imgsz": 640,
                "device": "cuda",
                "half_precision": True,
                "max_det": 5
            },
            "tracking": {
                "kalman_process_noise": 0.01,
                "kalman_measurement_noise": 0.1,
                "max_disappear_frames": 10,
                "min_hit_confidence": 0.6
            },
            "hit_detection": {
                "velocity_threshold": -50,
                "direction_change_angle": 120,
                "hit_confirmation_frames": 3,
                "min_distance_to_wall": 20,
                "debounce_time": 0.3
            },
            "performance": {
                "target_fps": 60,
                "frame_skip_threshold": 0.8,
                "warmup_frames": 30
            },
            "network": {
                "protocol": "udp",
                "udp_host": "127.0.0.1",
                "udp_port": 9000,
                "websocket_uri": "ws://localhost:9001"
            },
            "debug": {
                "show_visualization": True,
                "show_fps": True,
                "show_trajectory": True,
                "show_bounding_box": True,
                "save_debug_video": False
            }
        }
    
    def validate_settings(self, settings: dict) -> bool:
        """
        Validate settings structure and values.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            True if valid
        """
        required_sections = [
            "camera", "detection", "tracking", 
            "hit_detection", "performance", "network", "debug"
        ]
        
        for section in required_sections:
            if section not in settings:
                logger.error(f"Missing required section: {section}")
                return False
        
        # Validate camera settings
        camera = settings["camera"]
        if camera["width"] <= 0 or camera["height"] <= 0:
            logger.error("Invalid camera resolution")
            return False
        
        if camera["fps"] <= 0:
            logger.error("Invalid FPS")
            return False
        
        # Validate detection settings
        detection = settings["detection"]
        if not 0 <= detection["confidence_threshold"] <= 1:
            logger.error("Invalid confidence threshold")
            return False
        
        if not 0 <= detection["iou_threshold"] <= 1:
            logger.error("Invalid IOU threshold")
            return False
        
        logger.info("Settings validation passed")
        return True
    
    def merge_settings(self, base: dict, override: dict) -> dict:
        """
        Merge override settings into base settings.
        
        Args:
            base: Base settings dictionary
            override: Override settings dictionary
            
        Returns:
            Merged settings dictionary
        """
        merged = base.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = self.merge_settings(merged[key], value)
            else:
                merged[key] = value
        
        return merged
