import os
import sys
import logging


class SLAB_Formatter(logging.Formatter):
    """
    Sets up the formatter for console based on the logger level, specfically so
    ECHO (verbosity level 25) outputs with no formatting like click.echo

    Unabashedly stolen from http://stackoverflow.com/questions/1343227/
    """
    FORMATS = {25: '%(message)s',
               'DEFAULT': '%(levelname)-6s - %(name)s - %(message)s'}

    def format(self, record):
        self._fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        return logging.Formatter.format(self, record)


def setup_logger(verbosity, name='stack'):
    """
    Configure the file and screen logger handlers

    Logger levels Warning (30) and higher will always print to screen regardless of
        verbosity setting.  The Servicelab default is set to 25 for Echo and higher.
        Messages sent to screen will be of the verbosity level specified and higher.
        All messages will be logged to file, regardless of verbosity level specified.

    Args:
        verbosity (int): Level of screen verbosity.  Currently should be:
            10 => Debug  -vvv
            15 => Detail -vv
            20 => Info   -v
            25 => Echo   <no verbosity specified>
        name (str): Name of the logger.  This will be reflected in the log outputs for all
            levels of logging except Echo (25).  The name should be stack.<cmd> or
            stack.utils.<util>

    Returns:
        Logger object

    Example Usage:
        slab_logger = logger_utils.setup_logger(verbosity_level, 'stack.cmd_name')
        slab_logger.debug('This is a debug message for -vvv(or even more v's, if you like)')
        slab_logger.log(15, 'This is a detail message for -vv verbosity level')
        slab_logger.info('This is an info message for -v verbosity level')
        slab_logger.log(25, 'This is an echo message for all verbosity levels')
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.addLevelName(15, 'DETAIL')
        logging.addLevelName(25, 'ECHO')

        # Create filehandler that logs everything.
        pardir = os.path.dirname
        path = os.path.join(pardir(pardir(os.path.abspath(__file__))), '.stack')
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s - %(levelname)-6s - %(name)s - %(message)s",
                            filename=os.path.join(path, 'stack.log'),
                            filemode='a')

        # Create console handler that displays based on verbosity level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(SLAB_Formatter())
        console_handler.setLevel(verbosity)
        logger.addHandler(console_handler)

    return logger
