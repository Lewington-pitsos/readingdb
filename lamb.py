import logging

from readingdb.api import API
from readingdb.constants import LambdaEvents
from readingdb.auth import Auth
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info('Event: %s', event)

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com", config=Config(
        region_name="ap-southeast-2",
    ))

    route_id = event[LambdaEvents.ROUTE_ID]
    readings = api.all_route_readings(route_id, user_id="eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjBkOTVmZDBmLTBiNjUtNDFiMC1hMWMyLWMxYWM0NTJjNDE3NyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTc3ODA3NDgsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTc3ODQzNDgsImlhdCI6MTYxNzc4MDc0OCwianRpIjoiZDYzZmE5MTEtNDQ1MS00MTg3LWIxNGMtNmE5NGRkMzQ0NDhhIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.KJht9C0OPRsAUwykWFA1vv5WDHWa6gS-LoNrmfrJjKYYTrR1wtiJRYROwhh2Ft_AGpFc0hqFRwXrJM0z4FHLT8mxGujidoMKnUVT9CJyKludrdJlsV9gxmjxugX9pSK_ACB2AqVe_mLqPoDkIuHJ4Ju8xHFt5KjYXqfbeou4smFiBTc2pssj9gwLd9STuw2kha11NvsWaH-ub23folp4hfIMGZ5xVDG1fimqIDhzqJTyplDzRD0Gvm7RqfPwrGSo0T4PQpXYfz7gi0zeuKCI4BR5MM5MbPOWqra7o-kNC6OlIcn9vb5GA2r9TlbYjWu6E4iuITN01SBACdxEB4fTCg")

    logger.info(f"Found {len(readings)} for route {route_id} readings")

    response = {'result': readings}
    return response