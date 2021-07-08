REGION_NAME = 'ap-southeast-2'

LAT = 'lat'
LNG = 'lng'

ANNOTATOR_PREFERENCE = [
    '2f11b71a-cecf-40b8-ab6b-8c73e4254b26'
]

class Constants():
    # User
    USER_ID = 'UserID'
    DATA_ACCESS_GROUPS = 'DataAccessGroups'
    
    # Database
    READING_TABLE_NAME = 'Readings'
    ROUTE_TABLE_NAME = 'Routes'
    PAGINATION_KEY_NAME = 'PaginationKey'
    USER_TABLE_NAME = 'Annotators'

    # Reading Types
    POSITIONAL = 'PositionalReading'
    IMAGE = 'ImageReading'
    PREDICTION = 'PredictionReading'

    # Reading Keys
    ROUTE_ID = 'RouteID'
    READING_ID = 'ReadingID'
    TYPE = 'Type'
    READING = 'Reading'
    TIMESTAMP = 'Timestamp'

    # Positional Reading Keys
    LATITUDE = 'Latitude'
    LONGITUDE = 'Longitude'
    PLACE_ID = 'PlaceID'

    # Image Reading Keys
    FILENAME = 'ImageFileName'
    URI = 'S3Uri'
    PRESIGNED_URL = 'PresignedURL'

    # Route Keys
    USER_ID = 'UserID'
    NAME = 'RouteName'
    SAMPLE_DATA = 'SampleData'
    STATUS = 'RouteStatus'
    TIMESTAMP = 'Timestamp'
    LAST_UPDATED = 'LastUpdated'

    # Entry Keys
    TIMESTAMP = 'Date'

    # S3 Path
    BUCKET = 'Bucket'
    KEY = 'Key'

    # Entity Keys
    NAME = 'Name'
    CONFIDENCE = 'Confidence'
    PRESENT = 'Present'
    SEVERITY = 'Severity'


class PredictionReadingKeys(ImageReadingKeys):
    TIMESTAMP = EntryKeys.TIMESTAMP
    FILENAME = Constants.FILENAME

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
    
    ANNOTATOR_ID = 'AnnotatorID'
    ANNOTATION_TIMESTAMP = 'AnnotationTimestamp'

class DataAccessGroupKeys():
    GROUP_NAME = 'GroupName'
    GROUP_ID = 'GroupID'

DEFAULT_ANNOTATOR_NAME = "LoukaSean"
DEFAULT_ANNOTATOR_ID = "99bf4519-85d9-4726-9471-4c91a7677925"
FAUX_ANNOTATOR_ID = "3f01d5ec-c80b-11eb-acfa-02428ee80691"