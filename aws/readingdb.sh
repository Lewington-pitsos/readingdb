# deploying to aws ecr
pipenv lock -r > requirements.txt

docker build -f Dockerfile.readingdb -t readingdb:latest ./

aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com

# aws ecr create-repository --repository-name readingdb --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag readingdb:latest 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb:latest

docker push 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/readingdb:latest

# then create a new lambda with the "from image" option
# ensure to give the lambda proper permissions
# to update the imagem rebuild, retag, push and then select the newer image from the lambda console