class Database():
    READING_TABLE_NAME = "Readings"

class Keys():
    READING_ID = "readingID"
    ROUTE_ID = "routeID"
    USER_ID = "userID"
    TYPE = "type"
    READING = "reading"
    TIMESTAMP = "timestamp"

class ReadingTypes():
    POSITIONAL = "PositionalReading"
    IMAGE = "ImageReading"


class PositionReading():
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    ENCODING_COEFFICIENT = 1e+15
class ImageReading():
    FILENAME = "filename"