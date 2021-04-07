import abc

class AbstractAuth(abc.ABC):
    @abc.abstractmethod
    def get_user(accessToken: str) -> bool:
        raise NotImplementedError("set_as_predicting is not implemented") 


class Auth():
    def __init__(self) -> None:
        pass