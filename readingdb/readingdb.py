import abc
from readingdb.routespec import RouteSpec
from typing import Any, Dict, List, Tuple

from readingdb.route import Route
from readingdb.reading import Reading
from readingdb.readingspec import ReadingSpec

class ReadingDB(abc.ABC):
    @abc.abstractmethod
    def set_as_predicting(route_id: str, user_id: str) -> None:
        """Updates the status of the specified route to predicting (indicating
        that a prediction process is under way).
        """
        raise NotImplementedError() 

    @abc.abstractmethod
    def all_route_readings(route_id: int, user_id: str) -> List[Dict[str, Any]]:
        """Returns all readings (e.g. gps readings, accelerometer readings, 
        camera image readings, prior predictions) associated with that route.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def begin_prediction(user_id: str, route_id: str) -> None:
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
    def save_route(reading_spec: ReadingSpec, user_id: str) -> Route:
        """Uploads all readings listed within reading_spec as a single route.
        Returns the ID of the newly created route.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def save_predictions(readings: List[Dict[str, Any]], route_id: int, user_id: str) -> None:
        """Saves the prediction readings to the given route and sets the status
        of that route to 'complete'.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def update_route_name(route_id: str, user_id: str, name: str) -> None:
        """Sets the name of the given route to the given name.
        """
        raise NotImplementedError()

    # -------------- Reading Methods -------------- 

    @abc.abstractmethod
    def all_route_readings(route_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Loads and returns all the readings for the given route
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def routes_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Loads and returns all the routes for the given user
        including sample readings only.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_route(route_id: str, user_id: str) -> Dict[str, Any]:
        """Loads and returns all the specified route
        """
        raise NotImplementedError()