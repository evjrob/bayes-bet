MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123

# Create and initialize bayes-bet-pipeline-local bucket in minio
if aws --profile local --endpoint-url http://127.0.0.1:9000 s3api head-bucket --bucket bayes-bet-pipeline-local; then
    echo "Bucket bayes-bet-pipeline-local already exists"
else
    aws --profile local --endpoint-url http://127.0.0.1:9000 s3 mb s3://bayes-bet-pipeline-local
fi

# Create and initialize bayes-bet-web-local bucket in minio
if aws --profile local --endpoint-url http://127.0.0.1:9000 s3api head-bucket --bucket bayes-bet-web-local; then
    echo "Bucket bayes-bet-web-local already exists"
else
    aws --profile local --endpoint-url http://127.0.0.1:9000 s3 mb s3://bayes-bet-web-local
fi

aws --profile local --endpoint-url http://127.0.0.1:9000 s3 cp ../front_end/app/bayesbet/static/bayesbet.css s3://bayes-bet-web-local/bayesbet.css
aws --profile local --endpoint-url http://127.0.0.1:9000 s3 cp ../front_end/app/bayesbet/static/favicon.ico s3://bayes-bet-web-local/favicon.ico
aws --profile local --endpoint-url http://127.0.0.1:9000 s3 cp ../front_end/app/plots/static s3://bayes-bet-web-local --recursive
aws --profile local --endpoint-url http://127.0.0.1:9000 s3 cp assets/pred_dates.json s3://bayes-bet-web-local/pred_dates.json
mc alias set minio http://127.0.0.1:9000/
mc anonymous set download minio/bayes-bet-web-local

# Create and initialize bayes-bet-model-state-local table in dynamodb
if aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb describe-table --table-name bayes-bet-model-state-local > /dev/null; then
    echo "Table bayes-bet-model-state-local already exists, deleting!"
    aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb delete-table --table-name bayes-bet-model-state-local
fi

aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb create-table \
    --table-name bayes-bet-model-state-local \
    --attribute-definitions AttributeName=league,AttributeType=S AttributeName=prediction_date,AttributeType=S \
    --key-schema AttributeName=league,KeyType=HASH AttributeName=prediction_date,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=5 > /dev/null;

aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb put-item \
    --table-name bayes-bet-model-state-local \
    --item file://assets/model_state.json > /dev/null;

echo "Inserted model state into bayes-bet-model-state-local table"

# Create and initialize bayes-bet-predictions-local table in dynamodb
if aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb describe-table --table-name  bayes-bet-predictions-local > /dev/null; then
    echo "Table bayes-bet-predictions-local already exists, deleting!"
    aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb delete-table --table-name bayes-bet-predictions-local
fi

aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb create-table \
    --table-name bayes-bet-predictions-local \
    --attribute-definitions AttributeName=league,AttributeType=S AttributeName=prediction_date,AttributeType=S \
    --key-schema AttributeName=league,KeyType=HASH AttributeName=prediction_date,KeyType=RANGE \
    --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=5 > /dev/null;

aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb put-item \
    --table-name bayes-bet-predictions-local \
    --item file://assets/prediction.json > /dev/null;

echo "Inserted prediction into bayes-bet-predictions-local table"

# Create stepfunction workflow
cp ../infrastructure/terraform/assets/bayesbet_nhl_sfn.asl.json assets/bayesbet_nhl_sfn.asl.json
sed -i".backup" \
    -e "s/\${task_lambda}/arn:aws:lambda:us-east-1:000000000000:function:function:$LATEST/" \
    -e "s/\${project}/bayes-bet/" \
    -e "s/\${environment}/local/" \
    -e "s/\${pipeline_bucket}/bayes-bet-pipeline-local/" \
    -e "s/\${web_bucket}/bayes-bet-web-local/" \
    -e "s/\${max_concurrency}/1/" \
    -e "s/\${account_id}/123456789012/" \
    assets/bayesbet_nhl_sfn.asl.json
if aws --profile local --endpoint-url http://127.0.0.1:8083 stepfunctions describe-state-machine --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:bayes-bet-nhl-main-local > /dev/null; then
    echo "Step function bayes-bet-nhl-main-local already exists, updating!"
    aws --profile local \
        --endpoint-url http://127.0.0.1:8083 \
        stepfunctions update-state-machine \
        --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:bayes-bet-nhl-main-local \
        --role-arn "arn:aws:iam::000000000000:role/dummy"
else
    echo "Creating step function bayes-bet-nhl-main-local!"
    aws --profile local \
        --endpoint-url http://127.0.0.1:8083 \
        stepfunctions create-state-machine \
        --name bayes-bet-nhl-main-local \
        --definition file://assets/bayesbet_nhl_sfn.asl.json \
        --role-arn "arn:aws:iam::000000000000:role/dummy"
fi

# aws --profile=local --endpoint-url http://127.0.0.1:8083 stepfunctions start-execution --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:bayes-bet-nhl-main-local