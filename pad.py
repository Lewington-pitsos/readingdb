# import json

# file_name = "readingdb/test_data/sydney_filtered.json"

# with open(file_name, "r") as f:
#     entries = json.load(f)

# fault_keys = [
#     "LongCrack",
#     "LatCrack",
#     "CrocodileCrack",
#     "Pothole",
#     "Lineblur",
# ]

# keys = [
#     "ImageFileName",
#     "Latitude",
#     "Longitude"
# ]

# for e in entries:
#     e["Timestamp"] = e['Date']
#     del e['Date']

#     entities = []
#     for k in fault_keys:
#         entities.append({
#             "Name": k,
#             "Confidence": e[k + "Confidence"],
#             "Present": e["Is" + k + "Fault"]
#         })
#         del e[k + "Confidence"]
#         del e["Is" + k + "Fault"]

#     e["Reading"] = {}
#     e['Reading']["Entities"] = entities

#     for k in keys:
#         e["Reading"][k] = e[k]
#         del e[k]

# with open(file_name, "w") as f:
#     json.dump(entries, f, indent="    ")

# -----------------------------------------------------------------------------

# from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_DYNAMO_ENDPOINT
# from readingdb.db import DB
# import time
# db = DB(TEST_DYNAMO_ENDPOINT)


# db.teardown_reading_db()
# time.sleep(10)
# db.create_reading_db()

# -----------------------------------------------------------------------------

from readingdb.api import API
from readingdb.routespec import RouteSpec
import json

api = API("https://dynamodb.ap-southeast-2.amazonaws.com")

r = api.all_route_readings("ea2f2ff0-a24a-11eb-a871-024235873144")

print(r)

# with open("readingdb/test_data/gps_img_route.json") as f:
#     route_json = json.load(f) 

# api.save_route(RouteSpec.from_json(route_json), "62af2bda-a15f-43b7-a84a-55f9908351c7")


# -----------------------------------------------------------------------------

# from readingdb.authresponse import AuthResponse
# from readingdb.auth import Auth
# from readingdb.endpoints import TEST_DYNAMO_ENDPOINT
# from readingdb.api import API


# auth: Auth = Auth(region_name="ap-southeast-2")
# user_data: AuthResponse = auth.get_user("eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjljYjMyZjRjLWFhMDktNDk4Yi1hYjkzLTk5ODE3ZjdmNGQxYyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTgyNjc5MzEsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTgyNzE1MzEsImlhdCI6MTYxODI2NzkzMSwianRpIjoiNmRkNGZiNWMtMTZhZS00N2JjLTg4OTEtODRkYjUzNjg0NmMwIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.EgNiuZYENTdIF7t7Zs0LC0UEPaMSc1M66fxfi4OpoLcKvCXdLax6r4wa0gdeL96N6x2PzpBmdxEoeZfSnIFq2NNtcLPXYpmONGgbmP4bxdQW1FcplE6dlvkfo6UnQQdmjTd6r6rTq6CHlHBskFWfi7YRcdbtFf8Ic9nIB2G8J8EkjN1cwGrUUrQ3CqaOuLNjUqxtP6fYgrqEk6lseWVp4P33HK8zOwPUxUuqjwtWfJK_Mchy0QL_K-HpnyUoXU5cv63_PY_OI63QYz5FHFtloTwj1iWqGdE43_tH8AdT3UJpmFNHwHijqVVpsFVmTowRuw1QskdZP-yHK4p7Ea8Y7Q")

# api = API(TEST_DYNAMO_ENDPOINT)

# api.save_new_route("mobileappsessions172800-main", "public/route_2021_04_12_20_59_16_782.zip")
