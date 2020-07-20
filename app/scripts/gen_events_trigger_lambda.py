import boto3
import os
from datetime import datetime
import pytz
import json


'''
client = boto3.client("s3")

bucket_name = 's3-dq-api-cdlz-msk-test'

paginator = client.get_paginator("list_objects_v2")
operation_parameters = {'Bucket': 's3-dq-api-cdlz-msk-test',
                        'Prefix': 'parsed'}

for page in paginator.paginate(**operation_parameters):
    print(page["Contents"])

'''

# 'LastModified': datetime.datetime(2020, 7, 2, 11, 26, 16, tzinfo=tzutc()), 'ETag': '"f119021d79f6e4e206ff9a8428b3c12d"', 'Size': 21540, 'StorageClass': 'STANDARD'}, {'Key': 'parsed/2020-07-02/12:23:59.764861894/PARSED_20200702_0830_9999.jsonl', 'LastModified': datetime.datetime(2020, 7, 2, 11, 39, 58, tzinfo=tzutc()), 'ETag': '"642bc3daca988bab17a2d0ca02f394cc"', 'Size': 108702, 'StorageClass': 'STANDARD'}, {'Key': 'parsed/2020-07-02/13:09:59.764861894/PARSED_20200702_0840_9899.jsonl',


def get_matching_s3_objects(bucket, prefix="", suffix=""):
    """
    Generate objects in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch objects whose key starts with
        this prefix (optional).
    :param suffix: Only fetch objects whose keys end with
        this suffix (optional).
    """
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    kwargs = {'Bucket': bucket}

    # We can pass the prefix directly to the S3 API.  If the user has passed
    # a tuple or list of prefixes, we go through them one by one.
    if isinstance(prefix, str):
        prefixes = (prefix, )
    else:
        prefixes = prefix

    for key_prefix in prefixes:
        kwargs["Prefix"] = key_prefix

        for page in paginator.paginate(**kwargs):
            try:
                contents = page["Contents"]
            except KeyError:
                break

            for obj in contents:
                key = obj["Key"]
                lmd =  obj["LastModified"]
                utc=pytz.UTC
                lower_cutoffdt = utc.localize(datetime.strptime('2020-07-09 10:55:31', '%Y-%m-%d %H:%M:%S'))
                upper_cutoffdt = utc.localize(datetime.strptime('2020-07-13 10:21:08', '%Y-%m-%d %H:%M:%S'))
                #print(lmd)
                if key.endswith(suffix) and lmd > lower_cutoffdt and lmd < upper_cutoffdt:
                    yield obj


def get_matching_s3_keys(bucket, prefix="", suffix=""):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    for obj in get_matching_s3_objects(bucket, prefix, suffix):
        #yield obj["Key"]
        yield obj


if __name__ == '__main__':
    triggerlambda = os.environ['LAMBDA_FUNC']
    bucket_name = os.environ['S3_BUCKET']
    CSV_S3_FILE = os.environ['CSV_S3_FILE']
    ATHENA_LOG = os.environ['ATHENA_LOG']
    CSV_S3_BUCKET = os.environ['CSV_S3_BUCKET']
    CSV_S3_FILE = os.environ['CSV_S3_FILE']

    LOG_FILE = "/APP/gen-s3event-notification.log"

    env='default'
    namespace = 'test'

    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"

    for reprocessobj in get_matching_s3_keys(bucket_name, "parsed", "jsonl"):
        payload3 = json.dumps({
            "Records":[{
                "s3":{
                    "bucket":{
                        "name":bucket_name
                        },
                    "object":{
                        "key": reprocessobj['Key'],
                        "size": reprocessobj['Size'],
                        "eTag": reprocessobj['ETag']

                        }
                            }
                        }]
                    })
        #print(reprocesskey)
        #print(payload3['Records'][0]['s3']['bucket']['name'])
        #print(payload3['Records'][0]['s3']['object']['key'])

        #Trigger lambda
        client = boto3.client('lambda')

        response = client.invoke(
        FunctionName=triggerlambda,
        InvocationType='Event',
        LogType='None',
        ClientContext='triggeringfromdocker',
        Payload=payload3)

        try:

            response = client.invoke(
            FunctionName=triggerlambda,
            InvocationType='Event',
            LogType='None',
            ClientContext='triggeringfromdocker',
            Payload=payload3)
            print("****")
            print(response)

            #Introduce Wait. Don't trigger the next event immediately

        except:
            print("Error Occured")
