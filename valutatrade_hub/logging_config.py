import logging
from logging.handlers import RotatingFileHandler
from valutatrade_hub.core import constants


def setup_logging():
    logger = logging.getLogger("valutatrade")
    if logger.handlers:
        return logger  

    logger.setLevel(logging.INFO)

    log_file = constants.ACTIONS_LOG_PATH
    log_format = constants.LOGS_RAW_FORMAT  

    python_format = (
        log_format
            .replace("{time}", "%(asctime)s")
            .replace("{level}", "%(levelname)s")
            .replace("{message}", "%(message)s")
    )

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8"
    )

    formatter = logging.Formatter(python_format, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = setup_logging()
