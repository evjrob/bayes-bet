# Getting Up and Running

In three separate terminals starting from this directory, run:

1. ```docker-compose up --build```

2. ```cd terraform && terraform apply --auto-approve```

3. ```aws --endpoint=http://localhost:4566 stepfunctions start-execution --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:bayesbet-main-local```