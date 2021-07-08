from readingdb.constants import Constants
from typing import Any, Dict


class RUtils():
    @classmethod
    def get_ts(cls, reading: Dict[str, Any]) -> int:
        return reading[Constants.TIMESTAMP]

    @classmethod
    def get_type(cls, reading: Dict[str, Any]) -> str:
        return reading[Constants.TYPE]

    @classmethod
    def get_lat(cls, reading: Dict[str, Any]) -> float:
        return reading[Constants.READING][Constants.LATITUDE]
    @classmethod
    def get_lng(cls, reading: Dict[str, Any]) -> float:
        return reading[Constants.READING][Constants.LONGITUDE]

    @classmethod
    def get_uri(cls, reading: Dict[str, Any]) -> float:
        return reading[Constants.READING][Constants.URI]

    @classmethod
    def get_filename(cls, reading: Dict[str, Any]) -> float:
        return reading[Constants.READING][Constants.FILENAME]