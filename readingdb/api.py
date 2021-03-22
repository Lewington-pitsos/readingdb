from readingdb.db import DB
from readingdb.normalize import *
from readingdb.constants import *

class API(DB):
    def __init__(self, url, resource_name='dynamodb'):
        super().__init__(url, resource_name=resource_name)

    def save_entry(self, route_id, user_id, reading_id, entry):

        ts = entry[EntryKeys.TIMESTAMP]

        if isinstance(ts, float):
            ts = int(ts)
        self.put_reading(
            route_id,
            user_id,
            reading_id,
            ReadingTypes.PREDICTION,
            entry_to_prediction(entry),
            ts
        )
