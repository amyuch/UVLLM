import logging

def initLogger(path, cmdLevel = logging.DEBUG, fileLevel = logging.DEBUG):
    logger = logging.getLogger(path)
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # cmd log
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.setLevel(cmdLevel)
    # file log
    fh = logging.FileHandler(path)
    fh.setFormatter(fmt)
    fh.setLevel(fileLevel)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger

def get_recent_logs(logger, num_lines=10):
    """
    Retrieve the most recent log entries.

    Args:
        logger: The logger object.
        num_lines (int): Number of recent log lines to retrieve.

    Returns:
        str: Recent log entries as a string.
    """
    log_records = []
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            with open(handler.baseFilename, 'r') as log_file:
                log_records = log_file.readlines()[-num_lines:]
    return ''.join(log_records)
