import boto3
import os

REGION = 'us-east-1'
SOURCE_AWS_PROFILE = 'bayes-bet-admin'
SOURCE_TABLE_NAME = 'bayes-bet-main-prod'
TARGET_AWS_PROFILE = 'bayes-bet-staging'
TARGET_TABLE_NAME = 'bayes-bet-main-staging'

source_session = boto3.Session(profile_name=SOURCE_AWS_PROFILE)
dynamo_source_client = source_session.client('dynamodb', region_name=REGION)

target_session = boto3.Session(profile_name=TARGET_AWS_PROFILE)
dynamo_target_client = target_session.client('dynamodb', region_name=REGION)

dynamo_paginator = dynamo_source_client.get_paginator('scan')

dynamo_response = dynamo_paginator.paginate(
    TableName=SOURCE_TABLE_NAME,
    Select='ALL_ATTRIBUTES',
    ReturnConsumedCapacity='NONE',
    ConsistentRead=True
)

for page in dynamo_response:
    for item in page['Items']:
        dynamo_target_client.put_item(
            TableName=TARGET_TABLE_NAME,
            Item=item
        )
