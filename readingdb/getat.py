import json
import os
from typing import Tuple

import boto3

CURRENT_DIR = os.path.dirname(__file__)
CREDENTIALS_FILE = CURRENT_DIR + '/test_data/fdsadmin.json'

USERNAME_KEY = 'username'
PASSWORD_KEY = 'password'
CLIENT_ID = 'client_id'
ACCESS_TOKEN_KEY = 'AccessToken'
AUTH_RESULT_KEY = 'AuthenticationResult'

def get_credentials(cred_file: str=CREDENTIALS_FILE) -> Tuple[str, str, str]:
    with open(cred_file, 'r') as f:
        creds = json.load(f)
    
    return creds[USERNAME_KEY], creds[PASSWORD_KEY], creds[CLIENT_ID]

def get_access_token(cred_file: str=CREDENTIALS_FILE) -> str:
    cclient = boto3.client('cognito-idp', region_name='ap-southeast-2')
    uname, pwd, cid = get_credentials(cred_file)

    auth_resp = cclient.initiate_auth(
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': uname,
            'PASSWORD': pwd
        },
        ClientId=cid
    )

    return auth_resp[AUTH_RESULT_KEY][ACCESS_TOKEN_KEY]