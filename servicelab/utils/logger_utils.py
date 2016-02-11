import os
import sys
import logging

def setup_logger(verbosity=os.environ.get('verbosity'), name='stack'):
    logger = logging.getLogger(name)
    if not len(logger.handlers):
        #logger.setLevel(verbosity)                                        
        logging.addLevelName(15, 'DETAIL')
                                                                              
        # Create filehandler that logs everything.
        pardir = os.path.dirname
        path = os.path.join(pardir(pardir(os.path.abspath(__file__))), '.stack')
        #file_handler = logging.FileHandler(os.path.join(path, 'stack.log'))
        #file_handler.setLevel(logging.DEBUG)

        # Create formatter and add it to the handlers
        #formatter = logging.Formatter("%(asctime)s - %(name)s - "
        #                              "%(levelname)s - %(message)s")
        #file_handler.setFormatter(formatter)
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            filename=os.path.join(path, 'stack.log'),
                            filemode='a')
                                                                              
        # Add handlers to the logger
        #logger.addHandler(file_handler)

        ch_formatter = logging.Formatter('%(levelname)-6s - %(name)s - %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ch_formatter)
        console_handler.setLevel(verbosity)
        logger.addHandler(console_handler)                                    
                                                                              
    return logger                                                         
