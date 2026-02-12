"""
Logging setup using loguru.
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: str = "vision_engine.log",
    rotation: str = "10 MB",
    retention: str = "1 week",
    colorize: bool = True
) -> None:
    """
    Setup structured logging with loguru.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        rotation: Log rotation size/time
        retention: Log retention period
        colorize: Enable colored console output
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=level,
        colorize=colorize
    )
    
    # Add file handler
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation=rotation,
        retention=retention,
        compression="zip"
    )
    
    logger.info(f"Logger initialized (level: {level})")
