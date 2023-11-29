import logging


def get_logger(name):
    if logging.getLogger().hasHandlers():
        log_fmt = f"[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(aws_request_id)s\t{name}\t%(message)s\n"
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        for h in logger.handlers:
            h.setFormatter(logging.Formatter(log_fmt))
    else:
        log_fmt = "[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(name)s\t%(message)s\n"
        logging.basicConfig(level=logging.INFO, format=log_fmt)
        logger = logging.getLogger(name)
    logging.getLogger("pymc").setLevel(logging.WARNING)
    return logger
