resource "aws_lambda_function" "bayesbet_model_lambda" {
  function_name = "${var.project}-model-${var.env}"
  role          = aws_iam_role.bayesbet_model_lambda_role.arn
  memory_size   = 2048
  timeout       = 450
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.bayesbet_model_ecr.repository_url}:${random_id.image_tag.hex}"

  image_config {
    command           = ["app.lambda_handler"]
    entry_point       = ["python", "-m", "awslambdaric"]
    working_directory = "/workspaces/bayes-bet/model"
  }

  environment {
    variables = {
      WEB_S3_BUCKET             = "${aws_s3_bucket.bayesbet_web_bucket.id}"
      PIPELINE_S3_BUCKET        = "${aws_s3_bucket.bayesbet_pipeline_bucket.id}"
      DYNAMODB_PRED_TABLE_NAME  = "${aws_dynamodb_table.bayesbet_predictions.id}"
      DYNAMODB_MODEL_TABLE_NAME = "${aws_dynamodb_table.bayesbet_model_state.id}"
      DEPLOYMENT_VERSION        = var.deployment_version
    }
  }

  depends_on = [
    null_resource.ecr_docker_image_model,
  ]
}

resource "aws_lambda_function" "bayesbet_social_lambda" {
  function_name = "${var.project}-social-${var.env}"
  role          = aws_iam_role.bayesbet_social_lambda_role.arn
  memory_size   = 2048
  timeout       = 450
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.bayesbet_social_ecr.repository_url}:${random_id.image_tag.hex}"

  environment {
    variables = {
      TWITTER_BEARER_TOKEN        = var.twitter_bearer_token
      TWITTER_CONSUMER_KEY        = var.twitter_consumer_key
      TWITTER_CONSUMER_SECRET     = var.twitter_consumer_secret
      TWITTER_ACCESS_TOKEN        = var.twitter_access_token
      TWITTER_ACCESS_TOKEN_SECRET = var.twitter_access_token_secret
    }
  }

  depends_on = [
    null_resource.ecr_docker_image_social,
  ]
}

resource "aws_cloudwatch_metric_alarm" "social_lambda_error" {
  alarm_name          = "${var.project}-social-lambda-error-${var.env}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors errors in the social Lambda function"
  alarm_actions       = [aws_sns_topic.social_lambda_alarm.arn]

  dimensions = {
    FunctionName = aws_lambda_function.bayesbet_social_lambda.function_name
  }
}

resource "aws_sns_topic" "social_lambda_alarm" {
  name = "${var.project}-social-lambda-alarm-${var.env}"
}

resource "aws_sns_topic_subscription" "social_lambda_alarm_email" {
  topic_arn = aws_sns_topic.social_lambda_alarm.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
