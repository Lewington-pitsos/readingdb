# start the dynamo db
# go to the dynamo directory first
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

aws dynamodb list-tables --endpoint-url http://localhost:8000

python -m unittest discover

# docker lambda related

# local testing
docker build -t readingdb:latest ./ && docker run -p 9000:8080 readingdb:latest

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"RouteID": "1617260062.1409826-EPILIQLB84EE3CH"}'

curl -XPOST "https://l6r454hy23.execute-api.ap-southeast-2.amazonaws.com/prod/backend" -d '{"Type": "GetRoute", "RouteID": "1617880492.8395514-C88AL4ZBB464RLR", "AccessToken": "eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6IjFmMDNjZTlkLTMxOGEtNDQ1My04MDZhLTcyNTllZDQ3YzdmNyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTc5Mzk3NjIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTc5NDMzNjIsImlhdCI6MTYxNzkzOTc2MiwianRpIjoiYjE3ZTI3NzctOWQ3Yy00ZDIyLTg5ODItZWUwMWY5ZmRmMDc2IiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.izRZn5As6HIuXHQ47OsbiZTCk3mCU7qSePbp_YiXDw-3tS8Lr4QrH1cABvIIL-WwpNfdiLSFAS9GU0j-putADrROReKTwe21rmo0pAe34j--f0tMOMSoaNWLLHJdvEi3-RJ4pvDGk6tY5KXMrH6gPgWALc-ccNBh0iR47DsZI0X_9z7bPwWpE_P9hLfrSUlZvfFnxlmiQMtB8Oj1IvLafYmZIkBdi369_e6Gt0PqM2Ps56t-1bMAdV_xo9Oa-H87fHOQftgThXG71mKeiKFpsjUrNzQCRIbUht7BuprZGNE9li5bs76EcPPV3m6dYl34jPGXXmdXnB8pj22Z8Yxh0w"}'


pippush 'commit name' hotfix master