from typing import Any, Dict, List
from readingdb.constants import *
import json

def load_json_entries(reading_spec) -> List[Dict[str, Any]]:
    with open(reading_spec.data, "r") as f:
        entries = json.load(f)
    
    return entries

def get_entries(reading_spec) -> List[Dict[str, Any]]:
    return reading_spec.data

def txt_to_points(txt_file):
    points = []

    with open(txt_file) as f:
        lines = f.readlines()

        for line in lines:
            if line != "\n":
                segments = [s.strip("\n") for s in line.split(" ") if s != ""]    
                print(segments)            

                point = {
                    ReadingKeys.TIMESTAMP: int(segments[0].split(":")[-1]),
                    ReadingKeys.READING: {
                        PositionReadingKeys.LATITUDE: float(segments[1].split(":")[-1]),
                        PositionReadingKeys.LONGITUDE: float(segments[2].split(":")[-1])
                    },
                }

                points.append(point)

    return points

class ReadingSpec():
    JSON_ENTRIES_FORMAT = "json_entries"
    S3_FILES_FORMAT = "s3_files_format"
    GPS_FILE_FORMAT = "gps_txt_file"

    RECOGNIZED_READING_TYPES = {
        ReadingTypes.IMAGE:{
            JSON_ENTRIES_FORMAT: load_json_entries,
            S3_FILES_FORMAT: get_entries
        },
        ReadingTypes.POSITIONAL:{
            JSON_ENTRIES_FORMAT: load_json_entries
            GPS_FILE_FORMAT: decode_gps,
        },
        ReadingTypes.PREDICTION:{
            JSON_ENTRIES_FORMAT: load_json_entries
        },
        ReadingTypes.ANNOTATION:{
            JSON_ENTRIES_FORMAT: load_json_entries
        }
    }

    def __init__(self, reading_type, format, data) -> None:
        self.reading_type = reading_type
        self.format = format
        self.data = data

    def load_readings(self) -> List[Dict[str, Any]]:
        if self.reading_type not in self.RECOGNIZED_READING_TYPES:
            raise ValueError(f"Unrecognized reading type {self.reading_type} in reading specification {self}")

        if self.format not in self.RECOGNIZED_READING_TYPES[self.reading_type]:
            raise ValueError(f"Unrecognized format {self.format} for reading of type {self.reading_type} in reading {self}")

        return self.RECOGNIZED_READING_TYPES[self.reading_type][self.format](self)

