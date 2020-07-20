import boto3
import os
from datetime import datetime
import pytz
import json


def get_matching_s3_objects(bucket, prefix="", suffix="",stdt, endt):
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
                lower_cutoffdt = utc.localize(datetime.strptime(stdt, '%Y-%m-%d %H:%M:%S'))
                upper_cutoffdt = utc.localize(datetime.strptime(endt, '%Y-%m-%d %H:%M:%S'))
                if key.endswith(suffix) and lmd > lower_cutoffdt and lmd < upper_cutoffdt:
                    yield obj


def get_matching_s3_keys(bucket, prefix="", suffix="", stdt, endt):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    for obj in get_matching_s3_objects(bucket, prefix, suffix, stdt, endt):
        yield obj


if __name__ == '__main__':
    triggerlambda = os.environ['LAMBDA_FUNC']
    bucket_name = os.environ['S3_BUCKET']
    s3_lmdt_start = os.environ['LAST_MOD_DTTIME_START']
    s3_lmdt_end = os.environ['LAST_MOD_DTTIME_END']
    s3_prefix = os.environ['S3_PREFIX']
    s3_suffix = os.environ['S3_SUFFIX']
    CSV_S3_BUCKET = os.environ['CSV_S3_BUCKET']
    CSV_S3_FILE = os.environ['CSV_S3_FILE']

    LOG_FILE = "/APP/gen-s3event-notification.log"

    env='default'
    namespace = 'test'
    #os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
    #'2020-07-09 10:55:31'

    for reprocessobj in get_matching_s3_keys(bucket_name, s3_prefix, s3_suffix, s3_lmdt_start, s3_lmdt_end):
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
