# TODO: Test S3 resources for aws-tagger
# Events to test: CreateBucket

# S3 Bucket
resource "aws_s3_bucket" "test" {
  bucket = "${local.name_prefix}-bucket-${random_string.suffix.result}"

  tags = {
    Name = "${local.name_prefix}-s3-bucket"
  }
}

# Random string for unique bucket names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "test" {
  bucket = aws_s3_bucket.test.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "test" {
  bucket = aws_s3_bucket.test.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
