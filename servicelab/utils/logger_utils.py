import os
import sys
import logging

loggers = {}

def SLAB_Logger(verbosity, name='stack'):
    global loggers
                                                                              
    if loggers.get(name):                                                     
        return loggers.get(name)                                              
    else:                                                                     
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)                                        
        logging.addLevelName(15, 'DETAIL')
                                                                              
        # Create filehandler that logs everything.
        pardir = os.path.dirname
        path = os.path.join(pardir(pardir(os.path.abspath(__file__))), '.stack')
        import pdb
        pdb.set_trace()
        file_handler = logging.FileHandler(os.path.join(path, 'stack.log'))
        file_handler.setLevel(logging.DEBUG)

        # Create formatter and add it to the handlers
        formatter = logging.Formatter("%(asctime)s - %(name)s - "
                                      "%(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
                                                                              
        # Add handlers to the logger
        logger.addHandler(file_handler)
                                                                              
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(verbosity)
        logger.addHandler(console_handler)                                    
                                                                              
        loggers.update(dict(name=logger))
                                                                              
        return logger                                                         

