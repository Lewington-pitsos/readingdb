# import os
# import json

# with open("readingdb/test_data/ftg_filtered_entries.json", "r") as f:
#     entries = json.load(f)

# new_entries = []

# for e in entries:
#     e["ImageFileName"] = "/home/lewington/code/faultnet/" + e["ImageFileName"]
#     print(e["ImageFileName"])
#     if os.path.isfile(e["ImageFileName"]):
#         new_entries.append(e)

# with open("lel.json", "w") as f:
#     json.dump(new_entries, f, indent="    ")

from readingdb.db import DB
import time

db = DB("https://dynamodb.ap-southeast-2.amazonaws.com")

db.teardown_reading_db()


time.sleep(10)


db.create_reading_db()