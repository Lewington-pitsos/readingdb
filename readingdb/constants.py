class Database():
    READING_TABLE_NAME = "Readings"
    ROUTE_TABLE_NAME = "Routes"




class ReadingRouteKeys():
    ROUTE_ID = "RouteID"

class ReadingKeys():
    READING_ID = "ReadingID"
    TYPE = "Type"
    READING = "Reading"
    TIMESTAMP = "Timestamp"

class RouteKeys():
    USER_ID = "UserID"
    NAME = 'Name'

class ReadingTypes():
    POSITIONAL = "PositionalReading"
    IMAGE = "ImageReading"
    PREDICTION = "PredictionReading"


class PositionReading():
    LATITUDE = "Latitude"
    LONGITUDE = "Longitude"

    FLOAT_FIELDS = [
        LATITUDE, 
        LONGITUDE
    ]

    BOOL_FIELDS = []

class ImageReading():
    FILENAME = "ImageFileName"
class PredictionReading():
    BASIS = "Basis"

    LATCRACK_CONFIDENCE = "LatCrackConfidence"
    LONGCRACK_CONFIDENCE = "LongCrackConfidence"
    CROCODILECRACK_CONFIDENCE =  "CrocodileCrackConfidence"
    POTHOLE_CONFIDENCE = "PotholeConfidence"
    LINEBLUR_CONFIDENCE = "LineblurConfidence"
    GOOD_CONDITION_CONFIDENCE = "GoodConditionConfidence"

    LATITUDE = "Latitude"
    LONGITUDE = "Longitude"

    IS_LATCRACK = "IsLatCrackFault"
    IS_LONGCRACK = "IsLongCrackFault"
    IS_CROCODILECRACK =  "IsCrocodileCrackFault"
    IS_POTHOLE = "IsPotholeFault"
    IS_LINEBLUR = "IsLineblurFault"
    IS_GOOD_CONDITION = "IsGoodCondition"

    FLOAT_FIELDS = [
        LATCRACK_CONFIDENCE,
        LONGCRACK_CONFIDENCE,
        CROCODILECRACK_CONFIDENCE,
        POTHOLE_CONFIDENCE,
        LINEBLUR_CONFIDENCE,
        GOOD_CONDITION_CONFIDENCE,
        LATITUDE,
        LONGITUDE
    ]

    BOOL_FIELDS = [
        IS_LATCRACK,
        IS_LONGCRACK,
        IS_CROCODILECRACK,
        IS_POTHOLE,
        IS_LINEBLUR
    ]

    FIELDS = FLOAT_FIELDS + BOOL_FIELDS + [BASIS]
    

class PredictionBasis():
    FILENAME = "ImageFileName"

class EntryKeys():
    TIMESTAMP = "Date"