#!/bin/sh

# Get ECR URL components
build_path=$1
ecr_full_url=$2
ecr_image_tag=$3
ecr_image_name=${ecr_full_url#*/}
ecr_base_url=${ecr_full_url%"$ecr_image_name"}
echo "ECR FULL URL: $ecr_full_url"
echo "ECR BASE URL: $ecr_base_url"
echo "ECR IMAGE NAME: $ecr_image_name"
echo "ECR IMAGE TAG: $ecr_image_tag"

# Build the image
docker build -t $ecr_image_name -f $build_path/Dockerfile $build_path

# Push it to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ecr_base_url
docker tag $ecr_image_name:latest $ecr_full_url:$ecr_image_tag
docker push $ecr_full_url:$ecr_image_tag
