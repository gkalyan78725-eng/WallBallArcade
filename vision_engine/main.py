"""
Main entry point for Wall Ball AR Arcade Vision Engine.
"""

import argparse
import sys
import signal
import time
import cv2
from pathlib import Path
from typing import Optional

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))

from core import CameraManager, GPUDetector, BallTracker, PerformanceMonitor
from processing import HitDetector, TrajectoryAnalyzer, HomographyMapper
from calibration import WallCalibrator, ConfigManager
from network import UDPSender, WebSocketSender
from utils import setup_logger, DebugVisualizer
from loguru import logger


class VisionEngine:
    """Main vision engine coordinator."""
    
    def __init__(self, config: dict):
        """
        Initialize vision engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.running = False
        
        # Initialize components
        logger.info("Initializing vision engine components...")
        
        # Core components
        self.camera = CameraManager(
            camera_index=config["camera"]["index"],
            width=config["camera"]["width"],
            height=config["camera"]["height"],
            fps=config["camera"]["fps"],
            buffer_size=config["camera"]["buffer_size"],
            backend=config["camera"]["backend"]
        )
        
        self.detector = GPUDetector(
            model_path=config["detection"]["model"],
            device=config["detection"]["device"],
            confidence_threshold=config["detection"]["confidence_threshold"],
            iou_threshold=config["detection"]["iou_threshold"],
            imgsz=config["detection"]["imgsz"],
            half_precision=config["detection"]["half_precision"],
            max_det=config["detection"]["max_det"]
        )
        
        self.tracker = BallTracker(
            process_noise=config["tracking"]["kalman_process_noise"],
            measurement_noise=config["tracking"]["kalman_measurement_noise"],
            max_disappear_frames=config["tracking"]["max_disappear_frames"],
            min_hit_confidence=config["tracking"]["min_hit_confidence"]
        )
        
        self.performance = PerformanceMonitor(
            target_fps=config["performance"]["target_fps"]
        )
        
        # Processing components
        self.hit_detector = HitDetector(
            velocity_threshold=config["hit_detection"]["velocity_threshold"],
            direction_change_angle=config["hit_detection"]["direction_change_angle"],
            hit_confirmation_frames=config["hit_detection"]["hit_confirmation_frames"],
            min_distance_to_wall=config["hit_detection"]["min_distance_to_wall"],
            debounce_time=config["hit_detection"]["debounce_time"]
        )
        
        self.trajectory_analyzer = TrajectoryAnalyzer()
        self.homography_mapper = HomographyMapper()
        
        # Network
        protocol = config["network"]["protocol"]
        if protocol == "udp":
            self.sender = UDPSender(
                host=config["network"]["udp_host"],
                port=config["network"]["udp_port"]
            )
        else:
            logger.warning("WebSocket not implemented in sync mode, falling back to UDP")
            self.sender = UDPSender(
                host=config["network"]["udp_host"],
                port=config["network"]["udp_port"]
            )
        
        # Debug visualization
        if config["debug"]["show_visualization"]:
            self.visualizer = DebugVisualizer(
                show_bounding_box=config["debug"]["show_bounding_box"],
                show_trajectory=config["debug"]["show_trajectory"],
                show_fps=config["debug"]["show_fps"]
            )
        else:
            self.visualizer = None
        
        logger.info("Vision engine initialized")
    
    def run(self) -> None:
        """Run main processing loop."""
        logger.info("Starting vision engine...")
        
        # Start camera
        if not self.camera.start():
            logger.error("Failed to start camera")
            return
        
        # Warmup detector
        self.detector.warmup(
            warmup_frames=self.config["performance"]["warmup_frames"],
            frame_shape=(
                self.config["camera"]["height"],
                self.config["camera"]["width"],
                3
            )
        )
        
        # Load calibration if exists
        config_manager = ConfigManager()
        calibration = config_manager.load_calibration()
        if calibration:
            self.homography_mapper.load_calibration(calibration)
            logger.info("Calibration loaded")
        else:
            logger.warning("No calibration found, coordinates will not be transformed")
        
        self.running = True
        
        try:
            while self.running:
                self.performance.start_frame()
                
                # Capture frame
                ret, frame = self.camera.get_frame()
                if not ret or frame is None:
                    continue
                
                # Detect ball
                detections = self.detector.detect(frame)
                
                # Filter for sports ball (class_id 32 in COCO)
                ball_detections = self.detector.filter_by_class(detections, 32)
                
                # Update tracker
                if ball_detections:
                    # Use highest confidence detection
                    best_detection = max(ball_detections, key=lambda d: d.confidence)
                    self.tracker.update(best_detection.center, best_detection.confidence)
                else:
                    self.tracker.predict()
                
                # Check for hit
                track_state = self.tracker.get_state()
                if track_state and track_state.confidence > self.config["tracking"]["min_hit_confidence"]:
                    hit_event = self.hit_detector.check_hit(
                        position=track_state.position,
                        velocity=track_state.velocity,
                        confidence=track_state.confidence
                    )
                    
                    if hit_event:
                        # Transform coordinates if calibrated
                        if self.homography_mapper.is_calibrated():
                            wall_pos = self.homography_mapper.camera_to_wall(hit_event.position)
                            if wall_pos:
                                hit_event.wall_position = wall_pos
                                
                                # Send hit event
                                self.sender.send_hit(
                                    x=wall_pos[0],
                                    y=wall_pos[1],
                                    velocity=hit_event.velocity,
                                    timestamp=hit_event.timestamp
                                )
                        
                        # Add hit marker for visualization
                        if self.visualizer:
                            self.visualizer.add_hit_marker(
                                hit_event.position,
                                hit_event.timestamp
                            )
                
                # Visualization
                if self.visualizer and self.config["debug"]["show_visualization"]:
                    # Prepare detection info
                    detection_info = None
                    if ball_detections:
                        best = ball_detections[0]
                        detection_info = (best.bbox, best.confidence, "Ball")
                    
                    # Prepare info panel
                    info = {
                        "Detections": len(ball_detections),
                        "Tracking": "Yes" if track_state else "No",
                        "Velocity": f"{self.tracker.get_velocity_magnitude():.1f}" if track_state else "0"
                    }
                    
                    # Create visualization
                    display_frame = self.visualizer.create_visualization(
                        frame=frame,
                        detection=detection_info,
                        trajectory=track_state.trajectory if track_state else None,
                        fps=self.performance.get_fps(),
                        info=info,
                        current_time=time.time()
                    )
                    
                    cv2.imshow("Vision Engine", display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                self.performance.end_frame()
                
                # Log statistics periodically
                if self.performance.total_frames % 300 == 0:
                    self.performance.log_stats()
                    logger.info(f"Network stats: {self.sender.get_statistics()}")
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop vision engine."""
        logger.info("Stopping vision engine...")
        self.running = False
        
        self.camera.stop()
        self.sender.close()
        
        if self.visualizer:
            cv2.destroyAllWindows()
        
        # Print final statistics
        logger.info(f"Camera stats: {self.camera.get_statistics()}")
        logger.info(f"Detector stats: {self.detector.get_performance_stats()}")
        logger.info(f"Performance stats: {self.performance.get_overall_stats()}")
        
        logger.info("Vision engine stopped")


def run_mode(args) -> None:
    """Run vision engine in normal mode."""
    # Setup logging
    setup_logger(level=args.log_level)
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.load_settings(args.config)
    
    if config is None:
        logger.error("Failed to load configuration")
        return
    
    # Create and run engine
    engine = VisionEngine(config)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received termination signal")
        engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    engine.run()


def calibrate_mode(args) -> None:
    """Run calibration mode."""
    setup_logger(level=args.log_level)
    
    logger.info("Starting calibration mode...")
    
    # Initialize camera
    camera = CameraManager(
        camera_index=args.camera,
        width=args.width,
        height=args.height
    )
    
    if not camera.start():
        logger.error("Failed to start camera")
        return
    
    # Capture frame for calibration
    time.sleep(1)  # Let camera stabilize
    ret, frame = camera.get_frame(timeout=2.0)
    
    if not ret or frame is None:
        logger.error("Failed to capture frame")
        camera.stop()
        return
    
    # Run calibration
    calibrator = WallCalibrator(
        wall_width=args.wall_width,
        wall_height=args.wall_height
    )
    
    result = calibrator.calibrate(frame)
    
    if result:
        camera_points, wall_points = result
        
        # Compute homography
        mapper = HomographyMapper()
        if mapper.calibrate(camera_points, wall_points):
            # Save calibration
            config_manager = ConfigManager()
            calibration_data = mapper.get_calibration_data()
            
            if config_manager.save_calibration(calibration_data):
                logger.info("Calibration saved successfully!")
                
                # Test mode
                if args.test:
                    logger.info("Entering test mode...")
                    ret, frame = camera.get_frame(timeout=2.0)
                    if ret and frame is not None:
                        calibrator.test_calibration(frame, mapper)
            else:
                logger.error("Failed to save calibration")
        else:
            logger.error("Failed to compute homography")
    else:
        logger.info("Calibration cancelled")
    
    camera.stop()


def test_mode(args) -> None:
    """Run test mode."""
    setup_logger(level=args.log_level)
    
    logger.info("Starting test mode...")
    logger.info("This mode runs the vision engine with debug visualization")
    
    # Modify config to enable debug
    config_manager = ConfigManager()
    config = config_manager.load_settings(args.config)
    
    if config is None:
        config = config_manager.get_default_settings()
    
    config["debug"]["show_visualization"] = True
    config["debug"]["show_fps"] = True
    config["debug"]["show_trajectory"] = True
    config["debug"]["show_bounding_box"] = True
    
    # Run engine
    engine = VisionEngine(config)
    engine.run()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wall Ball AR Arcade Vision Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Operation mode")
    
    # Run mode
    run_parser = subparsers.add_parser("run", help="Run vision engine")
    run_parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Configuration file path"
    )
    
    # Calibrate mode
    calibrate_parser = subparsers.add_parser("calibrate", help="Calibration mode")
    calibrate_parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index"
    )
    calibrate_parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Camera width"
    )
    calibrate_parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Camera height"
    )
    calibrate_parser.add_argument(
        "--wall-width",
        type=int,
        default=1920,
        help="Wall/projector width"
    )
    calibrate_parser.add_argument(
        "--wall-height",
        type=int,
        default=1080,
        help="Wall/projector height"
    )
    calibrate_parser.add_argument(
        "--test",
        action="store_true",
        help="Enter test mode after calibration"
    )
    
    # Test mode
    test_parser = subparsers.add_parser("test", help="Test mode with debug visualization")
    test_parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    if args.mode == "run":
        run_mode(args)
    elif args.mode == "calibrate":
        calibrate_mode(args)
    elif args.mode == "test":
        test_mode(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
