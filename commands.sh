# start the dynamo db
# go to the dynamo directory first
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

aws dynamodb list-tables --endpoint-url http://localhost:8000

python -m unittest discover

# docker lambda related

# local testing
docker build -t readingdb:latest ./ && docker run -p 9000:8080 readingdb:latest

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"RouteID": "1617260062.1409826-EPILIQLB84EE3CH"}'

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"Type": "GetRoute", "RouteID": "1617839705.6470242-61ZDT8KWSA41RQV", "AccessToken": "eyJraWQiOiI0QXl3TjdidExEWm1RWFBEdVpxZ3JRTVk2MkVheXc0ZlN6eXBNcFI2bDh3PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI5OWJmNDUxOS04NWQ5LTQ3MjYtOTQ3MS00YzkxYTc2Nzc5MjUiLCJjb2duaXRvOmdyb3VwcyI6WyJhZG1pbiJdLCJldmVudF9pZCI6ImI3ZWM4ZWY0LWJlM2MtNDc2OS05NGMxLTEzMzJlYTg4YWNlNSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE2MTc4NDA3NzgsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC5hcC1zb3V0aGVhc3QtMi5hbWF6b25hd3MuY29tXC9hcC1zb3V0aGVhc3QtMl9jdHBnbTBLdzQiLCJleHAiOjE2MTc4NDQzNzgsImlhdCI6MTYxNzg0MDc3OSwianRpIjoiMjFkM2EwNTAtYWNmZi00MGMzLWFhZjMtMTI4YjFmZjBkYTNlIiwiY2xpZW50X2lkIjoiNHVxaHFzb29lNDNlYnRxMG9idm4wbG03dWkiLCJ1c2VybmFtZSI6ImZkc2FkbWluIn0.ZnO3YOxIWX_zxj3xHc2qIMxAtv5IPpd2d7G04__sjQqlKYX8mfSptsLUE5JJvhhnS9waZt6hnueLg4ZmNf5wEeOGhQptmQMHLdUNCkO264vkh5JCwjH_YRiL2DFjSe9fS6MyEVkOtFm8B3_uPgfl0uczsJIeK1WlZYYVh3sNPzESHcbCkOKLnRefET9Ab3LxXXC02qxuMNU7j3pcIzny7fkSKnuglGkb9PcyEy2rQEU5LqG9zx-jwdXqTGY2f1xYTBLe8eNgrnVwyQETBmN_mWgvgtfB8_Uur8xEIrMnqfDt-Hy4sLZmucZMZkOF97f4BSKN3PRl3FGVCXxhYThaww"}'

# deploying to aws ecr
docker build -t readingdb:latest ./

aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com

aws ecr create-repository --repository-name readingdb --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag readingdb:latest 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb:latest


docker push 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb:latest

# then create a new lambda with the "from image" option
# ensure to give the lambda proper permissions

# to update the imagem rebuild, retag, push and then select the newer image from the lambda console