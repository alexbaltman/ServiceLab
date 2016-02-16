import os
import sys
import logging

def setup_logger(verbosity, name='stack'):
    logger = logging.getLogger(name)
    if not len(logger.handlers):
        logging.addLevelName(15, 'DETAIL')

        # Create filehandler that logs everything.
        pardir = os.path.dirname
        path = os.path.join(pardir(pardir(os.path.abspath(__file__))), '.stack')

        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            filename=os.path.join(path, 'stack.log'),
                            filemode='a')

        # Create console handler that displays based on verbosity level
        ch_formatter = logging.Formatter('%(levelname)-6s - %(name)s - %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ch_formatter)
        console_handler.setLevel(verbosity)
        logger.addHandler(console_handler)

    return logger
