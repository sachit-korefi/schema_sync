import logging
import sys
import os
from functools import wraps


LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Get the log level from the environment variable, default to 'DEBUG'
log_level_name = os.getenv('LOG_LEVEL', 'DEBUG').upper()
log_level = LOG_LEVELS.get(log_level_name, logging.DEBUG)


# Create a logger
logger = logging.getLogger()
logger.setLevel(log_level)
# Disable propagation to prevent duplicate logs
logger.propagate = False

# Prevent duplicate handlers in case of reloads
if not logger.handlers:
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler
    logger.addHandler(handler)


def log_errors(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise
    return sync_wrapper