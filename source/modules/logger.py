import logging

def create_logger(logger_name):
    # Set up the logger.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create a logger specific to the specified name
    logger = logging.getLogger(logger_name.capitalize())
    return logger