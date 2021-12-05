resource "aws_sfn_state_machine" "bayesbet_nhl_sfn" {
  name     = "${var.project}-nhl-main-${var.env}"
  role_arn = "${aws_iam_role.bayesbet_sfn_role.arn}"

  definition = <<EOF
{
  "Comment": "The main BayesBet NHL model pipeline for daily game predictions",
  "StartAt": "IngestData",
  "States": {
    "IngestData": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.bayesbet_model_lambda.arn}",
      "Parameters": {
        "league": "nhl",
        "task": "ingest_data",
        "task_parameters": {
          "bucket_name": "${aws_s3_bucket.bayesbet_pipeline_bucket.id}",
          "pipeline_name": "${var.project}-main-${var.env}",
          "job_id.$": "$$.Execution.Name"
        }
      },
      "Next": "DailyUpdate"
    },
    "DailyUpdate": {
      "Type": "Parallel",
      "End": true,
      "Branches": [
        {
          "StartAt": "UpdatePreviousRecord",
          "States": {
            "UpdatePreviousRecord": {
              "Type": "Task",
              "Resource": "${aws_lambda_function.bayesbet_model_lambda.arn}",
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
              "End": true
            }
          }
        },
        {
          "StartAt": "NewGamesChoice",
          "States": {
            "NewGamesChoice":{
              "Type": "Choice",
              "Choices": [
                {
                  "And": [
                    {
                      "Variable": "$.next_game_date",
                      "IsNull": false
                    },
                    {
                      "Variable": "$.next_game_date",
                      "StringGreaterThanPath": "$.last_pred_date"
                    }
                  ],
                  "Next": "ModelInference"
                }
              ],
              "Default": "Finish"
            },
            "ModelInference": {
              "Type": "Task",
              "Resource": "${aws_lambda_function.bayesbet_model_lambda.arn}",
              "ResultPath": "$.posteriors",
              "Parameters": {
                "league": "nhl",
                "task": "model_inference",
                "task_parameters": {
                  "bucket_name": "${aws_s3_bucket.bayesbet_pipeline_bucket.id}",
                  "pipeline_name": "${var.project}-main-${var.env}",
                  "job_id.$": "$$.Execution.Name",
                  "last_pred_date.$": "$.last_pred_date",
                  "teams_to_int.$": "$.teams_to_int",
                  "n_teams.$": "$.n_teams"
                }
              },
              "Next": "PredictGames"
            },
            "PredictGames": {
              "Type": "Map",
              "MaxConcurrency": 1,
              "Parameters": {
                "game.$": "$$.Map.Item.Value",
                "posteriors.$": "$.posteriors",
                "teams_to_int.$": "$.teams_to_int"
              },
              "ItemsPath": "$.games_to_predict",
              "ResultPath": "$.predictions",
              "Next": "CreateNewRecord",
              "Iterator": {
                "StartAt": "PredictGame",
                "States": {
                  "PredictGame": {
                    "Type": "Task",
                    "Resource": "${aws_lambda_function.bayesbet_model_lambda.arn}",
                    "Parameters": {
                      "league": "nhl",
                      "task": "predict_game",
                      "task_parameters": {
                        "game.$": "$.game",
                        "posteriors.$": "$.posteriors",
                        "teams_to_int.$": "$.teams_to_int"
                      }
                    },
                    "End": true
                  }
                }
              }
            },
            "CreateNewRecord": {
              "Type": "Pass",
              "Next": "Finish"
            },
            "Finish": {
              "Type": "Succeed"
            }
          }
        }
      ]
    }
  }
}
EOF
}
