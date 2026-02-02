# TODO: Test ELBV2 resources for aws-tagger
# Events to test: CreateLoadBalancer, CreateTargetGroup

# Application Load Balancer
resource "aws_lb" "test" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.test.id]
  subnets            = [aws_subnet.main.id, aws_subnet.secondary.id]

  enable_deletion_protection = false

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

# ALB Target Group
resource "aws_lb_target_group" "test" {
  name     = "${local.name_prefix}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${local.name_prefix}-target-group"
  }
}

# ALB Listener
resource "aws_lb_listener" "test" {
  load_balancer_arn = aws_lb.test.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.test.arn
  }
}

# Network Load Balancer
resource "aws_lb" "nlb" {
  name               = "${local.name_prefix}-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = [aws_subnet.main.id, aws_subnet.secondary.id]

  enable_deletion_protection = false

  tags = {
    Name = "${local.name_prefix}-nlb"
  }
}

# NLB Target Group
resource "aws_lb_target_group" "nlb" {
  name     = "${local.name_prefix}-nlb-tg"
  port     = 80
  protocol = "TCP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    protocol            = "TCP"
    timeout             = 10
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${local.name_prefix}-nlb-target-group"
  }
}
