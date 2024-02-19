resource "aws_s3_bucket" "bayesbet_web_bucket" {
  bucket = "${var.project}-web-${var.env}"
}

resource "aws_s3_bucket_ownership_controls" "bayesbet_web_bucket" {
  bucket = aws_s3_bucket.bayesbet_web_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "bayesbet_web_bucket" {
  bucket = aws_s3_bucket.bayesbet_web_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "bayesbet_web_bucket" {
  depends_on = [
    aws_s3_bucket_ownership_controls.bayesbet_web_bucket,
    aws_s3_bucket_public_access_block.bayesbet_web_bucket,
  ]

  bucket = aws_s3_bucket.bayesbet_web_bucket.id
  acl    = "public-read"
}

resource "aws_s3_bucket_cors_configuration" "bayesbet_web_bucket" {
  bucket = aws_s3_bucket.bayesbet_web_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
  }
}

resource "aws_s3_bucket" "bayesbet_pipeline_bucket" {
  bucket = "${var.project}-pipeline-${var.env}"
}

resource "aws_s3_bucket" "bayesbet_dvc_bucket" {
  bucket = "${var.project}-dvc-${var.env}"
}