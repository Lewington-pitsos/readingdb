from copy import Error
from typing import Dict, Any


class AuthResponse():
    AUTH_RESULT_KEY = "AuthenticationResult"
    ACCESS_TOKEN_KEY = "AccessToken"
    ID_TOKEN_KEY = "IdToken"
    USER_ATTR_KEY = "UserAttributes"
    ATTR_NAME_KEY = "Name"
    ATTR_VALUE_KEY = "Value"
    USERNAME_KEY = "Username"
    USER_SUB = 'sub'

    def __init__(self, response_data: Dict[str, Any], error: Error =None) -> None:
        self.response_data: Dict[str, Any] = response_data
        self.error: Error = error
        self.username: str = response_data[self.USERNAME_KEY] if self.USERNAME_KEY in response_data else None
            
        for attr in self.response_data[self.USER_ATTR_KEY]:
            if attr[self.ATTR_NAME_KEY] == self.USER_SUB:
                self.usr_sub: str = attr[self.ATTR_VALUE_KEY]
                break
        else:
            self.user_sub = None
    
    def contains_error(self) -> bool:
        return self.error is not None

    def is_authenticated(self) -> bool:
        return not self.contains_error and self.username is not None and self.user_sub is not None