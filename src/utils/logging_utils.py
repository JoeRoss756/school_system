import logging

level_numeric = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}
logging.basicConfig(filename="logs/school.log",
                    filemode='w',
                    level=level_numeric['INFO'],
                    format='%(name)s-%(levelname)s-%(asctime)s: %(message)s'
                    )
logger = logging.getLogger(__name__)
logger.info('initializing basic logger.')

