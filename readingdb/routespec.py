from typing import Dict, List

from readingdb.readingspec import ReadingSpec

class RouteSpec():
    ROUTE_NAME_KEY = "route"
    ROUTE_READINGS_KEY = "readings"
    READING_TYPE_KEY = "type"
    READING_FORMAT_KEY = "format"
    READING_PATH_KEY = "path"

    @staticmethod
    def from_json(json_data: Dict[str, any]):
        readings: List[ReadingSpec] = []
        for r in json_data[RouteSpec.ROUTE_READINGS_KEY]:
            readings.append(ReadingSpec(
                r[RouteSpec.READING_TYPE_KEY],
                r[RouteSpec.READING_FORMAT_KEY],
                r[RouteSpec.READING_PATH_KEY]
            ))

        return RouteSpec(
            readings,
            json_data[RouteSpec.ROUTE_NAME_KEY] if RouteSpec.ROUTE_NAME_KEY in json_data else None
        )

    def __init__(self, readings: List[ReadingSpec], name: str = None) -> None:
        self.reading_specs = readings
        self.name = name