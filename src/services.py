"""
Simple Service Configurations - Easy to extend

Adding a new AWS service is as simple as adding a few lines here.
Now using JMESPath for much cleaner resource extraction!
"""

from botocore.exceptions import ClientError

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
        "CreateNatGateway": {
            "eventsource": "ec2",
            "resource_type": "ec2:natgateway",
            "section": "responseElements",
            "jmespath": "natGateway.natGatewayId",
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
            "jmespath": "cluster.name || cluster.clusterName",
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
    },
    "secretsmanager": {
        "CreateSecret": {
            "eventsource": "secretsmanager",
            "resource_type": "secretsmanager:secret",
            "section": "responseElements",
            "jmespath": "arn || aRN",
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
    "logs": {
        "CreateLogGroup": {
            "eventsource": "logs",
            "resource_type": "logs:loggroup",
            "section": "requestParameters",
            "jmespath": "logGroupName",
        }
    },
    "cloudwatch": {
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
            "jmespath": "cluster.clusterArn",
        },
        "CreateService": {
            "eventsource": "ecs",
            "resource_type": "ecs:service",
            "section": "responseElements",
            "jmespath": "service.serviceArn",
        },
    },
    "autoscaling": {
        "CreateAutoScalingGroup": {
            "eventsource": "autoscaling",
            "resource_type": "autoscaling:group",
            "section": "requestParameters",
            "jmespath": "autoScalingGroupName",
        }
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
        "CreateTable": {
            "eventsource": "glue",
            "resource_type": "glue:table",
            "section": "requestParameters",
            "jmespath": "join('/', [databaseName, tableInput.name])",
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
            "resource_type": "bedrock:customization-job",
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
    "kafka": {
        "CreateClusterV2": {
            "eventsource": "kafka",
            "resource_type": "kafka:cluster",
            "section": "responseElements",
            "jmespath": "clusterArn",
        },
        "CreateCluster": {
            "eventsource": "kafka",
            "resource_type": "kafka:cluster",
            "section": "responseElements",
            "jmespath": "clusterArn",
        },
    },
    "kinesis": {
        "CreateStream": {
            "eventsource": "kinesis",
            "resource_type": "kinesis:stream",
            "section": "requestParameters",
            "jmespath": "streamName",
        }
    },
    "batch": {
        "CreateComputeEnvironment": {
            "eventsource": "batch",
            "resource_type": "batch:computeenvironment",
            "section": "responseElements",
            "jmespath": "computeEnvironmentArn",
        },
        "CreateJobQueue": {
            "eventsource": "batch",
            "resource_type": "batch:jobqueue",
            "section": "responseElements",
            "jmespath": "jobQueueArn",
        },
    },
    "elasticache": {
        "CreateReplicationGroup": {
            "eventsource": "elasticache",
            "resource_type": "elasticache:replicationgroup",
            "section": "requestParameters",
            "jmespath": "replicationGroupId",
        },
        "CreateCacheCluster": {
            "eventsource": "elasticache",
            "resource_type": "elasticache:cluster",
            "section": "requestParameters",
            "jmespath": "cacheClusterId",
        },
    },
    "memorydb": {
        "CreateCluster": {
            "eventsource": "memorydb",
            "resource_type": "memorydb:cluster",
            "section": "responseElements",
            "jmespath": "cluster.aRN",
        }
    },
    "iam": {
        "CreateRole": {
            "eventsource": "iam",
            "resource_type": "iam:role",
            "section": "responseElements",
            "jmespath": "role.roleName",
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


# CloudTrail eventSource prefix (`<prefix>.amazonaws.com`) when it differs from the SERVICE_CONFIGS key
CLOUDTRAIL_SOURCES = {
    "cloudwatch": "monitoring",
    "stepfunctions": "states",
    "efs": "elasticfilesystem",
    "opensearch": "es",
    "elbv2": "elasticloadbalancing",
}


def get_service_config(event_name: str, event_source: str = "") -> dict:
    """Get service configuration for an event.

    Event names are not unique across services (e.g. `CreateCluster` exists for
    EKS, ECS, Redshift, MSK and MemoryDB), so the CloudTrail `EventSource`
    (e.g. `ecs.amazonaws.com`) picks the service when given.
    """
    prefix = event_source.split(".", 1)[0]
    for eventsource, events in SERVICE_CONFIGS.items():
        if event_name not in events:
            continue
        if not prefix or prefix == CLOUDTRAIL_SOURCES.get(eventsource, eventsource):
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
    owner_email: str | None = None,
) -> bool:
    """Tag a resource - simplified logic"""
    logger.debug(f"Tagging: {resource_type}:{resource_id}")
    try:
        # Prepare tags
        tags = [{"Key": config.owner_tag_name, "Value": username}]

        # Add creation time tag if available
        if creation_time:
            tags.append({"Key": config.creation_time_tag_name, "Value": creation_time})

        if owner_email:
            tags.append({"Key": config.owner_email_tag_name, "Value": owner_email})

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
                # put_bucket_tagging replaces the whole set: merge so existing tags survive
                try:
                    existing = clients["s3"].get_bucket_tagging(Bucket=resource_id)
                except ClientError as e:
                    if e.response["Error"]["Code"] != "NoSuchTagSet":
                        raise
                    existing = {}
                merged = {t["Key"]: t["Value"] for t in existing.get("TagSet", [])}
                merged |= {t["Key"]: t["Value"] for t in tags}
                clients["s3"].put_bucket_tagging(
                    Bucket=resource_id,
                    Tagging={
                        "TagSet": [{"Key": k, "Value": v} for k, v in merged.items()]
                    },
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

            case "logs":
                clients["logs"].tag_resource(
                    resourceArn=f"arn:aws:logs:{clients['region']}:{clients['account_id']}:log-group:{resource_id}",
                    tags={tag["Key"]: tag["Value"] for tag in tags},
                )

            case "cloudwatch":
                clients["cloudwatch"].tag_resource(
                    ResourceARN=f"arn:aws:cloudwatch:{clients['region']}:{clients['account_id']}:alarm:{resource_id}",
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
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
                kind = "apikeys" if resource_type == "apigateway:apikey" else "restapis"
                clients["apigateway"].tag_resource(
                    resourceArn=f"arn:aws:apigateway:{clients['region']}::/{kind}/{resource_id}",
                    tags=tag_dict,
                )

            case "ecs":
                # resource_id is the cluster/service ARN from the response (handles the long ARN format)
                clients["ecs"].tag_resource(
                    resourceArn=resource_id,
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

            case "autoscaling":
                # Auto Scaling Groups use a distinct tag shape (ResourceId/ResourceType/PropagateAtLaunch)
                clients["autoscaling"].create_or_update_tags(
                    Tags=[
                        {
                            "ResourceId": resource_id,
                            "ResourceType": "auto-scaling-group",
                            "Key": tag["Key"],
                            "Value": tag["Value"],
                            "PropagateAtLaunch": True,
                        }
                        for tag in tags
                    ]
                )

            case "kinesis":
                # Kinesis expects stream name and key-value tags
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["kinesis"].add_tags_to_stream(
                    StreamName=resource_id, Tags=tag_dict
                )

            case "batch":
                # AWS Batch expects ARN and key-value tags
                tag_dict = {tag["Key"]: tag["Value"] for tag in tags}
                clients["batch"].tag_resource(resourceArn=resource_id, tags=tag_dict)

            case "elasticache":
                # ElastiCache expects ARN; resource_id is the cluster/replication group ID
                kind = (
                    "replicationgroup"
                    if resource_type == "elasticache:replicationgroup"
                    else "cluster"
                )
                clients["elasticache"].add_tags_to_resource(
                    ResourceName=f"arn:aws:elasticache:{clients['region']}:{clients['account_id']}:{kind}:{resource_id}",
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                )

            case "kafka":
                # MSK expects ARN and key-value tags
                clients["kafka"].tag_resource(
                    ResourceArn=resource_id,
                    Tags={tag["Key"]: tag["Value"] for tag in tags},
                )

            case "memorydb":
                # MemoryDB expects ARN and key-value tags
                clients["memorydb"].tag_resource(
                    ResourceArn=resource_id,
                    Tags=[{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags],
                )

            case "iam":
                # IAM has one tag API per resource type
                iam_tags = [{"Key": tag["Key"], "Value": tag["Value"]} for tag in tags]
                if resource_type == "iam:role":
                    clients["iam"].tag_role(RoleName=resource_id, Tags=iam_tags)
                elif resource_type == "iam:user":
                    clients["iam"].tag_user(UserName=resource_id, Tags=iam_tags)
                else:
                    clients["iam"].tag_policy(PolicyArn=resource_id, Tags=iam_tags)

            case "bedrock":
                clients["bedrock"].tag_resource(
                    resourceARN=resource_id,
                    tags=[{"key": tag["Key"], "value": tag["Value"]} for tag in tags],
                )

            case "cloudfront":
                # CloudFront is global: no region in the ARN
                clients["cloudfront"].tag_resource(
                    Resource=f"arn:aws:cloudfront::{clients['account_id']}:distribution/{resource_id}",
                    Tags={
                        "Items": [
                            {"Key": tag["Key"], "Value": tag["Value"]} for tag in tags
                        ]
                    },
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
