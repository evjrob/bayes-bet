data "aws_caller_identity" "current" {}

resource "aws_sfn_state_machine" "bayesbet_nhl_sfn" {
  name     = "${var.project}-nhl-main-${var.env}"
  role_arn = aws_iam_role.bayesbet_sfn_role.arn

  definition = templatefile("${path.module}/assets/bayesbet_nhl_sfn.asl.json", {
    task_lambda = aws_lambda_function.bayesbet_model_lambda.arn,
    pipeline_bucket = aws_s3_bucket.bayesbet_pipeline_bucket.id,
    web_bucket = aws_s3_bucket.bayesbet_web_bucket.id,
    project = var.project,
    environment = var.env,
    max_concurrency = var.sfn_max_concurrency,
    account_id = data.aws_caller_identity.current.account_id
    }
  )
}
