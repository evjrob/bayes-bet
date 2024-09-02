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

# Create and initialize bayes-bet-model-state-local table in dynamodb
if aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb describe-table --table-name bayes-bet-model-state-local > /dev/null; then
    echo "Table bayes-bet-model-state-local already exists"
else 
    aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb create-table \
        --table-name bayes-bet-model-state-local \
        --attribute-definitions AttributeName=league,AttributeType=S AttributeName=prediction_date,AttributeType=S \
        --key-schema AttributeName=league,KeyType=HASH AttributeName=prediction_date,KeyType=RANGE \
        --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=5
fi

aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb put-item \
    --table-name bayes-bet-model-state-local \
    --item file://assets/model_state.json

echo "Inserted model state into bayes-bet-model-state-local table"

# Create and initialize bayes-bet-predictions-local table in dynamodb
if aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb describe-table --table-name  bayes-bet-predictions-local > /dev/null; then
    echo "Table bayes-bet-predictions-local already exists"
else
    aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb create-table \
        --table-name bayes-bet-predictions-local \
        --attribute-definitions AttributeName=league,AttributeType=S AttributeName=prediction_date,AttributeType=S \
        --key-schema AttributeName=league,KeyType=HASH AttributeName=prediction_date,KeyType=RANGE \
        --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=5
fi

aws --profile local --endpoint-url http://127.0.0.1:8000 dynamodb put-item \
    --table-name bayes-bet-predictions-local \
    --item file://assets/prediction.json

echo "Inserted prediction into bayes-bet-predictions-local table"