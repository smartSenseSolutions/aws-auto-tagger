# TODO: Test ECS resources for aws-tagger
# Events to test: CreateCluster, CreateService

# ECS Cluster
resource "aws_ecs_cluster" "test" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${local.name_prefix}-ecs-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "test" {
  family                   = "${local.name_prefix}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512

  container_definitions = jsonencode([
    {
      name  = "nginx"
      image = "nginx:latest"
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
    }
  ])

  tags = {
    Name = "${local.name_prefix}-ecs-task-definition"
  }
}

# ECS Service
resource "aws_ecs_service" "test" {
  name            = "${local.name_prefix}-service"
  cluster         = aws_ecs_cluster.test.id
  task_definition = aws_ecs_task_definition.test.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.main.id, aws_subnet.secondary.id]
    security_groups  = [aws_security_group.test.id]
    assign_public_ip = true
  }

  tags = {
    Name = "${local.name_prefix}-ecs-service"
  }
}

# ECS Capacity Provider
resource "aws_ecs_capacity_provider" "test" {
  name = "${local.name_prefix}-capacity-provider"

  auto_scaling_group_provider {
    auto_scaling_group_arn = aws_autoscaling_group.test.arn
  }

  tags = {
    Name = "${local.name_prefix}-ecs-capacity-provider"
  }
}

# Auto Scaling Group for ECS
resource "aws_autoscaling_group" "test" {
  name                = "${local.name_prefix}-asg"
  desired_capacity    = 0
  min_size            = 0
  max_size            = 1
  target_group_arns   = [aws_lb_target_group.test.arn]
  vpc_zone_identifier = [aws_subnet.main.id, aws_subnet.secondary.id]

  launch_template {
    id      = aws_launch_template.test.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-asg"
    propagate_at_launch = true
  }
}

# Launch Template for ECS
resource "aws_launch_template" "test" {
  name_prefix   = "${local.name_prefix}-lt"
  image_id      = "ami-0c02fb55956c7d316"
  instance_type = "t3.micro"

  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.test.id]
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              echo "ECS_CLUSTER=${aws_ecs_cluster.test.name}" >> /etc/ecs/ecs.config
              EOF
  )

  iam_instance_profile {
    name = aws_iam_instance_profile.test.name
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${local.name_prefix}-launch-template"
    }
  }
}

# IAM Instance Profile for ECS
resource "aws_iam_instance_profile" "test" {
  name = "${local.name_prefix}-instance-profile"
  role = aws_iam_role.ecs_instance_role.name
}

# IAM Role for ECS Instances
resource "aws_iam_role" "ecs_instance_role" {
  name = "${local.name_prefix}-ecs-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role Policy Attachment for ECS Instances
resource "aws_iam_role_policy_attachment" "ecs_instance_role_policy" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}
