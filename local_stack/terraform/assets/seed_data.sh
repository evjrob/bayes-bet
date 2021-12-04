#!/bin/sh
# Arguments
# 1 - website s3 bucket
# 2 - dynamodb table name
web_s3_bucket=$1
dynamodb_table_name=$2
aws s3 cp assets/pred_dates.json s3://$web_s3_bucket/pred_dates.json
aws dynamodb put-item --table-name $dynamodb_table_name --item file://assets/db_item.json