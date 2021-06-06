REGION_NAME = 'ap-southeast-2'

class Database():
    READING_TABLE_NAME = 'Readings'
    ROUTE_TABLE_NAME = 'Routes'
    PAGINATION_KEY_NAME = 'PaginationKey'
    ANNOTATOR_TABLE_NAME = 'Annotators'
class ReadingRouteKeys():
    ROUTE_ID = 'RouteID'
class ReadingKeys():
    READING_ID = 'ReadingID'
    TYPE = 'Type'
    READING = 'Reading'
    TIMESTAMP = 'Timestamp'
class RouteKeys():
    USER_ID = 'UserID'
    NAME = 'RouteName'
    SAMPLE_DATA = 'SampleData'
    STATUS = 'RouteStatus'
    TIMESTAMP = 'Timestamp'
    LAST_UPDATED = 'LastUpdated'
class AnnotatorKeys():
    ANNOTATOR_ID = 'AnnotatorID'
    NAME = 'AnnotatorName'
    ANNOTATOR_TYPE = 'AnnotatorType'
    ANNOTATOR_GROUP = "AnnotatorGroup"
    USER_ID = 'UserID'
class ReadingTypes():
    POSITIONAL = 'PositionalReading'
    IMAGE = 'ImageReading'
    PREDICTION = 'PredictionReading'
    ANNOTATION = 'Annotation'

    IMAGE_TYPES = [
        PREDICTION,
        ANNOTATION,
        IMAGE
    ]
class PositionReadingKeys():
    LATITUDE = 'Latitude'
    LONGITUDE = 'Longitude'

    FLOAT_FIELDS = [
        LATITUDE, 
        LONGITUDE
    ]

    BOOL_FIELDS = []
class EntryKeys():
    TIMESTAMP = 'Date'
class ImageReadingKeys():
    FILENAME = 'ImageFileName'
    URI = 'S3Uri'
    PRESIGNED_URL = 'PresignedURL'
class S3Path():
    BUCKET = 'Bucket'
    KEY = 'Key'
class EntityKeys():
    NAME = 'Name'
    CONFIDENCE = 'Confidence'
    PRESENT = 'Present'
    SEVERITY = 'Severity'
class PredictionReadingKeys(ImageReadingKeys):
    TIMESTAMP = EntryKeys.TIMESTAMP
    FILENAME = ImageReadingKeys.FILENAME

    LATCRACK_CONFIDENCE = 'LatCrackConfidence'
    LONGCRACK_CONFIDENCE = 'LongCrackConfidence'
    CROCODILECRACK_CONFIDENCE =  'CrocodileCrackConfidence'
    POTHOLE_CONFIDENCE = 'PotholeConfidence'
    LINEBLUR_CONFIDENCE = 'LineblurConfidence'
    GOOD_CONDITION_CONFIDENCE = 'GoodConditionConfidence'

    LATITUDE = 'Latitude'
    LONGITUDE = 'Longitude'

    IS_LATCRACK = 'IsLatCrackFault'
    IS_LONGCRACK = 'IsLongCrackFault'
    IS_CROCODILECRACK =  'IsCrocodileCrackFault'
    IS_POTHOLE = 'IsPotholeFault'
    IS_LINEBLUR = 'IsLineblurFault'
    IS_GOOD_CONDITION = 'IsGoodCondition'
    
    ENTITIES = 'Entities'