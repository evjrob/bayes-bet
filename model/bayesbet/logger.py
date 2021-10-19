import logging


def get_logger(name):
    if logging.getLogger().hasHandlers():
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
    else:
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(level=logging.INFO, format=log_fmt)
        logger = logging.getLogger(name)
    return logger