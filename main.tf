provider "aws" {
  region = "us-east-1"
}

#################################
# S3 Bucket unique
#################################
resource "aws_s3_bucket" "bucket" {
  bucket        = "api-request-croustillant-demo"
  force_destroy = true
}

#################################
# Lambda Function
#################################
resource "aws_lambda_function" "fetch_api_lambda" {
  filename         = "lambda/lambda_function.zip"
  function_name    = "api-request-croustillant-demo"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  role             = "arn:aws:iam::306780054766:role/LabRole"

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.bucket.bucket
    }
  }

  memory_size = 128
  timeout     = 60
}

#################################
# Lambda permissions for EventBridge
#################################
locals {
  fetch_schedules = {
    "fetch-api-1h-demo"  = "cron(15 1 ? * * *)"
    "fetch-api-9h-demo"  = "cron(15 9 ? * * *)"
    "fetch-api-11h-demo" = "cron(15 11 ? * * *)"
    "fetch-api-15h-demo" = "cron(15 15 ? * * *)"
  }
}

resource "aws_lambda_permission" "allow_eventbridge" {
  for_each      = local.fetch_schedules
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fetch_api_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.fetch_rules[each.key].arn
  statement_id  = "AllowExecutionFromEventBridge-${each.key}"
}

#################################
# EventBridge rules for Fetch API
#################################
resource "aws_cloudwatch_event_rule" "fetch_rules" {
  for_each            = local.fetch_schedules
  name                = each.key
  schedule_expression = each.value
}

resource "aws_cloudwatch_event_target" "fetch_targets" {
  for_each = local.fetch_schedules
  rule     = aws_cloudwatch_event_rule.fetch_rules[each.key].name
  target_id = each.key
  arn      = aws_lambda_function.fetch_api_lambda.arn
}
