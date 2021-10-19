resource "aws_sfn_state_machine" "bayesbet_nhl_sfn" {
  name     = "${var.project}-main-${var.env}"
  role_arn = "arn:aws:iam::012345678901:role/DummyRole"

  definition = <<EOF
{
  "Comment": "A Hello World example of the Amazon States Language using an AWS Lambda Function",
  "StartAt": "NHLMain",
  "States": {
    "NHLMain": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:012345678912:function:function",
      "Parameters": {
        "league.$": "$.league",
        "task.$": "$.task",
        "task_parameters.$": "$.taskParameters"
      },
      "End": true
    }
  }
}
EOF
}