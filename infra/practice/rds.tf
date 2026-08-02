# RDS PostgreSQL (practice / free-tier oriented).
#
# BEFORE apply, set a master password (do NOT commit real secrets):
#   PowerShell:  $env:TF_VAR_db_password = "YourStrongPassword1"
#   bash:        export TF_VAR_db_password='YourStrongPassword1'
#
# Then:
#   terraform plan
#   terraform apply

variable "db_password" {
  description = "RDS master password (set via TF_VAR_db_password)"
  type        = string
  sensitive   = true
}

variable "db_publicly_accessible" {
  description = "If true, DB gets a public IP (easy for laptop learning; turn off later)"
  type        = bool
  default     = true
}

variable "db_allowed_cidr" {
  description = "Who can connect on 5432. Practice default is open; tighten to your IP/32 ASAP."
  type        = string
  default     = "0.0.0.0/0"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_db_subnet_group" "careplan" {
  name       = "careplan-practice-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-rds-exercise"
  }
}

resource "aws_security_group" "careplan_rds" {
  name        = "careplan-practice-rds-sg"
  description = "Practice SG for CarePlan RDS Postgres"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Postgres"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.db_allowed_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-rds-exercise"
  }
}

resource "aws_db_instance" "careplan" {
  identifier = "careplan-practice"

  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp2"

  db_name  = "careplan"
  username = "careplan"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.careplan.name
  vpc_security_group_ids = [aws_security_group.careplan_rds.id]
  publicly_accessible    = var.db_publicly_accessible

  # Free-tier friendly: single-AZ
  multi_az = false

  # Learning convenience — for real envs set skip_final_snapshot=false
  skip_final_snapshot = true
  deletion_protection = false

  backup_retention_period = 1
  apply_immediately       = true

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-rds-exercise"
  }
}

output "rds_endpoint" {
  description = "Hostname:port for Postgres clients"
  value       = aws_db_instance.careplan.endpoint
}

output "rds_address" {
  description = "Hostname only"
  value       = aws_db_instance.careplan.address
}

output "rds_port" {
  value = aws_db_instance.careplan.port
}

output "rds_db_name" {
  value = aws_db_instance.careplan.db_name
}

output "rds_username" {
  value = aws_db_instance.careplan.username
}
