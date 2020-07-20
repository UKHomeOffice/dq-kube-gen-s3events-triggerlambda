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



## Structure

- **app/**
  - *Dockerfile*: describe what is installed in the container and the Python file that needs to run
  - *docker-entrypoint.sh*: bash scripts running at container startup
  - *packages.txt*: Python custom Modules
  - *ecosystem.config.js*: declare variables used by PM2 at runtime
  - **bin/**
    - *DQ_NATS_file_ingest*: Python script used with PM2 to declare imported files to PM2 at runtime
  - **scripts/**
    - *__init__.py*: declare Python module import
    - *DQ_NATS_file_ingest.py*: Python3.7 script running within the container
    - *settings.py*: declare variables passed to the *DQ_NATS_file_ingest.py* file at runtime
  - **test/**
    - *start.sh*: Download, build and run Docker containers
    - *stop.sh*: Stop and remove **all** Docker containers
    - *eicar.com*: File containing a test virus string
- **kube/**
  - *deployment.yml*: describe a Kubernetes POD deployment
  - *secret.yml*: list the Drone secrets passed to the containers during deployment  
- *.drone.yml*: CI deployment configuration
- *LICENSE*: MIT license file
- *README.md*: readme file

## Kubernetes POD connectivity

The POD consists of 3 (three) Docker containers responsible for handling data.

| Container Name | Function | Language | Exposed port | Managed by |
| :--- | :---: | :---: | ---: | --- |
| dq-nats-data-ingest | Data pipeline app| Python3.7 | N/A | DQ Devops |
| clamav-api | API for virus checks | N/A | 8080 |ACP |
| clamav | Database for virus checks | N/A | 3310 |ACP |


## Drone secrets

Environmental variables are set in Drone based on secrets listed in the *.drone.yml* file and they are passed to Kubernetes as required.

## Local Test suite

Testing the NATS Python script can be done by having access to AWS S3 and Docker.
The full stack comprises of 4 Docker containers within the same network linked to each other so DNS name resolution works between the components.

The containers can be started and a couple of test files generated using the *start.sh* script located in **app/test**.
The script will require the following variables passed in at runtime.

|Name|Value|Required|Description|
| --- |:---:| :---:| --- |
| pubkey | /local/path/id_rsa.pub | True | Public SSH key used by the SFTP server|
| privkey | /local/path/id_rsa | True | Private SSH used to connect to the SFTP server|
| mountpoint|  /local/path/mountpoint-dir | True | SFTP source directory|
| bucketname | s3-bucket-name | True | S3 bucket name |
| keyprefix | prefix | True | S3 folder name |
| awskeyid | ABCD | True | AWS access key ID |
| awssecret | abcdb1234 | True | AWS Secret access key |
| webhook | https://hooks.slack.com/services/ABCDE12345 | True | Slack Webhook URL |

- Components:
  - SFTP container
  - ClamAV container
  - ClamAV REST API container
  - NATS Python container

After the script has completed - for the first time it will take around 5 minutes to download all images - there should be a test files in the S3 bucket:

```
[-PRMD=EG-ADMD=ICAO-C=XX-;MTA-EGGG-1-MTCU_YYYYYYYYYYYYYYYY].json
```
The other test file contains a test virus string and it will be located under:

```
/NATS/quarantine/nats/[-PRMD=EG-ADMD=ICAO-C=XX-;MTA-EGGG-1-MTCU_YYYYYYYYYYYYYYYY].json
```

- Launching the test suite

NOTE: navigate to **app/test** first.

```
sh start.sh
```

- When done with testing stop the test suite

NOTE: **all** running containers will be stopped

```
sh stop.sh
```

If files have not uploaded into s3, check the error logs by exec'ing into the nats python container and checking error.log file. The path of this file is shown by entering the command:

```
pm2 show 0
```

If the logs read that the private key found is not a valid format, then cat your id_rsa file to check if the the format is OPENSSH. If you generated your keys specifying RSA type and you still have OPENSSH, then use this command to generate the keys again:

```
ssh-keygen -t rsa -b 4096 -C "email@email.com" -m PEM -f /Path-to-file/id_rsa
```
Some versions of macs auto-format ssh-keys to OPENSSH even when RSA is specified and need to be converted using this command.
