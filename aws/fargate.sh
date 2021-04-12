aws ecs create-cluster --cluster-name unzipper-cluster

aws ecs register-task-definition --cli-input-json file:///home/lewington/code/readingsdb/aws/unzipper-td.json

# confirm that it's there
aws ecs list-task-definitions
