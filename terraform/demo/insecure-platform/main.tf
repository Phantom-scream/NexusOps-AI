terraform {
  required_version = ">= 1.5.0"
}

resource "aws_security_group_rule" "ssh_world" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

resource "aws_db_instance" "orders" {
  identifier          = "orders-prod"
  instance_type       = "db.t3.medium"
  publicly_accessible = true
  storage_encrypted   = false
  skip_final_snapshot = true
  password            = "super-secret-password"
}

resource "aws_iam_policy" "platform_admin" {
  name   = "platform-admin"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

resource "aws_s3_bucket" "logs" {
  bucket = "nexusops-prod-logs"
  acl    = "public-read"
}
