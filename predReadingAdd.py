import time

from pprint import pprint

from readingdb.db import DB
from readingdb.constants import *

db = DB("http://localhost:8000")

start_id = 4

for i in range(20):
    add_response = db.put_reading(
        103,
        3,
        start_id + i,
        ReadingTypes.PREDICTION,
        {
            PredictionReading.BASIS: {
                PredictionBasis.FILENAME: "https://aws/s3/somebucket/file.jpg"
            },
            PredictionReading.CROCODILECRACK_CONFIDENCE: 0.72510201,
            PredictionReading.LATCRACK_CONFIDENCE: 0.119,
            PredictionReading.LINEBLUR_CONFIDENCE: 0.00011,
            PredictionReading.GOOD_CONDITION_CONFIDENCE: 0.0000901,
            PredictionReading.IS_CROCODILECRACK: True,
            PredictionReading.LATITUDE: 41.86648,
            PredictionReading.LONGITUDE:  -174.39999
        },
        int(time.time())
    )
    print("Put reading succeeded:")
    pprint(add_response, sort_dicts=False)