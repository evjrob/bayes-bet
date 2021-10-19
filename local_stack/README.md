# Getting Up and Running

In three separate terminals starting from this directory, run:

1. ```docker-compose up --build```

2. ```cd terraform && terraform apply --auto-approve```

3. ```aws --endpoint=http://localhost:4566 dynamodb put-item --table-name bayesbet-main-local --item file://assets/db_item.json```

    ```aws --endpoint=http://localhost:4566 s3 cp assets/pred_dates.json s3://bayesbet-web-local/pred_dates.json```

    ```aws --endpoint=http://localhost:4566 stepfunctions start-execution --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:bayesbet-main-local --input file://assets/nhl_sfn_input.json```