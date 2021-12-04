provider "aws" {
  region  = "us-east-1"
  profile = "terraform"
  # skip_credentials_validation = true
  # skip_metadata_api_check     = true
  # skip_requesting_account_id  = true
  # s3_force_path_style         = true

  # endpoints {
  #   iam           = "http://localhost:4566"
  #   lambda        = "http://localhost:4566"
  #   ecr           = "http://localhost:4566"
  #   dynamodb      = "http://localhost:4566"
  #   s3            = "http://localhost:4566"
  #   stepfunctions = "http://localhost:4566"
  # }
}

