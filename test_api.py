import json

from pprint import pprint

from readingdb.constants import Database
from readingdb.api import API

api = API("http://localhost:8000")
api.create_reading_table()
tables = api.all_tables()
print("tables", tables)

with open("test_data/entries.json", "r") as f:
    entries = json.load(f)

rid = 0

for e in entries[500:600]:
    api.save_entry(103, 45, rid, e)
    rid+=1

pprint(api.all_route_readings(45))
api.delete_table(Database.READING_TABLE_NAME)