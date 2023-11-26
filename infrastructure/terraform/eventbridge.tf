resource "aws_cloudwatch_event_rule" "bayesbet_nhl_main_schedule" {
  name                = "${var.project}-nhl-main-schedule-${var.env}"
  description         = "Scheduled trigger for main nhl pipeline"
  schedule_expression = "cron(0 8 * * ? *)"
  is_enabled          = true
}

resource "aws_cloudwatch_event_target" "bayesbet_nhl_main_target" {
  rule      = aws_cloudwatch_event_rule.bayesbet_nhl_main_schedule.name
  target_id = "${var.project}-nhl-main-target-${var.env}"
  arn       = aws_sfn_state_machine.bayesbet_nhl_sfn.arn
  role_arn  = aws_iam_role.bayesbet_eventbridge_role.arn
}

resource "aws_cloudwatch_event_rule" "bayesbet_nhl_social_schedule" {
  name                = "${var.project}-nhl-social-schedule-${var.env}"
  description         = "Scheduled trigger for NHL social lambda"
  schedule_expression = "cron(0 14 * * ? *)"
  is_enabled          = var.socials_scheduled
}

resource "aws_cloudwatch_event_target" "bayesbet_nhl_social_target" {
  rule      = aws_cloudwatch_event_rule.bayesbet_nhl_social_schedule.name
  target_id = "${var.project}-nhl-social-target-${var.env}"
  arn       = aws_lambda_function.screenshot_function.arn

  input = jsonencode({
    url = var.socials_url
  })
}