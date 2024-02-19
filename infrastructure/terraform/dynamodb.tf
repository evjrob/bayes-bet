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

resource "aws_dynamodb_table" "bayesbet_predictions" {
  name         = "${var.project}-predictions-${var.env}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "league"
  range_key    = "prediction_date"

  attribute {
    name = "league"
    type = "S"
  }

  attribute {
    name = "prediction_date"
    type = "S"
  }
}