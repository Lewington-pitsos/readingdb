aws ecs create-cluster --cluster-name unzipper-cluster

# run this and it will create revisions automatically
aws ecs register-task-definition --cli-input-json file:///home/lewington/code/readingsdb/aws/unzipper-td.json 

# confirm that it's there
aws ecs list-task-definitions

# Build unzipper Dockerfile

docker build -f Dockerfile.unzipper -t unzipper:latest ./

aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com

# aws ecr create-repository --repository-name unzipper --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

docker tag unzipper:latest 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/unzipper:latest

docker push 950765595897.dkr.ecr.ap-southeast-2.amazonaws.com/unzipper:latest