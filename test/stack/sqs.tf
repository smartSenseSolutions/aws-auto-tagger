# TODO: Test SQS resources for aws-tagger
# Events to test: CreateQueue

# SQS Queue
resource "aws_sqs_queue" "test" {
  name = "${local.name_prefix}-queue"

  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600
  delay_seconds              = 0
  receive_wait_time_seconds  = 0

  tags = {
    Name = "${local.name_prefix}-sqs-queue"
  }
}

# SQS Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name = "${local.name_prefix}-dlq"

  visibility_timeout_seconds = 30
  message_retention_seconds  = 1209600
  delay_seconds              = 0
  receive_wait_time_seconds  = 0

  tags = {
    Name = "${local.name_prefix}-sqs-dlq"
  }
}

# SQS Queue with Dead Letter Queue
resource "aws_sqs_queue" "with_dlq" {
  name = "${local.name_prefix}-queue-with-dlq"

  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600
  delay_seconds              = 0
  receive_wait_time_seconds  = 0

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${local.name_prefix}-sqs-queue-with-dlq"
  }
}
