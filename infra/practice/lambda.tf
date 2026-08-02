# Three CarePlan Lambdas + IAM baseline.
# Relationships (SQS trigger / extra SQS IAM) live in wiring.tf.
# Code package: lightweight stubs under runtimes/aws/stubs/

data "archive_file" "lambda_stubs" {
  type        = "zip"
  source_dir  = "${path.module}/../../runtimes/aws/stubs"
  output_path = "${path.module}/build/careplan_lambda_stubs.zip"
}

# ----- IAM: shared role (logs + policies in wiring.tf) -----

resource "aws_iam_role" "careplan_lambda" {
  name = "careplan-practice-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-lambda-exercise"
  }
}

resource "aws_iam_role_policy_attachment" "careplan_lambda_basic_logs" {
  role       = aws_iam_role.careplan_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

locals {
  # Shared DB settings for all Lambdas (matches local Django env names)
  rds_env = {
    POSTGRES_HOST     = aws_db_instance.careplan.address
    POSTGRES_PORT     = tostring(aws_db_instance.careplan.port)
    POSTGRES_DB       = aws_db_instance.careplan.db_name
    POSTGRES_USER     = aws_db_instance.careplan.username
    POSTGRES_PASSWORD = var.db_password
  }

  lambda_common = {
    role             = aws_iam_role.careplan_lambda.arn
    runtime          = "python3.12"
    filename         = data.archive_file.lambda_stubs.output_path
    source_code_hash = data.archive_file.lambda_stubs.output_base64sha256
    memory_size      = 128
    tags = {
      Project = "CarePlan"
      Purpose = "terraform-lambda-exercise"
    }
  }
}

resource "aws_lambda_function" "create_order" {
  function_name = "careplan-create-order"
  handler       = "create_order.handler"
  description   = "Create order → enqueue SQS (stub)"

  role             = local.lambda_common.role
  runtime          = local.lambda_common.runtime
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  timeout          = 15
  memory_size      = local.lambda_common.memory_size
  tags             = local.lambda_common.tags

  environment {
    variables = merge(local.rds_env, {
      SQS_QUEUE_URL = aws_sqs_queue.careplan_practice.url
    })
  }
}

resource "aws_lambda_function" "generate_careplan" {
  function_name = "careplan-generate-careplan"
  handler       = "generate_careplan.handler"
  description   = "Triggered by SQS to generate CarePlan (stub)"

  role             = local.lambda_common.role
  runtime          = local.lambda_common.runtime
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  # Keep below SQS visibility_timeout_seconds (30)
  timeout          = 20
  memory_size      = local.lambda_common.memory_size
  tags             = local.lambda_common.tags

  environment {
    variables = local.rds_env
  }
}

resource "aws_lambda_function" "get_order" {
  function_name = "careplan-get-order"
  handler       = "get_order.handler"
  description   = "Get order / care plan status (stub)"

  role             = local.lambda_common.role
  runtime          = local.lambda_common.runtime
  filename         = local.lambda_common.filename
  source_code_hash = local.lambda_common.source_code_hash
  timeout          = 15
  memory_size      = local.lambda_common.memory_size
  tags             = local.lambda_common.tags

  environment {
    variables = local.rds_env
  }
}

output "lambda_create_order_name" {
  value = aws_lambda_function.create_order.function_name
}

output "lambda_generate_careplan_name" {
  value = aws_lambda_function.generate_careplan.function_name
}

output "lambda_get_order_name" {
  value = aws_lambda_function.get_order.function_name
}

output "lambda_role_arn" {
  value = aws_iam_role.careplan_lambda.arn
}
