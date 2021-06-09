from readingdb.constants import PositionReadingKeys, ReadingKeys
from typing import Any, Dict


class RUtils():
    @classmethod
    def get_ts(cls, reading: Dict[str, Any]) -> int:
        return reading[ReadingKeys.TIMESTAMP]

    @classmethod
    def get_type(cls, reading: Dict[str, Any]) -> str:
        return reading[ReadingKeys.TYPE]

    @classmethod
    def get_lat(cls, reading: Dict[str, Any]) -> float:
        return reading[ReadingKeys.READING][PositionReadingKeys.LATITUDE]


    @classmethod
    def get_lng(cls, reading: Dict[str, Any]) -> float:
        return reading[ReadingKeys.READING][PositionReadingKeys.LONGITUDE]