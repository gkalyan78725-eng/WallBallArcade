"""
YOLOv8 GPU-accelerated object detector with FP16 support.
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from loguru import logger

try:
    from ultralytics import YOLO
    import torch
except ImportError:
    logger.error("ultralytics or torch not installed. Install with: pip install ultralytics torch")
    raise


@dataclass
class Detection:
    """Object detection result."""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    center: Tuple[float, float]  # cx, cy


class GPUDetector:
    """
    YOLOv8 object detector with GPU acceleration.
    
    Features:
    - CUDA device selection with CPU fallback
    - FP16 half-precision for 2x speedup
    - Model warmup with dummy frames
    - Performance tracking
    - Configurable confidence and IOU thresholds
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        device: str = "cuda",
        confidence_threshold: float = 0.45,
        iou_threshold: float = 0.4,
        imgsz: int = 640,
        half_precision: bool = True,
        max_det: int = 5
    ):
        """
        Initialize GPU detector.
        
        Args:
            model_path: Path to YOLO model file
            device: Device to use ('cuda' or 'cpu')
            confidence_threshold: Minimum confidence for detection
            iou_threshold: IOU threshold for NMS
            imgsz: Input image size
            half_precision: Use FP16 for faster inference
            max_det: Maximum detections per image
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.half_precision = half_precision
        self.max_det = max_det
        
        # Check CUDA availability
        self.device = device
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA not available, falling back to CPU")
            self.device = "cpu"
            self.half_precision = False  # FP16 only works on GPU
        
        logger.info(f"Initializing YOLO detector on {self.device}")
        
        # Load model
        try:
            self.model = YOLO(model_path)
            self.model.to(self.device)
            
            if self.half_precision and self.device == "cuda":
                self.model.model.half()
                logger.info("FP16 half-precision enabled")
            
            logger.info(f"YOLO model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
        
        # Performance tracking
        self.inference_times: List[float] = []
        self.total_detections = 0
    
    def warmup(self, warmup_frames: int = 30, frame_shape: Tuple[int, int, int] = (720, 1280, 3)) -> None:
        """
        Warmup the model with dummy frames.
        
        Args:
            warmup_frames: Number of warmup iterations
            frame_shape: Shape of dummy frames (height, width, channels)
        """
        logger.info(f"Warming up model with {warmup_frames} frames...")
        
        dummy_frame = np.zeros(frame_shape, dtype=np.uint8)
        
        for i in range(warmup_frames):
            _ = self.detect(dummy_frame)
        
        # Reset statistics after warmup
        self.inference_times.clear()
        self.total_detections = 0
        
        logger.info("Warmup complete")
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect objects in frame.
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of Detection objects
        """
        start_time = time.time()
        
        try:
            # Run inference
            results = self.model.predict(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                imgsz=self.imgsz,
                device=self.device,
                half=self.half_precision,
                max_det=self.max_det,
                verbose=False
            )
            
            # Parse results
            detections = []
            if results and len(results) > 0:
                boxes = results[0].boxes
                
                for box in boxes:
                    # Extract box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Calculate center
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    
                    detection = Detection(
                        bbox=(float(x1), float(y1), float(x2), float(y2)),
                        confidence=confidence,
                        class_id=class_id,
                        center=(float(cx), float(cy))
                    )
                    detections.append(detection)
            
            # Track performance
            inference_time = time.time() - start_time
            self.inference_times.append(inference_time)
            self.total_detections += len(detections)
            
            # Keep only last 100 measurements
            if len(self.inference_times) > 100:
                self.inference_times.pop(0)
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.inference_times:
            return {
                "avg_inference_time": 0,
                "avg_fps": 0,
                "total_detections": 0
            }
        
        avg_time = np.mean(self.inference_times)
        avg_fps = 1.0 / avg_time if avg_time > 0 else 0
        
        return {
            "avg_inference_time": avg_time,
            "avg_fps": avg_fps,
            "total_detections": self.total_detections,
            "device": self.device,
            "half_precision": self.half_precision
        }
    
    def filter_by_class(self, detections: List[Detection], class_id: int) -> List[Detection]:
        """
        Filter detections by class ID.
        
        Args:
            detections: List of detections
            class_id: Class ID to filter (e.g., 32 for sports ball in COCO)
            
        Returns:
            Filtered list of detections
        """
        return [d for d in detections if d.class_id == class_id]
