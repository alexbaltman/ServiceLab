import os
import sys
import logging


class SLAB_Formatter(logging.Formatter):
    """
    Sets up the formatter for console based on the logger level, specfically so
    ECHO outputs the same as click.echo
    """
    FORMATS = {25: '%(message)s',
               'DEFAULT': '%(levelname)-6s - %(name)s - %(message)s'}

    def format(self, record):
        self._fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        return logging.Formatter.format(self, record)


def setup_logger(verbosity, name='stack'):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.addLevelName(15, 'DETAIL')
        logging.addLevelName(25, 'ECHO')

        # Create filehandler that logs everything.
        pardir = os.path.dirname
        path = os.path.join(pardir(pardir(os.path.abspath(__file__))), '.stack')

        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            filename=os.path.join(path, 'stack.log'),
                            filemode='a')

        # Create console handler that displays based on verbosity level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(SLAB_Formatter())
        console_handler.setLevel(verbosity)
        logger.addHandler(console_handler)

    return logger
