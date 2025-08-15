'''
import logging

logger = logging
logger.basicConfig(filename='.\chabot.log', encoding='utf-8',format='%(asctime)s - %(message)s', level=logging.INFO)
logger.info("This is input text: ""%s", "Chatbot application started")
if __name__ == '__main__':
    logging.info('Starting unload.')

'''
import logging
import os
from logging.handlers import RotatingFileHandler

class BaseLogger:
    def __init__(self, log_name: str = 'app', log_level=logging.INFO, log_dir: str = 'logs', max_bytes=5_000_000, backup_count=5):
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Construct full path to log file
        log_file = os.path.join(log_dir, f"{log_name}.log")

        # Create logger
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False  # Avoid duplicate logs if root logger is also configured

        # Avoid adding multiple handlers if already added
        if not self.logger.handlers:
            # File handler with rotation
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s]- %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger
