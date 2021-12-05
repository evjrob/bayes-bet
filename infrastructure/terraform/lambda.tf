resource "aws_lambda_function" "bayesbet_model_lambda" {
  function_name = "${var.project}-model-${var.env}"
  role          = aws_iam_role.bayesbet_model_lambda_role.arn
  memory_size   = 4096
  timeout       = 300
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.bayesbet_model_ecr.repository_url}:latest"

  image_config {
    command           = ["app.lambda_handler"]
    entry_point       = ["python", "-m", "awslambdaric"]
    working_directory = "/workspaces/bayes-bet/model/awslambda"
  }

  environment {
    variables = {
      WEB_S3_BUCKET       = "${aws_s3_bucket.bayesbet_web_bucket.id}"
      PIPELINE_S3_BUCKET  = "${aws_s3_bucket.bayesbet_pipeline_bucket.id}"
      DYNAMODB_TABLE_NAME = "${aws_dynamodb_table.bayesbet_games.id}"
    }
  }

  depends_on = [
    null_resource.ecr_docker_image,
  ]
}
