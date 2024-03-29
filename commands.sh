# start the dynamo db
# go to the dynamo directory first
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

aws dynamodb list-tables --endpoint-url http://localhost:8000

python -W ignore:unclosed:ResourceWarning -m unittest -c

# aws authentication

aws ecr get-login --no-include-email --region ap-southeast-2 | sh


# docker lambda related


# local testing
docker build -f Dockerfile.readingdb -t readingdb2 --build-arg CRED="$(cat ../../aws/credentials)" ./

docker run -p 9000:8080 readingdb2:latest

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"RouteID": "1617260062.1409826-EPILIQLB84EE3CH"}'
# {"Status": "Error", "Body": "Invalid Event Syntax"}


curl -XPOST "https://l6r454hy23.execute-api.ap-southeast-2.amazonaws.com/prod/backend" -d '{"Type": "GetRoute", "RouteID": "1617880492.8395514-C88AL4ZBB464RLR", "AccessToken": "eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjFmMDNjZTlkLTMxOGEtNDQ1My04MDZhLTcyNTllZDQ3YzdmNyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTc5Mzk3NjIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTc5NDMzNjIsImlhdCI6MTYxNzkzOTc2MiwianRpIjoiYjE3ZTI3NzctOWQ3Yy00ZDIyLTg5ODItZWUwMWY5ZmRmMDc2IiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.izRZn5As6HIuXHQ47OsbiZTCk3mCU7qSePbp_YiXDw-3tS8Lr4QrH1cABvIIL-WwpNfdiLSFAS9GU0j-putADrROReKTwe21rmo0pAe34j--f0tMOMSoaNWLLHJdvEi3-RJ4pvDGk6tY5KXMrH6gPgWALc-ccNBh0iR47DsZI0X_9z7bPwWpE_P9hLfrSUlZvfFnxlmiQMtB8Oj1IvLafYmZIkBdi369_e6Gt0PqM2Ps56t-1bMAdV_xo9Oa-H87fHOQftgThXG71mKeiKFpsjUrNzQCRIbUht7BuprZGNE9li5bs76EcPPV3m6dYl34jPGXXmdXnB8pj22Z8Yxh0w"}'
# {"Status": "Error", "Body": "Unauthenticated request, unrecognized Access Token...

# re-tag and push
docker tag readingdb2:latest 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb2:latest
docker push 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb2:latest


pippush 'commit name' hotfix master

# creating and deleting dynamodb tables

aws dynamodb delete-table --table-name Readings2
aws dynamodb create-table \
    --table-name Readings2\
    --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
    --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

aws dynamodb delete-table --table-name Org
aws dynamodb create-table \
    --table-name Org\
    --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
    --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

