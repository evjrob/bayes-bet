resource "aws_s3_bucket" "bayesbet_web_bucket" {
  bucket = "${var.project}-web-${var.env}"
  acl    = "public-read"
  force_destroy = true
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
  }
}

resource "aws_s3_bucket" "bayesbet_pipeline_bucket" {
  bucket = "${var.project}-pipeline-${var.env}"
  force_destroy = true
}