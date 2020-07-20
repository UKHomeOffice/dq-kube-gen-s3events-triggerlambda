import boto3
import os
from datetime import datetime
import pytz
import json

import os
import sys
import time
import random
#import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from dateutil.relativedelta import relativedelta
from botocore.config import Config
from botocore.exceptions import ClientError
import urllib.request


LOG_FILE = "/APP/gen-s3event-notification.log"

"""
Setup Logging
"""
LOGFORMAT = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'
FORM = logging.Formatter(LOGFORMAT)
logging.basicConfig(
    format=LOGFORMAT,
    level=logging.INFO
)
LOGGER = logging.getLogger()
if LOGGER.hasHandlers():
    LOGGER.handlers.clear()
LOGHANDLER = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=7)
LOGHANDLER.suffix = "%Y-%m-%d"
LOGHANDLER.setFormatter(FORM)
LOGGER.addHandler(LOGHANDLER)
CONSOLEHANDLER = logging.StreamHandler()
CONSOLEHANDLER.setFormatter(FORM)
LOGGER.addHandler(CONSOLEHANDLER)
LOGGER.info("Starting")

LOG_GROUP_NAME = None
LOG_STREAM_NAME = None


CONFIG = Config(
    retries=dict(
        max_attempts=4
    )
)

def send_message_to_slack(text):
    """
    Formats the text provides and posts to a specific Slack web app's URL
    Args:
        text : the message to be displayed on the Slack channel
    Returns:
        Slack API repsonse
    """


    try:
        post = {
            "text": ":fire: :sad_parrot: An error has occured in the *Athena Partition Maintenace* pod :sad_parrot: :fire:",
            "attachments": [
                {
                    "text": "{0}".format(text),
                    "color": "#B22222",
                    "attachment_type": "default",
                    "fields": [
                        {
                            "title": "Priority",
                            "value": "High",
                            "short": "false"
                        }
                    ],
                    "footer": "Kubernetes API",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
                }
            ]
            }

        ssm_param_name = 'slack_notification_webhook'
        ssm = boto3.client('ssm', config=CONFIG)
        try:
            response = ssm.get_parameter(Name=ssm_param_name, WithDecryption=True)
        except ClientError as err:
            if err.response['Error']['Code'] == 'ParameterNotFound':
                LOGGER.info('Slack SSM parameter %s not found. No notification sent', ssm_param_name)
                return
            else:
                LOGGER.error("Unexpected error when attempting to get Slack webhook URL: %s", err)
                return
        if 'Value' in response['Parameter']:
            url = response['Parameter']['Value']

            json_data = json.dumps(post)
            req = urllib.request.Request(
                url,
                data=json_data.encode('ascii'),
                headers={'Content-Type': 'application/json'})
            LOGGER.info('Sending notification to Slack')
            response = urllib.request.urlopen(req)

        else:
            LOGGER.info('Value for Slack SSM parameter %s not found. No notification sent', ssm_param_name)
            return

    except Exception as err:
        LOGGER.error(
            'The following error has occurred on line: %s',
            sys.exc_info()[2].tb_lineno)
        LOGGER.error(str(err))

def get_matching_s3_objects(bucket,stdt, endt, prefix="", suffix=""):
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
                LOGGER.error(str(KeyError))
                break

            for obj in contents:
                key = obj["Key"]
                lmd =  obj["LastModified"]
                utc=pytz.UTC
                lower_cutoffdt = utc.localize(datetime.strptime(stdt, '%Y-%m-%d %H:%M:%S'))
                upper_cutoffdt = utc.localize(datetime.strptime(endt, '%Y-%m-%d %H:%M:%S'))
                if key.endswith(suffix) and lmd > lower_cutoffdt and lmd < upper_cutoffdt:
                    yield obj


def get_matching_s3_keys(bucket, stdt, endt, prefix="", suffix=""):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    for obj in get_matching_s3_objects(bucket, stdt, endt, prefix, suffix):
        yield obj


if __name__ == '__main__':
    triggerlambda = os.environ['LAMBDA_FUNC']
    bucket_name = os.environ['S3_BUCKET']
    s3_lmdt_start = os.environ['LAST_MOD_DTTIME_START']
    s3_lmdt_end = os.environ['LAST_MOD_DTTIME_END']
    s3_prefix = os.environ['S3_PREFIX']
    s3_suffix = os.environ['S3_SUFFIX']
    wait_sec = os.environ['WAIT_SEC']


    #LOG_FILE = "/APP/gen-s3event-notification.log"
    #os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
    #'2020-07-09 10:55:31'

    for reprocessobj in get_matching_s3_keys(bucket_name, s3_lmdt_start, s3_lmdt_end, s3_prefix, s3_suffix):
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

        except Exception as err:
            LOGGER.error(str(err))
            send_message_to_slack(err)
            print("Error Occured")
