# Wire relationships between Lambda, SQS, and RDS.
#
#   create_order  --SendMessage-->  SQS  --event source-->  generate_careplan
#   all three Lambdas get RDS connection env vars (code uses them later)
#
# Practice note: Lambdas stay OUT of VPC. That only works while RDS is
# publicly_accessible and SG allows inbound (your practice defaults).
# Production: put Lambdas in VPC + tighten SG to Lambda security group.

# ----- IAM: SQS send (create_order) + SQS consume (generate_careplan) -----

resource "aws_iam_role_policy" "careplan_lambda_sqs" {
  name = "careplan-practice-lambda-sqs"
  role = aws_iam_role.careplan_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CreateOrderSendToQueue"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueUrl",
          "sqs:GetQueueAttributes",
        ]
        Resource = [
          aws_sqs_queue.careplan_practice.arn,
        ]
      },
      {
        Sid    = "GenerateCareplanConsumeQueue"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility",
        ]
        Resource = [
          aws_sqs_queue.careplan_practice.arn,
        ]
      },
    ]
  })
}

# ----- SQS automatically invokes generate_careplan -----

resource "aws_lambda_event_source_mapping" "sqs_to_generate_careplan" {
  event_source_arn = aws_sqs_queue.careplan_practice.arn
  function_name    = aws_lambda_function.generate_careplan.arn
  batch_size       = 1
  enabled          = true

  # Optional: partial batch failure reporting (useful later)
  function_response_types = ["ReportBatchItemFailures"]
}

# Visibility timeout should be comfortably above Lambda timeout.
# Your queue default is 30s; generate_careplan timeout is raised in lambda.tf.
