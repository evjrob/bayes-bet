resource "aws_iam_role" "bayesbet_model_lambda_role" {
  name = "${var.project}-model-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


resource "aws_iam_policy" "bayesbet_model_lambda_policy" {
  name        = "${var.project}-model-policy-${var.env}"
  description = "Allow bayesbet model lambda to connect to resources"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:List*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.bayesbet_web_bucket.id}"
    },
    {
      "Action": [
        "s3:Get*",
        "s3:Put*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.bayesbet_web_bucket.id}/*"
    },
    {
      "Action": [
        "s3:List*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.bayesbet_pipeline_bucket.id}"
    },
    {
      "Action": [
        "s3:Get*",
        "s3:Put*"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.bayesbet_pipeline_bucket.id}/*"
    },
    {
      "Action": [
        "dynamodb:List*",
        "dynamodb:DescribeReservedCapacity*",
        "dynamodb:DescribeLimits",
        "dynamodb:DescribeTimeToLive"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "dynamodb:BatchGet*",
        "dynamodb:DescribeStream",
        "dynamodb:DescribeTable",
        "dynamodb:Get*",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWrite*",
        "dynamodb:CreateTable",
        "dynamodb:Delete*",
        "dynamodb:Update*",
        "dynamodb:PutItem"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.bayesbet_predictions.arn}"
    },
    {
      "Action": [
        "dynamodb:BatchGet*",
        "dynamodb:DescribeStream",
        "dynamodb:DescribeTable",
        "dynamodb:Get*",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWrite*",
        "dynamodb:CreateTable",
        "dynamodb:Delete*",
        "dynamodb:Update*",
        "dynamodb:PutItem"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.bayesbet_model_state.arn}"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "bayesbet_model_lambda_policy_attach" {
  role       = aws_iam_role.bayesbet_model_lambda_role.name
  policy_arn = aws_iam_policy.bayesbet_model_lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "bayesbet_model_basic_lambda_attach" {
  role       = aws_iam_role.bayesbet_model_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "bayesbet_social_lambda_role" {
  name = "${var.project}-social-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "bayesbet_social_basic_lambda_attach" {
  role       = aws_iam_role.bayesbet_social_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "bayesbet_sfn_role" {
  name = "${var.project}-sfn-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


resource "aws_iam_policy" "bayesbet_sfn_policy" {
  name        = "${var.project}-sfn-policy-${var.env}"
  description = "Allow bayesbet step functions to connect to resources"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Effect": "Allow",
      "Resource": "${aws_lambda_function.bayesbet_model_lambda.arn}"
    },
    {
      "Action": [
        "states:StartExecution"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sfn_state_machine.bayesbet_nhl_sfn.arn}"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "bayesbet_sfn_policy_attach" {
  role       = aws_iam_role.bayesbet_sfn_role.name
  policy_arn = aws_iam_policy.bayesbet_sfn_policy.arn
}

resource "aws_iam_role" "bayesbet_eventbridge_role" {
  name = "${var.project}-eventbridge-role-${var.env}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy" "bayesbet_eventbridge_policy" {
  name = "${var.project}-eventbridge-policy-${var.env}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "states:StartExecution"
      ],
      "Effect": "Allow",
      "Resource": "${aws_sfn_state_machine.bayesbet_nhl_sfn.arn}"
    },
    {
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Effect": "Allow",
      "Resource": "${aws_lambda_function.bayesbet_social_lambda.arn}"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "bayesbet_eventbridge_policy_attach" {
  role       = aws_iam_role.bayesbet_eventbridge_role.name
  policy_arn = aws_iam_policy.bayesbet_eventbridge_policy.arn
}