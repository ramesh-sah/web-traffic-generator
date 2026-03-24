import logging
import sys
import os
from bot.config import OUTPUT_FOLDER

def setup_logger():
    # Create logger
    logger = logging.getLogger("SEO_BOOSTER")
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers if setup_logger is called multiple times
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler
        log_file = os.path.join(OUTPUT_FOLDER, "app.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()
