import logging
from tinydb import TinyDB, Query

# initialize script
logging.basicConfig(filename="prod.log", level=logging.INFO, format="%(levelname): %(asctime)s - %(message)s", datefmt='%d-%b-%y %H:%M:%S')
db = TinyDB('db.json')

