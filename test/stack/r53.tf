# TODO: Test Route53 resources for aws-tagger
# Events to test: CreateHostedZone

# Route53 Hosted Zone
resource "aws_route53_zone" "test" {
  name = "awstagger-test.com"

  tags = {
    Name = "${local.name_prefix}-route53-zone"
  }
}

# Route53 Record
resource "aws_route53_record" "test" {
  zone_id = aws_route53_zone.test.zone_id
  name    = "www.awstagger-test.com"
  type    = "A"
  ttl     = "300"

  records = ["192.168.1.1"]
}

# Route53 Health Check
resource "aws_route53_health_check" "test" {
  fqdn              = "www.awstagger-test.com"
  port              = 80
  type              = "HTTP"
  resource_path     = "/"
  failure_threshold = "3"
  request_interval  = "30"

  tags = {
    Name = "${local.name_prefix}-route53-health-check"
  }
}
