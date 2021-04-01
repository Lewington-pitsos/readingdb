# import os
# import json

# with open("readingdb/test_data/sample_readings.json", "r") as f:
#     entries = json.load(f)

# new_entries = []

# for e in entries:
#     e["Reading"]["ImageFileName"] = e["Reading"]["Basis"]["ImageFileName"]
#     del e["Reading"]["Basis"]
    

# with open("readingdb/test_data/sample_readings.json", "w") as f:
#     json.dump(entries, f, indent="    ")

from readingdb.db import DB
import time

db = DB("https://dynamodb.ap-southeast-2.amazonaws.com")

db.teardown_reading_db()


time.sleep(10)


db.create_reading_db()