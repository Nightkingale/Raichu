import logging

def create_logger(logger_name):
    # Set up the logger.
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )

    # Create a logger specific to the specified name
    logger = logging.getLogger(logger_name.capitalize())
    return logger