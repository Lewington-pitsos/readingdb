from typing import Any, Dict, List
from readingdb.constants import *
import json

def load_json_entries(reading_spec) -> List[Dict[str, Any]]:
    with open(reading_spec.path, "r") as f:
        entries = json.load(f)
    
    return entries
class ReadingSpec():
    JSON_ENTRIES_FORMAT = "json_entries"
    S3_FILES_FORMAT = "s3_files_format"


    RECOGNIZED_READING_TYPES = {
        ReadingTypes.IMAGE:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        ReadingTypes.POSITIONAL:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        ReadingTypes.PREDICTION:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        ReadingTypes.ANNOTATION:{
            JSON_ENTRIES_FORMAT: load_json_entries
        }
    }
    

    def __init__(self, reading_type, format, path) -> None:
        self.reading_type = reading_type
        self.format = format
        self.path = path

    def load_readings(self) -> List[Dict[str, Any]]:
        if self.reading_type not in self.RECOGNIZED_READING_TYPES:
            raise ValueError(f"Unrecognize reading type {self.reading_type} in reading specification {self}")

        if self.format not in self.RECOGNIZED_READING_TYPES[self.reading_type]:
            raise ValueError(f"Unrecognize format {self.format} for reading of type {self.reading_type} in reading {self}")

        return self.RECOGNIZED_READING_TYPES[self.reading_type][self.format](self)

