# TODO: Test RDS resources for aws-tagger
# Events to test: CreateDBInstance, CreateDBCluster

# RDS Subnet Group
resource "aws_db_subnet_group" "test" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = [aws_subnet.main.id, aws_subnet.secondary.id]

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

# RDS Parameter Group
resource "aws_db_parameter_group" "test" {
  family = "mysql8.0"
  name   = "${local.name_prefix}-db-parameter-group"

  tags = {
    Name = "${local.name_prefix}-db-parameter-group"
  }
}

# RDS Instance
resource "aws_db_instance" "test" {
  identifier = "${local.name_prefix}-db-instance"

  engine         = local.rds.engine
  engine_version = local.rds.engine_version
  instance_class = local.rds.instance_type

  allocated_storage = local.rds.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "testdb"
  username = "admin"
  password = "password123"

  db_subnet_group_name   = aws_db_subnet_group.test.name
  parameter_group_name   = aws_db_parameter_group.test.name
  vpc_security_group_ids = [aws_security_group.test.id]

  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Name = "${local.name_prefix}-rds-instance"
  }
}

# RDS Cluster
resource "aws_rds_cluster" "test" {
  cluster_identifier = "${local.name_prefix}-db-cluster"

  engine         = "aurora-mysql"
  engine_version = "8.0"

  database_name   = "testdb"
  master_username = "admin"
  master_password = "password123"

  db_subnet_group_name   = aws_db_subnet_group.test.name
  vpc_security_group_ids = [aws_security_group.test.id]

  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Name = "${local.name_prefix}-rds-cluster"
  }
}

# RDS Cluster Instance
resource "aws_rds_cluster_instance" "test" {
  identifier         = "${local.name_prefix}-db-cluster-instance"
  cluster_identifier = aws_rds_cluster.test.id
  instance_class     = "db.t3.micro"
  engine             = aws_rds_cluster.test.engine

  tags = {
    Name = "${local.name_prefix}-rds-cluster-instance"
  }
}
