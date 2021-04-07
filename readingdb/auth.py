import abc
from typing import Any, Dict

import boto3
from boto3 import CognitoIdentityProvider

from readingdb.authresponse import AuthResponse



class AbstractAuth(abc.ABC):
    @abc.abstractmethod
    def get_user(accessToken: str) -> AuthResponse:
        raise NotImplementedError("set_as_predicting is not implemented") 

class Auth():
    def __init__(self, region_name="ap-southeast-2",) -> AuthResponse:
        self.cclient = boto3.client('cognito-idp', region_name=region_name)

    def get_user(self, accessToken: str) -> Dict[str, Any]:
        try:
            resp = self.cclient.get_user(AccessToken=accessToken)

            return AuthResponse(resp)

        except Exception as e:
            return AuthResponse({}, e)