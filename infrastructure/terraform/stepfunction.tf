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

resource "aws_cloudwatch_metric_alarm" "bayesbet_nhl_sfn_execution_failed" {
  alarm_name          = "${var.project}-nhl-sfn-execution-failed-${var.env}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors failed executions of the Step Function"
  alarm_actions       = [aws_sns_topic.sfn_alarm.arn]

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.bayesbet_nhl_sfn.arn
  }
}

resource "aws_sns_topic" "sfn_alarm" {
  name = "${var.project}-nhl-sfn-alarm-${var.env}"
}

resource "aws_sns_topic_subscription" "sfn_alarm_email" {
  topic_arn = aws_sns_topic.sfn_alarm.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
