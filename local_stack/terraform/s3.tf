resource "aws_s3_bucket" "bayesbet_bucket" {
  bucket = "${var.project}-${var.env}"
  acl    = "public-read"
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
  }
}