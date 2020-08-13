# dq-kube-gen-s3events-triggerlambda
Repo to Generate S3 notification events for Files already in S3 and Trigger a Lambda that processes the events.

[![Docker Repository on Quay](https://quay.io/repository/ukhomeofficedigital/dq-nats-sftp-python/status "Docker Repository on Quay")](https://quay.io/repository/ukhomeofficedigital/dq-nats-sftp-python)

Docker container that can generate S3 notifications events based on a range of last modified timestamps and Trigger a lambda passing that event as an input to the lambda function.
Tasks include:
- Reading  Files in an S3 bucket based on a Prefix and suffix.
- Filter files based on a time range.
- Generate S3 notification events for these files(s3 objects)
- Trigger a lambda function by passing the event data as an input.

## Dependencies

- Docker
- Python3.7
- Drone
- AWS CLI
- AWS Keys with GET access to S3 and Invoke access on AWS Lambda.
- Kubernetes

## Example usage
### Running in Docker

Build container
```
docker build -t gens3events app/
```

Run container
```
docker run
-e LAMBDA_FUNC="arn:aws:lambda:eu-west-2:797728447925:function:api-kafka-input-test-trigger"
-e AWS_ACCESS_KEY_ID=ABCDEFGHIJLMNOP
-e AWS_SECRET_ACCESS_KEY=aBcDe1234+fghijklm01
-e AWS_DEFAULT_REGION=eu-west-2
-e S3_BUCKET="s3-dq-api-cdlz-msk-test"
-e LAST_MOD_DTTIME_START="2020-07-09 10:55:31"  
-e LAST_MOD_DTTIME_END "2020-07-09 13:55:31"
-e S3_PREFIX "parsed"
-e S3_SUFFIX "jsonl"
-e WAIT_SEC "60"
gens3events
```

## Useful commands
Run a one time instance of the job:-
```
kubectl create job dq-athena-partition-maintenance --from=cronjob/dq-athena-partition-maintenance
```

## Variables
See below a list of variables that are required, and also some that are optional

|  Variable name           |    example    | description                                                                                     | required |
| ------------------------ | ------------- | ------------------------------------------------------------------------------------------------| -------- |
|    LAMBDA_FUNC            | arn:aws:lambda:eu-west-2:797728447925:function:api-kafka-input-test-trigger | Lambda Function that should be triggered |    Y     |
|    WAIT_SEC            | 60 | Seconds to wait before generating the next notifications and triggering the next lambda                                                                   |    Y     |
|    S3_BUCKET         | s3-dq-api-cdlz-msk-test | S3 bucket that contains files that need to be process file                                                            |    Y     |
|    LAST_MOD_DTTIME_START         | 2020-07-09 10:55:31 | Starting range of Last Modified date time for files that need reprocessing                                                             |    Y     |
|    LAST_MOD_DTTIME_END           | 2020-07-09 10:55:31      | End of the range of Last Modified date time for files that need reprocessing        |    Y     |
|    AWS_ACCESS_KEY_ID     | ABCD          | AWS access key ID                                                                               |    Y     |
|    AWS_SECRET_ACCESS_KEY | ABCD1234      | AWS secret access key                                                                           |    Y     |
|    AWS_DEFAULT_REGION    | eu-west-2     | AWS default region               |    Y     |    



## Drone secrets

Environmental variables are set in Drone based on secrets listed in the *.drone.yml* file and they are passed to Kubernetes as required.

## Running the build

This repo will generate events for environments independently. If you want to run Events for notprod, make a branch with the prefix notprod/. If you want to run Events for prod, make a branch with the prefix prod/. Once you make a branch the change will be LAST_MOD_DTTIME_START and LAST_MOD_DTTIME_END to that which you specify. Commit your branch and push, this will trigger the build in the respective environment. 
