#################################
# Glue Catalog Database
#################################
resource "aws_glue_catalog_database" "database" {
  name = "croustillant_db-demo"
}

#################################
# Glue Crawler
#################################
resource "aws_glue_crawler" "crawler" {
  name          = "croustillant_glue_crawler-demo"
  role          = "arn:aws:iam::306780054766:role/LabRole"
  database_name = aws_glue_catalog_database.database.name

  s3_target {
    path = "s3://${aws_s3_bucket.bucket.bucket}/raw/"
  }

  configuration = jsonencode({
    Version = 1.0
  })
}

#################################
# EventBridge rules for Glue Crawler (every 30 minutes)
#################################
locals {
  crawler_schedules = {
    "crawler-1h-demo" = "cron(30 1 ? * * *)"
    "crawler-9h-demo" = "cron(30 9 ? * * *)"
    "crawler-11h-demo" = "cron(30 11 ? * * *)"
    "crawler-15h-demo" = "cron(30 15 ? * * *)"
  }
}

resource "aws_lambda_function" "start_crawler_lambda" {
  filename      = "lambda/start_crawler.zip"
  function_name = "start_crawler_lambda-demo"
  handler       = "start_crawler.lambda_handler"
  runtime       = "python3.11"
  role          = "arn:aws:iam::306780054766:role/LabRole"

  environment {
    variables = {
      CRAWLER_NAME = aws_glue_crawler.crawler.name
    }
  }

  memory_size = 128
  timeout     = 3
}

resource "aws_lambda_permission" "allow_eventbridge_crawler" {
  for_each      = local.crawler_schedules
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start_crawler_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.crawler_rules[each.key].arn
  statement_id  = "AllowExecutionFromEventBridge-${each.key}"
}

resource "aws_cloudwatch_event_rule" "crawler_rules" {
  for_each            = local.crawler_schedules
  name                = each.key
  schedule_expression = each.value
}

resource "aws_cloudwatch_event_target" "crawler_targets" {
  for_each = local.crawler_schedules
  rule     = aws_cloudwatch_event_rule.crawler_rules[each.key].name
  target_id = each.key
  arn      = aws_lambda_function.start_crawler_lambda.arn
}
