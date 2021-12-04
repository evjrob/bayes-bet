resource "aws_dynamodb_table" "bayesbet_games" {
  name         = "${var.project}-main-${var.env}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "League"
  range_key    = "PredictionDate"

  attribute {
    name = "League"
    type = "S"
  }

  attribute {
    name = "PredictionDate"
    type = "S"
  }
}