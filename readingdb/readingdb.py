import abc
from readingdb.routespec import RouteSpec
from typing import Any, Dict, List, Tuple

from readingdb.route import Route
from readingdb.reading import Reading
from readingdb.readingspec import ReadingSpec

class ReadingDB(abc.ABC):
    @abc.abstractmethod
    def set_as_predicting(self, route_id: str, user_id: str) -> None:
        """Updates the status of the specified route to predicting (indicating
        that a prediction process is under way).
        """
        raise NotImplementedError() 
    
    @abc.abstractmethod
    def begin_prediction(self, user_id: str, route_id: str) -> None:
        """Sends a message to the prediction queue that requests
        predictions be made for the given route and user.

        Args:
            route_id (str): [description]
            user_id (str): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError()


   # -------------- Writing Methods -------------- 

    @abc.abstractmethod
    def save_route(self, reading_spec: ReadingSpec, user_id: str) -> Route:
        """Uploads all readings listed within reading_spec as a single route.
        Returns the ID of the newly created route.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_new_route(self, bucket: str, key: str):
        """Adds a new route to the database that contains the readings in the 
        specified zipped file.

        Args:
            bucket (str): the s3 bucket where the readings are kept.
            key (str): the key in that bucket where the zipped file sits.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_predictions(self, readings: List[Dict[str, Any]], route_id: int, user_id: str) -> None:
        """Saves the prediction readings to the given route and sets the status
        of that route to 'complete'.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def update_route_name(self, route_id: str, user_id: str, name: str) -> None:
        """Sets the name of the given route to the given name.
        """
        raise NotImplementedError()

    # -------------- Reading Methods -------------- 

    @abc.abstractmethod
    def all_route_readings(self, route_id: int, user_id: str, key: str) -> List[Dict[str, Any]]:
        """Returns all readings (e.g. gps readings, accelerometer readings, 
        camera image readings, prior predictions) associated with that route.

        The key tells the api what key to upload the reading data to s3 with if 
        it needs to upload to s3 because there is too much data.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def all_route_readings_async(self, route_id: str, access_token: str) -> List[Dict[str, Any]]:
        """Calls a lambda that contains readingdb and gets THAT lambda
        to execute all_route_readings. That lambda will upload a file
        to s3 and a client can poll for that file. An access token must be
        provided so that an additional lambda call can be made.

        Returns an s3 uri for where the file will be uploaded to. 
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Loads and returns all the routes for the given user
        including sample readings only.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_route(self, route_id: str, user_id: str) -> Dict[str, Any]:
        """Loads and returns all the specified route
        """
        raise NotImplementedError()