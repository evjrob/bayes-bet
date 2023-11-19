#!/bin/sh
# Arguments
# 1 - ECR URL

# Get ECR URL components
ecr_full_url=$1
ecr_image_tag=$2
ecr_image_name=${ecr_full_url#*/}
ecr_base_url=${ecr_full_url%"$ecr_image_name"}
echo "ECR FULL URL: $ecr_full_url"
echo "ECR BASE URL: $ecr_base_url"
echo "ECR IMAGE NAME: $ecr_image_name"
echo "ECR IMAGE TAG: $ecr_image_tag"

# Build the image
docker build -t $ecr_image_name -f ../../model/Dockerfile ../../model

# Push it to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ecr_base_url
docker tag $ecr_image_name:$ecr_image_tag $ecr_full_url:$ecr_image_tag
docker push $ecr_full_url:$ecr_image_tag
