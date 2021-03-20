# start the dynamo db
# go to the dynamo directory first
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedD


aws dynamodb list-tables --endpoint-url http://localhost:8000