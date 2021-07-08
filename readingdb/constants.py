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

    # Prediction Reading Keys
    ENTITIES = 'Entities'
    ANNOTATOR_ID = 'AnnotatorID'
    ANNOTATION_TIMESTAMP = 'AnnotationTimestamp'

    # Route Keys
    USER_ID = 'UserID'
    NAME = 'RouteName'
    SAMPLE_DATA = 'SampleData'
    STATUS = 'RouteStatus'
    TIMESTAMP = 'Timestamp'
    LAST_UPDATED = 'LastUpdated'

    # S3 Path
    BUCKET = 'Bucket'
    KEY = 'Key'

    # Entity Keys
    NAME = 'Name'
    CONFIDENCE = 'Confidence'
    PRESENT = 'Present'
    SEVERITY = 'Severity'

    # Data Access Group
    GROUP_NAME = 'GroupName'
    GROUP_ID = 'GroupID'

DEFAULT_ANNOTATOR_NAME = "LoukaSean"
DEFAULT_ANNOTATOR_ID = "99bf4519-85d9-4726-9471-4c91a7677925"
FAUX_ANNOTATOR_ID = "3f01d5ec-c80b-11eb-acfa-02428ee80691"