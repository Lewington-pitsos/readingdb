import boto3
cognito = boto3.client('cognito-identity')
response = cognito.get_credentials_for_identity(IdentityId="id")