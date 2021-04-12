# Key Learnings

## It's basically just EC2

Fargate as a service is a lot more similar to an ECS instance than a lambda. In particular:

- you must specify some parameters about the hardware you will be using (memory, compute, etc)
- you need to do a bunch of networking stuff so it can access the internet
- basically your code is going to run inside a server, and you need to tell it how to reach the outside world

When you use fargate you'll be creating a "task" which is general enough that it could be run on ec2 or fargate.

## Subnets as "slot-holders"

A subnet can be thought of as a set number of "slots" where things like ec2 instances can be placed. Things inside the same subnet can communicate with each other easily. Subnets can be public (internet access) and private (no internet access)

## Key Terms

**Task**: Some computation that needs running.
**Cluster**: The computational resources that tasks are run on.
**TaskDefinition**: some JSON that states the parameters of a task, e.g.:
- what docker image it runs on
- the networking required
- how logs will be logged 
- which IAM role to execute task with, etc

## Role Passing

Executing fargate tasks requires an IAM role to be assigned to the task. This is highly non-standard, so in order to get it to work you will need to:

1. find the role that the task ITSELF will be using (hopefully specified in the TaskDefinition)
2. ensure that this role has a "trust relationship" such that "ecs-tasks.amazonaws.com" is among the "trusted entities. Looks something like:

    {
        "Version": "2008-10-17",
        "Statement": [
            {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                    "ec2.amazonaws.com",
                    "ecs-tasks.amazonaws.com"
                    ]
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

3. find the IAM USER (not ROLE, USER) that you are using to ask aws to start running the task. E.g. if you are spining up the task in boto3, it's whatever IAM your boto3 is running under.
4. ensure that this user has the permission to "pass" the first role around. You do this just by attaching a policy (see below) to that user, can be via a group or a role or whatever

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:GetRole",
                    "iam:PassRole"
                ],
                "Resource": "arn:aws:iam::950765595897:role/ecsInstanceRole"
            }
        ]
    }

Until this is correclty configured you will get errors when you try to run the task and it will make you want to cry.