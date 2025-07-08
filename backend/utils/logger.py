import logging
import sys
import os
from datetime import datetime

def setup_logging():
    """Setup logging configuration for the backend"""
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                os.path.join(logs_dir, f"backend-{timestamp}.log"),
                encoding="utf-8"
            )
        ]
    )
    
    # Set specific log levels for different modules
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging setup completed")
    
    return logger 