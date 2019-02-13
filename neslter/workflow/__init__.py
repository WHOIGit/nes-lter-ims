import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.level = logging.DEBUG