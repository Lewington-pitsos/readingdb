import time

from pprint import pprint

from readingdb.db import DB
from readingdb.constants import *

db = DB("http://localhost:8000")

start_id = 4

for i in range(800):
    add_response = db.put_reading(
        103,
        3,
        start_id + i,
        ReadingTypes.POSITIONAL,
        {
            PositionReadingKeys.LATITUDE: 41.86648, 
            PositionReadingKeys.LONGITUDE: -174.39999
        },
        int(time.time())
    )
    print("Put reading succeeded:")
    pprint(add_response, sort_dicts=False)