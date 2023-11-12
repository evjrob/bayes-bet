resource "aws_cloudwatch_event_rule" "bayesbet_nhl_main_schedule" {
  name                = "${var.project}-nhl-main-schedule-${var.env}"
  description         = "Scheduled trigger for main nhl pipeline"
  schedule_expression = "cron(0 8 * * ? *)"
  is_enabled          = false

resource "aws_cloudwatch_event_target" "bayesbet_nhl_main_target" {
  rule      = aws_cloudwatch_event_rule.bayesbet_nhl_main_schedule.name
  target_id = "${var.project}-nhl-main-target-${var.env}"
  arn       = aws_sfn_state_machine.bayesbet_nhl_sfn.arn
  role_arn  = aws_iam_role.bayesbet_eventbridge_role.arn
}