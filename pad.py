# import json

# file_name = "readingdb/test_data/tst_imgs.json"

# with open(file_name, "r") as f:
#     entries = json.load(f)

# keys = [
#     "LongCrack",
#     "LatCrack",
#     "CrocodileCrack",
#     "Pothole",
#     "Lineblur",
# ]

# for e in entries:
#     entities = []
#     for k in keys:
#         entities.append({
#             "Name": k,
#             "Confidence": e["Reading"][k + "Confidence"],
#             "Present": e["Reading"]["Is" + k + "Fault"]
#         })
#         del e["Reading"][k + "Confidence"]
#         del e["Reading"]["Is" + k + "Fault"]

#     e['Reading']["Entities"] = entities

# with open(file_name, "w") as f:
#     json.dump(entries, f, indent="    ")

# -----------------------------------------------------------------------------

# from readingdb.db import DB
# import time

# db = DB("https://dynamodb.ap-southeast-2.amazonaws.com")

# db.teardown_reading_db()
# time.sleep(10)
# db.create_reading_db()

# -----------------------------------------------------------------------------

from readingdb.api import API
from readingdb.routespec import RouteSpec
import json


api = API("https://dynamodb.ap-southeast-2.amazonaws.com")

with open("readingdb/test_data/ftg_route.json") as f:
    route_json = json.load(f) 

api.upload(RouteSpec.from_json(route_json), "99bf4519-85d9-4726-9471-4c91a7677925")