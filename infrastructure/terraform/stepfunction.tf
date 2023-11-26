data "aws_caller_identity" "current" {}

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
                    },
                    {
                      "Variable": "$.next_game_date",
                      "StringLessThanEqualsPath": "$.today"
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
              "MaxConcurrency": 6,
              "Parameters": {
                "game.$": "$$.Map.Item.Value",
                "posteriors.$": "$.posteriors",
                "teams_to_int.$": "$.teams_to_int"
              },
              "ItemsPath": "$.games_to_predict",
              "ResultPath": "$.game_preds",
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
              "Type": "Task",
              "Resource": "${aws_lambda_function.bayesbet_model_lambda.arn}",
              "ResultPath": "$.new_record_output",
              "Parameters": {
                "league": "nhl",
                "task": "create_record",
                "task_parameters": {
                  "bucket_name": "${aws_s3_bucket.bayesbet_web_bucket.id}",
                  "game_date.$": "$.next_game_date",
                  "posteriors.$": "$.posteriors",
                  "int_to_teams.$": "$.int_to_teams",
                  "game_preds.$": "$.game_preds"
                }
              },
              "Next": "BackfillChoice"
            },
            "BackfillChoice":{
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.next_game_date",
                  "StringLessThanPath": "$.today",
                  "Next": "NewBackfillExecution"
                }
              ],
              "Default": "Finish"
            },
            "NewBackfillExecution": {
              "Type":"Task",
              "Resource":"arn:aws:states:::states:startExecution",
              "Parameters":{  
                  "Input":{},
                  "StateMachineArn":"arn:aws:states:us-east-1:${data.aws_caller_identity.current.account_id}:stateMachine:${var.project}-nhl-main-${var.env}"
              },
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
