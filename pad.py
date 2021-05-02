# import json

# file_name = "cruft/entries.json"

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

# new_entries = []

# for e in entries:
#     e["Timestamp"] = e['Date']
#     del e['Date']

#     if e["ImageFileName"] != "AUS_3.jpg":
#         e["ImageFileName"] = e["ImageFileName"].replace(
#             "data/inference/sydney_fast/images/", 
#             "/home/lewington/code/faultnet/data/inference/sydney_fast/images/"
#         )
#         new_entries.append(e)

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



# with open(file_name.replace("entries", "revised_entries"), "w") as f:
#     json.dump(new_entries, f, indent="    ")

# -----------------------------------------------------------------------------

# from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_DYNAMO_ENDPOINT
# from readingdb.db import DB
# import time
# db = DB(TEST_DYNAMO_ENDPOINT)


# db.teardown_reading_db()
# time.sleep(10)
# db.create_reading_db()

# -----------------------------------------------------------------------------

# from readingdb.api import API
# from readingdb.routespec import RouteSpec
# import json

# api = API("https://dynamodb.ap-southeast-2.amazonaws.com")

# # r = api.all_route_readings("ea2f2ff0-a24a-11eb-a871-024235873144")

# # print(r)

# with open("cruft/sydney_full.json") as f:
#     route_json = json.load(f) 

# api.save_route(RouteSpec.from_json(route_json), "99bf4519-85d9-4726-9471-4c91a7677925")


# -----------------------------------------------------------------------------

# from readingdb.authresponse import AuthResponse
# from readingdb.auth import Auth
# from readingdb.endpoints import TEST_DYNAMO_ENDPOINT
# from readingdb.api import API


# auth: Auth = Auth(region_name="ap-southeast-2")
# user_data: AuthResponse = auth.get_user("eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjljYjMyZjRjLWFhMDktNDk4Yi1hYjkzLTk5ODE3ZjdmNGQxYyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTgyNjc5MzEsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTgyNzE1MzEsImlhdCI6MTYxODI2NzkzMSwianRpIjoiNmRkNGZiNWMtMTZhZS00N2JjLTg4OTEtODRkYjUzNjg0NmMwIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.EgNiuZYENTdIF7t7Zs0LC0UEPaMSc1M66fxfi4OpoLcKvCXdLax6r4wa0gdeL96N6x2PzpBmdxEoeZfSnIFq2NNtcLPXYpmONGgbmP4bxdQW1FcplE6dlvkfo6UnQQdmjTd6r6rTq6CHlHBskFWfi7YRcdbtFf8Ic9nIB2G8J8EkjN1cwGrUUrQ3CqaOuLNjUqxtP6fYgrqEk6lseWVp4P33HK8zOwPUxUuqjwtWfJK_Mchy0QL_K-HpnyUoXU5cv63_PY_OI63QYz5FHFtloTwj1iWqGdE43_tH8AdT3UJpmFNHwHijqVVpsFVmTowRuw1QskdZP-yHK4p7Ea8Y7Q")

# api = API(TEST_DYNAMO_ENDPOINT)

# api.save_new_route("mobileappsessions172800-main", "public/route_2021_04_12_20_59_16_782.zip")


# -----------------------------------------------------------------------------

import json
from readingdb.lamb import EVENT_ACCESS_TOKEN
from readingdb.constants import REGION_NAME
from readingdb.authresponse import AuthResponse
from readingdb.auth import Auth
import boto3

client = boto3.client("lambda")

auth: Auth = Auth(region_name=REGION_NAME)

user_data: AuthResponse = auth.get_user()

pl = {
    "Type": "GetReadings",
    "RouteID": "f5c110a0-aad2-11eb-9dd3-0242c8762599",
    "AccessToken": "eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjFlNjQwMjEyLTAwODItNDlkMC1iODhjLWFmNTA2NTlkNGU2NCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTk5NDUzMjQsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTk5NDg5MjQsImlhdCI6MTYxOTk0NTMyNCwianRpIjoiYzg1NDQ3MjUtZDdiNS00MzIzLTg3MWUtZGJhNGMwNDUzYjBiIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.SCAD3ZdUqTgdodAfe7BA48D-6r3tL3Jw4GFY0mQc9l0xyeeYdL5XyXMk_1gVTfYT4KiAj8xSMZ8AL_0HBgLLGvon-oq9n5CWwjaXXFvmhejEAAmTuV2ytc39N4Q1nlyFblruSulAFRNsIiZkCRLXyne6vng3ZdCvoVpZqCU9Vejw8o9ZCy5iEM9PgTPd2zmjlkEWeCm2v-A7Bdn5YIFmImRTtZWvjiDx3Kg4pxSopUjlPq0IQCUUzYYS9P6CSYBfG2OhPPiK7U_W5L9bZr4c8ulKcuF6wpDrt8kH-LdB92mtj9nRe-vVaL7OPs-IeK1Q4owLHTSzqyJ68GBQX6dtqg",
}

s=json.dumps(pl)

print("waiting for response")

resp = client.invoke(
    FunctionName="arn:aws:lambda:ap-southeast-2:950765595897:function:routesidplay-backend-lambda",
    InvocationType='RequestResponse',
    Payload=s
)

data = resp['Payload'].read()

print(data)