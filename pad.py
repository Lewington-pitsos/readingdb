# import os
# import json

# with open("readingdb/test_data/ftg_imgs.json", "r") as f:
#     entries = json.load(f)

# keys = [
#     "Latitude",
#     "Longitude",
#     "LongCrackConfidence",
#     "LatCrackConfidence",
#     "CrocodileCrackConfidence",
#     "PotholeConfidence",
#     "LineblurConfidence",
#     "ImageFileName",
#     "IsLongCrackFault",
#     "IsLatCrackFault",
#     "IsCrocodileCrackFault",
#     "IsPotholeFault",
#     "IsLineblurFault",
# ]

# for e in entries:
#     e["Reading"] = {}
    
#     for k in keys:
#         e["Reading"][k] = e[k]
#         del e[k]    

# with open("readingdb/test_data/ftg_imgs.json", "w") as f:
#     json.dump(entries, f, indent="    ")

# from readingdb.db import DB
# import time

# db = DB("https://dynamodb.ap-southeast-2.amazonaws.com")

# db.teardown_reading_db()


# time.sleep(10)


# db.create_reading_db()

from readingdb.auth import Auth

a = Auth()

a.get_user()

# from readingdb.api import API
# from readingdb.routespec import RouteSpec
# import json


# api = API("https://dynamodb.ap-southeast-2.amazonaws.com")

# with open("readingdb/test_data/ftg_20_route.json") as f:
#     route_json = json.load(f) 

# api.upload(RouteSpec.from_json(route_json), "99bf4519-85d9-4726-9471-4c91a7677925")