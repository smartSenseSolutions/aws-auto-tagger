# TODO: Test all AWS services supported in services.py
# Current coverage: 30+ AWS services
# 
# Services to test:
# - EC2: RunInstances, CreateVolume, CreateSecurityGroup, CreateVpc, CreateSubnet, CreateSnapshot, CreateImage, AllocateAddress
# - S3: CreateBucket
# - RDS: CreateDBInstance, CreateDBCluster
# - Lambda: CreateFunction
# - EKS: CreateCluster, CreateNodegroup
# - ELBV2: CreateLoadBalancer, CreateTargetGroup
# - DynamoDB: CreateTable
# - KMS: CreateKey, CreateAlias
# - Secrets Manager: CreateSecret
# - SNS: CreateTopic
# - SQS: CreateQueue
# - CloudWatch: CreateLogGroup, PutMetricAlarm
# - Route53: CreateHostedZone
# - API Gateway: CreateRestApi, CreateApiKey
# - ECS: CreateCluster, CreateService
# - ECR: CreateRepository
# - Step Functions: CreateStateMachine
# - CloudFormation: CreateStack
# - EFS: CreateFileSystem
# - Glue: CreateDatabase, CreateGlueTable
# - OpenSearch: CreateDomain
# - Redshift: CreateCluster
# - Cognito: CreateUserPool, CreateIdentityPool
# - Bedrock: CreateModelCustomizationJob
# - Amplify: CreateApp
# - CloudFront: CreateDistribution
# - IAM: CreateRole, CreateUser, CreatePolicy

# Variables
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "aws-tagger"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  ec2 = {
    instance_type = "t4g.nano"
    ami           = "ami-0c02fb55956c7d316"
    volume_size   = 10
  }

  rds = {
    instance_type     = "db.t4g.micro"
    engine            = "mysql"
    allocated_storage = 20
    engine_version    = "8.0"
  }

  eks = {
    version                  = "1.33"
    node_group_instance_type = "t4g.small"
  }

}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}