# start the dynamo db
# go to the dynamo directory first
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

aws dynamodb list-tables --endpoint-url http://localhost:8000

python -m unittest discover

# docker lambda related

# local testing
docker build -t readingdb:latest ./ && docker run -p 9000:8080 readingdb:latest

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'


# deploying to aws ecr
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com

aws ecr create-repository --repository-name readingdb --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag readingdb:latest 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb:latest


docker push 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb:latest