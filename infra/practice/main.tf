# Practice: main SQS queue + Dead Letter Queue.
# Messages that fail processing 3 times are moved to the DLQ.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1) Dead Letter Queue — holds poison / repeatedly failed messages
resource "aws_sqs_queue" "careplan_practice_dlq" {
  name = "careplan-practice-dlq"

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-dlq-exercise"
  }
}

# 2) Main queue — redrive to DLQ after 3 receives without successful delete
resource "aws_sqs_queue" "careplan_practice" {
  name = "careplan-practice-queue"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.careplan_practice_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-first-exercise"
  }
}

# Allow the main queue to redirect messages into the DLQ
resource "aws_sqs_queue_redrive_allow_policy" "careplan_practice_dlq_allow" {
  queue_url = aws_sqs_queue.careplan_practice_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.careplan_practice.arn]
  })
}

output "queue_url" {
  description = "URL of the practice SQS queue"
  value       = aws_sqs_queue.careplan_practice.url
}

output "queue_arn" {
  description = "ARN of the practice SQS queue"
  value       = aws_sqs_queue.careplan_practice.arn
}

output "dlq_url" {
  description = "URL of the Dead Letter Queue"
  value       = aws_sqs_queue.careplan_practice_dlq.url
}

output "dlq_arn" {
  description = "ARN of the Dead Letter Queue"
  value       = aws_sqs_queue.careplan_practice_dlq.arn
}
