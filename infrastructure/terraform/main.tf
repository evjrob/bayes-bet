terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "bayesbet-terraform-state"
    key    = "terraform.tfstate"
    region = "east-us-1"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-1"
}
