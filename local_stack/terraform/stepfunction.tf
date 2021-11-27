resource "aws_sfn_state_machine" "bayesbet_nhl_sfn" {
  name     = "${var.project}-main-${var.env}"
  role_arn = "arn:aws:iam::012345678901:role/DummyRole"

  definition = <<EOF
{
  "Comment": "A Hello World example of the Amazon States Language using an AWS Lambda Function",
  "StartAt": "IngestData",
  "States": {
    "IngestData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:012345678912:function:function",
      "Parameters": {
        "league": "nhl",
        "task": "ingest_data",
        "task_parameters": {
          "bucket_name": "${aws_s3_bucket.bayesbet_pipeline_bucket.id}",
          "pipeline_name": "${var.project}-main-${var.env}",
          "job_id.$": "$$.Execution.Name"
        }
      },
      "Next": "UpdatePreviousRecord"
    },
    "UpdatePreviousRecord": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:012345678912:function:function",
      "Parameters": {
        "league": "nhl",
        "task": "update_previous_record",
        "task_parameters": {
          "bucket_name": "${aws_s3_bucket.bayesbet_pipeline_bucket.id}",
          "pipeline_name": "${var.project}-main-${var.env}",
          "job_id.$": "$$.Execution.Name",
          "last_pred_date.$": "$.last_pred_date",
          "season_start.$": "$.season_start"
        }
      },
      "Next": "Finish"
    },
    "Finish": {
      "Type": "Succeed"
    }
  }
}
EOF
}
