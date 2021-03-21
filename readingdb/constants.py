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
    POSITIONAL = "positionalReading"
    IMAGE = "imageReading"
    PREDICTION = "predictionReading"


class PositionReading():
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    ENCODING_COEFFICIENT = 1e+15

    FLOAT_FIELDS = [
        LATITUDE, 
        LONGITUDE
    ]

    BOOL_FIELDS = []

class ImageReading():
    FILENAME = "filename"
class PredictionReading():
    BASIS = "basis"

    LATCRACK_CONFIDENCE = "latCrackConfidence"
    LONGCRACK_CONFIDENCE = "longCrackConfidence"
    CROCODILECRACK_CONFIDENCE =  "crocodileCrackConfidence"
    POTHOLE_CONFIDENCE = "potholeConfidence"
    LINEBLUR_CONFIDENCE = "lineblurConfidence"
    GOOD_CONDITION_CONFIDENCE = "goodConditionConfidence"

    LATITUDE = "latitude"
    LONGITUDE = "longitude"

    IS_LATCRACK = "isLatCrackFault"
    IS_LONGCRACK = "isLongCrackFault"
    IS_CROCODILECRACK =  "isCrocodileCrackFault"
    IS_POTHOLE = "isPotholeFault"
    IS_LINEBLUR = "isLineblurFault"
    IS_GOOD_CONDITION = "isGoodCondition"

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
    ENCODING_COEFFICIENT = 1e+15

    BOOL_FIELDS = [
        IS_LATCRACK,
        IS_LONGCRACK,
        IS_CROCODILECRACK,
        IS_POTHOLE,
        IS_LINEBLUR
    ]

class PredictionBasis():
    FILENAME = "filename"