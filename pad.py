import json

from pprint import pprint

from readingdb.constants import Database
from readingdb.api import API

# api = API("http://localhost:8000")
# try:
#     api.create_reading_table()
# except:
#     print("table already exists homie")    

# with open("readingdb/test_data/ftg_filtered_entries.json", "r") as f:
#     entries = json.load(f)

# rid = 0

# for e in entries:
#     api.save_entry(103, 45, rid, e)
#     rid+=1

# readings = api.all_route_readings(45)

# pprint(readings)

api = API(url="https://dynamodb.ap-southeast-2.amazonaws.com")

with open("readingdb/test_data/ftg_filtered_entries.json", "r") as f:
    entries = json.load(f)

rid = 0

for e in entries:
    api.save_entry(103, 45, rid, e)
    rid+=1

readings = api.all_route_readings(45)

pprint(readings)