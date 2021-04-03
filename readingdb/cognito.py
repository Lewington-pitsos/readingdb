import boto3

class CognitoAuth():
    AUTH_RESULT_KEY = "AuthenticationResult"
    ACCESS_TOKEN_KEY = "AccessToken"
    ID_TOKEN_KEY = "IdToken"
    USER_ATTR_KEY = "UserAttributes"
    ATTR_NAME_KEY = "Name"
    ATTR_VALUE_KEY = "Value"
    USERNAME_KEY = "Username"
    USER_SUB = 'sub'

    def __init__(
        self, 
        auth, 
        region_name="ap-southeast-2", 
    ):
        cclient = boto3.client('cognito-idp', region_name=region_name)

        auth_resp = cclient.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': auth.username,
                'PASSWORD': auth.password
            },
            ClientId=auth.clientid
        )

        if not self.ACCESS_TOKEN_KEY in auth_resp[self.AUTH_RESULT_KEY]:
            raise ValueError(f"Unexpected cognito authentication response: {auth_resp}")

        if not self.ID_TOKEN_KEY in auth_resp[self.AUTH_RESULT_KEY]:
            raise ValueError(f"Unexpected cognito authentication response: {auth_resp}")

        self.access_token = auth_resp[self.AUTH_RESULT_KEY][self.ACCESS_TOKEN_KEY]
        self.id_token = auth_resp[self.AUTH_RESULT_KEY][self.ID_TOKEN_KEY]
        user_resp = cclient.get_user(AccessToken=auth_resp[self.AUTH_RESULT_KEY][self.ACCESS_TOKEN_KEY])

        self.uname = user_resp[self.USERNAME_KEY]

        for attr in user_resp[self.USER_ATTR_KEY]:
            if attr[self.ATTR_NAME_KEY] == self.USER_SUB:
                self.usr_sub = attr[self.ATTR_VALUE_KEY]
                break
        else:
            raise ValueError(f"Could not identify a user sub value in user response: {user_resp}")

        iamClient = boto3.client("iam")