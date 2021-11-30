# Build the image
docker build -t bayesbet-model -f ../../model/Dockerfile.lambda ../../model

# Push it to ECR
aws --endpoint=http://localhost:4566 ecr get-login-password --region us-east-1
docker login --username AWS --password-stdin localhost:4510
docker tag bayesbet-model:latest localhost:4510/bayesbet-model-local:latest
docker push localhost:4510/bayesbet-model-local:latest