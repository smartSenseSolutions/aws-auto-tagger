"""
Simple Service Configurations - Easy to extend

Adding a new AWS service is as simple as adding a few lines here.
Now using JMESPath for much cleaner resource extraction!
"""

from .utils import logger


# Service configurations organized by eventsource - much cleaner!
SERVICE_CONFIGS = {
    "ec2": {
        "RunInstances": {
            "eventsource": "ec2",
            "resource_type": "ec2:instance",
            "section": "responseElements",
            "jmespath": "instancesSet.items[*].instanceId",  # Gets ALL instances, not just first
        },
        "CreateVolume": {
            "eventsource": "ec2",
            "resource_type": "ec2:volume",
            "section": "responseElements",
            "jmespath": "volumeId",
        },
        "CreateSecurityGroup": {
            "eventsource": "ec2",
            "resource_type": "ec2:security-group",
            "section": "responseElements",
            "jmespath": "groupId",
        },
        "CreateVpc": {
            "eventsource": "ec2",
            "resource_type": "ec2:vpc",
            "section": "responseElements",
            "jmespath": "vpc.vpcId",
        },
        "CreateSubnet": {
            "eventsource": "ec2",
            "resource_type": "ec2:subnet",
            "section": "responseElements",
            "jmespath": "subnet.subnetId",
        },
        "CreateSnapshot": {
            "eventsource": "ec2",
            "resource_type": "ec2:snapshot",
            "section": "responseElements",
            "jmespath": "snapshotId",
        },
        "CreateImage": {
            "eventsource": "ec2",
            "resource_type": "ec2:image",
            "section": "responseElements",
            "jmespath": "imageId",
        },
        "AllocateAddress": {
            "eventsource": "ec2",
            "resource_type": "ec2:elastic-ip",
            "section": "responseElements",
            "jmespath": "allocationId",
        },
    },
    "s3": {
        "CreateBucket": {
            "eventsource": "s3",
            "resource_type": "s3:bucket",
            "section": "requestParameters",
            "jmespath": "bucketName",
        }
    },
    "rds": {
        "CreateDBInstance": {
            "eventsource": "rds",
            "resource_type": "rds:db",
            "section": "requestParameters",
            "jmespath": "dBInstanceIdentifier",
        },
        "CreateDBCluster": {
            "eventsource": "rds",
            "resource_type": "rds:cluster",
            "section": "requestParameters",
            "jmespath": "dBClusterIdentifier",
        },
    },
    "lambda": {
        "CreateFunction20150331": {
            "eventsource": "lambda",
            "resource_type": "lambda:function",
            "section": "requestParameters",
            "jmespath": "functionName",
        }
    },
    "eks": {
        "CreateCluster": {
            "eventsource": "eks",
            "resource_type": "eks:cluster",
            "section": "responseElements",
            "jmespath": "cluster.name",
        },
        "CreateNodegroup": {
            "eventsource": "eks",
            "resource_type": "eks:nodegroup",
            "section": "responseElements",
            "jmespath": "join('/', [nodegroup.clusterName, nodegroup.nodegroupName])",
        },
    },
    "elbv2": {
        "CreateLoadBalancer": {
            "eventsource": "elbv2",
            "resource_type": "elbv2:loadbalancer",
            "section": "responseElements",
            "jmespath": "loadBalancers[*].loadBalancerArn",
        },
        "CreateTargetGroup": {
            "eventsource": "elbv2",
            "resource_type": "elbv2:targetgroup",
            "section": "responseElements",
            "jmespath": "targetGroups[*].targetGroupArn",
        },
    },
    "dynamodb": {
        "CreateTable": {
            "eventsource": "dynamodb",
            "resource_type": "dynamodb:table",
            "section": "responseElements",
            "jmespath": "tableDescription.tableName",
        }
    },
    "kms": {
        "CreateKey": {
            "eventsource": "kms",
            "resource_type": "kms:key",
            "section": "responseElements",
            "jmespath": "keyMetadata.keyId",
        },
        "CreateAlias": {
            "eventsource": "kms",
            "resource_type": "kms:alias",
            "section": "requestParameters",
            "jmespath": "aliasName",
        },
    },
    "secretsmanager": {
        "CreateSecret": {
            "eventsource": "secretsmanager",
            "resource_type": "secretsmanager:secret",
            "section": "responseElements",
            "jmespath": "arn",
        }
    },
    "sns": {
        "CreateTopic": {
            "eventsource": "sns",
            "resource_type": "sns:topic",
            "section": "responseElements",
            "jmespath": "topicArn",
        }
    },
    "sqs": {
        "CreateQueue": {
            "eventsource": "sqs",
            "resource_type": "sqs:queue",
            "section": "responseElements",
            "jmespath": "queueUrl",
        }
    },
    "cloudwatch": {
        "CreateLogGroup": {
            "eventsource": "cloudwatch",
            "resource_type": "cloudwatch:loggroup",
            "section": "requestParameters",
            "jmespath": "logGroupName",
        },
        "PutMetricAlarm": {
            "eventsource": "cloudwatch",
            "resource_type": "cloudwatch:alarm",
            "section": "requestParameters",
            "jmespath": "alarmName",
        },
    },
    "route53": {
        "CreateHostedZone": {
            "eventsource": "route53",
            "resource_type": "route53:hostedzone",
            "section": "responseElements",
            "jmespath": "hostedZone.id",
        }
    },
    "apigateway": {
        "CreateRestApi": {
            "eventsource": "apigateway",
            "resource_type": "apigateway:restapi",
            "section": "responseElements",
            "jmespath": "id",
        },
        "CreateApiKey": {
            "eventsource": "apigateway",
            "resource_type": "apigateway:apikey",
            "section": "responseElements",
            "jmespath": "id",
        },
    },
    "ecs": {
        "CreateCluster": {
            "eventsource": "ecs",
            "resource_type": "ecs:cluster",
            "section": "responseElements",
            "jmespath": "cluster.clusterName",
        },
        "CreateService": {
            "eventsource": "ecs",
            "resource_type": "ecs:service",
            "section": "responseElements",
            "jmespath": "service.serviceName",
        },
    },
    "ecr": {
        "CreateRepository": {
            "eventsource": "ecr",
            "resource_type": "ecr:repository",
            "section": "responseElements",
            "jmespath": "repository.repositoryName",
        }
    },
    "stepfunctions": {
        "CreateStateMachine": {
            "eventsource": "stepfunctions",
            "resource_type": "stepfunctions:statemachine",
            "section": "responseElements",
            "jmespath": "stateMachineArn",
        }
    },
    "cloudformation": {
        "CreateStack": {
            "eventsource": "cloudformation",
            "resource_type": "cloudformation:stack",
            "section": "requestParameters",
            "jmespath": "stackName",
        }
    },
    "efs": {
        "CreateFileSystem": {
            "eventsource": "efs",
            "resource_type": "efs:filesystem",
            "section": "responseElements",
            "jmespath": "fileSystemId",
        }
    },
    "glue": {
        "CreateDatabase": {
            "eventsource": "glue",
            "resource_type": "glue:database",
            "section": "requestParameters",
            "jmespath": "databaseInput.name",
        },
        "CreateGlueTable": {
            "eventsource": "glue",
            "resource_type": "glue:table",
            "section": "requestParameters",
            "jmespath": "tableInput.name",
        },
    },
    "opensearch": {
        "CreateDomain": {
            "eventsource": "opensearch",
            "resource_type": "opensearch:domain",
            "section": "requestParameters",
            "jmespath": "domainName",
        }
    },
    "redshift": {
        "CreateCluster": {
            "eventsource": "redshift",
            "resource_type": "redshift:cluster",
            "section": "requestParameters",
            "jmespath": "clusterIdentifier",
        }
    },
    "cognito-idp": {
        "CreateUserPool": {
            "eventsource": "cognito-idp",
            "resource_type": "cognito:userpool",
            "section": "responseElements",
            "jmespath": "userPool.id",
        }
    },
    "cognito-identity": {
        "CreateIdentityPool": {
            "eventsource": "cognito-identity",
            "resource_type": "cognito:identitypool",
            "section": "responseElements",
            "jmespath": "identityPoolId",
        }
    },
    "bedrock": {
        "CreateModelCustomizationJob": {
            "eventsource": "bedrock",
            "resource_type": "bedrock:model",
            "section": "responseElements",
            "jmespath": "jobArn",
        }
    },
    "amplify": {
        "CreateApp": {
            "eventsource": "amplify",
            "resource_type": "amplify:app",
            "section": "responseElements",
            "jmespath": "app.appId",
        }
    },
    "cloudfront": {
        "CreateDistribution": {
            "eventsource": "cloudfront",
            "resource_type": "cloudfront:distribution",
            "section": "responseElements",
            "jmespath": "distribution.id",
        }
    },
    "iam": {
        "CreateRole": {
            "eventsource": "iam",
            "resource_type": "iam:role",
            "section": "responseElements",
            "jmespath": "role.arn",
        },
        "CreateUser": {
            "eventsource": "iam",
            "resource_type": "iam:user",
            "section": "responseElements",
            "jmespath": "user.userName",
        },
        "CreatePolicy": {
            "eventsource": "iam",
            "resource_type": "iam:policy",
            "section": "responseElements",
            "jmespath": "policy.arn",
        },
    },
}


def get_service_config(event_name: str) -> dict:
    """Get service configuration for an event"""
    # Search through all eventsources for the event
    for eventsource, events in SERVICE_CONFIGS.items():
        if event_name in events:
            return events[event_name]
    return None


def tag_resource(
    eventsource: str,
    resource_type: str,
    resource_id: str,
    username: str,
    creation_time: str,
    config,
    clients,
) -> bool:
    """Tag a resource - simplified logic"""
    logger.debug(f"Tagging: {resource_type}:{resource_id}")
    try:
        # Prepare tags
        tags = [{"Key": config.owner_tag_name, "Value": username}]

        # Add creation time tag if available
        if creation_time:
            tags.append({"Key": config.creation_time_tag_name, "Value": creation_time})

        # Add additional tags
        if config.additional_tags:
            for key, value in config.additional_tags.items():
                tags.append({"Key": key, "Value": value})

        logger.debug(f"Tagging {resource_type}:{resource_id} with {len(tags)} tags")

        # Tag based on event source - using match-case for cleaner code
        match eventsource:
            case "ec2":
                clients["ec2"].create_tags(Resources=[resource_id], Tags=tags)

            case "s3":
                clients["s3"].put_bucket_tagging(
                    Bucket=resource_id, Tagging={"TagSet": tags}
                )

            case "rds":
                # Handle both DB instances and clusters
                if resource_type == "rds:cluster":
                    arn = f"arn:aws:rds:{clients['region']}:{clients['account_id']}:cluster:{resource_id}"
                else:
                    arn = f"arn:aws:rds:{clients['region']}:{clients['account_id']}:db:{resource_id}"
                clients["rds"].add_tags_to_resource(ResourceName=arn, Tags=tags)

            case "lambda":
                arn = f"arn:aws:lambda:{clients['region']}:{clients['account_id']}:function:{resource_id}"
                clients["lambda"].tag_resource(
                    Resource=arn, Tags={tag["Key"]: tag["Value"] for tag in tags}
                )

            case "eks":
                # EKS can be cluster or nodegroup
                if resource_type == "eks:cluster":
                    arn = f"arn:aws:eks:{clients['region']}:{clients['account_id']}:cluster/{resource_id}"
                elif resource_type == "eks:nodegroup":
                    # resource_id format: "cluster-name/nodegroup-name"
                    cluster_name, nodegroup_name = resource_id.split("/", 1)
                    arn = f"arn:aws:eks:{clients['region']}:{clients['account_id']}:nodegroup/{cluster_name}/{nodegroup_name}"
                else:
                    arn = f"arn:aws:eks:{clients['region']}:{clients['account_id']}:cluster/{resource_id}"  # Fallback for other EKS resources
                clients["eks"].tag_resource(
                    resourceArn=arn, tags={tag["Key"]: tag["Value"] for tag in tags}
                )

            case "elbv2":
                # For ELB, resource_id is already the full ARN
                clients["elbv2"].add_tags(ResourceArns=[resource_id], Tags=tags)

            case "dynamodb":
                clients["dynamodb"].tag_resource(
                    ResourceArn=f"arn:aws:dynamodb:{clients['region']}:{clients['account_id']}:table/{resource_id}",
                    Tags=tags,
                )

            case "kms":
                # KMS uses key-value pairs
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["kms"].tag_resource(
                    KeyId=resource_id,
                    Tags=[{"TagKey": k, "TagValue": v} for k, v in tag_dict.items()],
                )

            case "secretsmanager":
                # Secrets Manager expects ARN and key-value tags
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["secretsmanager"].tag_resource(
                    SecretId=resource_id,
                    Tags=[{"Key": k, "Value": v} for k, v in tag_dict.items()],
                )

            case "sns":
                # SNS expects ARN and key-value tags
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["sns"].tag_resource(
                    ResourceArn=resource_id,
                    Tags=[{"Key": k, "Value": v} for k, v in tag_dict.items()],
                )

            case "sqs":
                # SQS expects queue URL and key-value dict
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["sqs"].tag_queue(QueueUrl=resource_id, Tags=tag_dict)

            case "cloudwatch":
                if resource_type == "cloudwatch:loggroup":
                    tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                    clients["cloudwatch-logs"].tag_log_group(
                        logGroupName=resource_id, tags=tag_dict
                    )
                else:
                    tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                    clients["cloudwatch"].tag_resource(
                        ResourceARN=f"arn:aws:cloudwatch:{clients['region']}:{clients['account_id']}:alarm:{resource_id}",
                        Tags=[{"Key": k, "Value": v} for k, v in tag_dict.items()],
                    )

            case "route53":
                # Route 53 uses resource ID and key-value tags
                clients["route53"].change_tags_for_resource(
                    ResourceType="hostedzone",
                    ResourceId=resource_id.replace("/hostedzone/", ""),
                    AddTags=[
                        {"Key": tag["Key"], "Value": tag["Value"]} for tag in tags
                    ],
                )

            case "apigateway":
                # API Gateway uses resource ARN
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["apigateway"].tag_resource(
                    resourceArn=f"arn:aws:apigateway:{clients['region']}::/restapis/{resource_id}",
                    tags=tag_dict,
                )

            case "ecs":
                # ECS expects ARN and key-value tags
                if resource_type == "ecs:cluster":
                    cluster_arn = f"arn:aws:ecs:{clients['region']}:{clients['account_id']}:cluster/{resource_id}"
                else:
                    cluster_arn = f"arn:aws:ecs:{clients['region']}:{clients['account_id']}:service/{resource_id}"
                clients["ecs"].tag_resource(
                    resourceArn=cluster_arn,
                    tags=[{"key": tag["Key"], "value": tag["Value"]} for tag in tags],
                )

            case "ecr":
                # ECR expects ARN and key-value tags
                clients["ecr"].tag_resource(
                    resourceArn=f"arn:aws:ecr:{clients['region']}:{clients['account_id']}:repository/{resource_id}",
                    tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                )

            case "stepfunctions":
                # Step Functions expects ARN
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["stepfunctions"].tag_resource(
                    resourceArn=resource_id,
                    tags=[{"key": k, "value": v} for k, v in tag_dict.items()],
                )

            case "cloudformation":
                # CloudFormation expects stack name and key-value tags
                clients["cloudformation"].update_stack(
                    StackName=resource_id,
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                    UsePreviousTemplate=True,
                )

            case "efs":
                # EFS expects file system ID and key-value tags
                clients["efs"].tag_resource(
                    ResourceId=resource_id,
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                )

            case "opensearch":
                # OpenSearch expects domain ARN
                clients["opensearch"].add_tags(
                    ARN=f"arn:aws:es:{clients['region']}:{clients['account_id']}:domain/{resource_id}",
                    TagList=[
                        {"Key": tag["Key"], "Value": tag["Value"]} for tag in tags
                    ],
                )

            case "redshift":
                # Redshift expects resource name and key-value tags
                clients["redshift"].create_tags(
                    ResourceName=f"arn:aws:redshift:{clients['region']}:{clients['account_id']}:cluster:{resource_id}",
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                )

            case "cognito-idp":
                # Cognito User Pool expects ARN
                clients["cognito-idp"].tag_resource(
                    ResourceArn=f"arn:aws:cognito-idp:{clients['region']}:{clients['account_id']}:userpool/{resource_id}",
                    Tags={tag["Key"]: tag["Value"] for tag in tags},
                )

            case "cognito-identity":
                # Cognito Identity Pool expects ARN
                clients["cognito-identity"].tag_resource(
                    ResourceArn=f"arn:aws:cognito-identity:{clients['region']}:{clients['account_id']}:identitypool/{resource_id}",
                    Tags={tag["Key"]: tag["Value"] for tag in tags},
                )

            case "amplify":
                # Amplify expects app ARN
                clients["amplify"].tag_resource(
                    resourceArn=f"arn:aws:amplify:{clients['region']}:{clients['account_id']}:apps/{resource_id}",
                    tags={tag["Key"]: tag["Value"] for tag in tags},
                )

            case "glue":
                # Glue expects ARN and key-value tags
                if resource_type == "glue:database":
                    resource_arn = f"arn:aws:glue:{clients['region']}:{clients['account_id']}:database/{resource_id}"
                else:
                    resource_arn = f"arn:aws:glue:{clients['region']}:{clients['account_id']}:table/{resource_id}"
                clients["glue"].tag_resource(
                    ResourceArn=resource_arn,
                    TagsToAdd={tag["Key"]: tag["Value"] for tag in tags},
                )

            case "iam":
                # IAM expects ARN and key-value tags
                clients["iam"].tag_resource(
                    ResourceArn=resource_id,
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                )

            case _:
                logger.warning(f"Unsupported event source: {eventsource}")
                return False

        tag_summary = ", ".join([f"{tag['Key']}:{tag['Value']}" for tag in tags])
        logger.info(f"✅ Tagged {resource_type}:{resource_id} with [{tag_summary}]")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to tag {resource_type}:{resource_id}: {e}")
        return False


def get_supported_events():
    """Get list of supported events - simple!"""
    events = []
    for eventsource, event_configs in SERVICE_CONFIGS.items():
        events.extend(event_configs.keys())
    return events
