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
from readingdb.endpoints import DYNAMO_ENDPOINT
from readingdb.api import API

at = "eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6Ijg4NjAyOTgzLWZhN2UtNDI2Ni05ODBhLWUyOTRmN2Y1Y2FkNCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTk5ODA5MDEsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTk5ODQ1MDEsImlhdCI6MTYxOTk4MDkwMSwianRpIjoiNDc4ZjE1YjMtMThlNS00ZjhkLWJkMmUtNjVmZjcyMTZmOTg3IiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.gEv-4EbGsbpL_3xRbMHhYZ1GtBxZ9lM8lCX_AKLb4GaAPkycxMdth_WbO9MA7C2H-d6fnKMikyzUrpo9ZZ1xJuMmZ8j-J2UYP1JVpxIZKjtJxmqz_IYsNhx5C5vGowBWXq1rxWTOR2h14qMMUNNkgJ2v17WAkTdlH1bheFkuzNNljNSIJp2_g8RApX_G7QsyI6nMqrWLdzG-5e6tTBa6oRGvyRpLZiHaKpbxTTpytXsZMnJCLIEuVWA4XBJ5_C1hLa5gvjQPU2ReUyU3LO6GKfck4JunRRzvRZ3dg7xsZIOQmj4JUEo7lCGFGqvJPl_BMP6DoFXr36BJp5P8krn_YQ"
api = API(DYNAMO_ENDPOINT)

key = api.all_route_readings_async("99bf4519-85d9-4726-9471-4c91a7677925", at)

print(key)