import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import logger

logger.info("Logger test: This should show in both file and terminal.")
