import logging

global _logger

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
_logger = logging.getLogger()

class Logger:

    @staticmethod
    def get_logger():
        return _logger

