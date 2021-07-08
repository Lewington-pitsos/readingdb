from typing import Any, Dict, List
from readingdb.constants import *
import json

def load_json_entries(reading_spec) -> List[Dict[str, Any]]:
    with open(reading_spec.data, 'r') as f:
        entries = json.load(f)
    
    return entries

def get_entries(reading_spec) -> List[Dict[str, Any]]:
    return reading_spec.data

class ReadingSpec():
    JSON_ENTRIES_FORMAT = 'json_entries'
    S3_FILES_FORMAT = 's3_files_format'
    GPS_FILE_FORMAT = 'gps_txt_file'

    RECOGNIZED_READING_TYPES = {
        Constants.IMAGE:{
            JSON_ENTRIES_FORMAT: load_json_entries,
            S3_FILES_FORMAT: get_entries
        },
        Constants.POSITIONAL:{
            JSON_ENTRIES_FORMAT: load_json_entries,
            S3_FILES_FORMAT: get_entries
        },
        Constants.PREDICTION:{
            JSON_ENTRIES_FORMAT: load_json_entries,
            S3_FILES_FORMAT: get_entries
        }
    }

    def __init__(self, reading_type, format, data) -> None:
        self.reading_type = reading_type
        self.format = format
        self.data = data

    def load_readings(self) -> List[Dict[str, Any]]:
        if self.reading_type not in self.RECOGNIZED_READING_TYPES:
            raise ValueError(f'Unrecognized reading type {self.reading_type} in reading specification {self}')

        if self.format not in self.RECOGNIZED_READING_TYPES[self.reading_type]:
            raise ValueError(f'Unrecognized format {self.format} for reading of type {self.reading_type} in reading {self}')

        return self.RECOGNIZED_READING_TYPES[self.reading_type][self.format](self)

