package nexusops.terraform.security

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_security_group_rule"
    resource.change.after.cidr_blocks[_] == "0.0.0.0/0"
    resource.change.after.from_port == 22
    msg := sprintf("CRITICAL: SSH open to the internet in resource %s", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_s3_bucket"
    resource.change.after.acl == "public-read"
    msg := sprintf("HIGH: S3 bucket %s has public-read ACL", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_db_instance"
    resource.change.after.publicly_accessible == true
    msg := sprintf("CRITICAL: RDS instance %s is publicly accessible", [resource.address])
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_db_instance"
    not resource.change.after.storage_encrypted
    msg := sprintf("HIGH: RDS instance %s has unencrypted storage", [resource.address])
}

warn[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_db_instance"
    not resource.change.after.deletion_protection
    msg := sprintf("MEDIUM: RDS instance %s has deletion protection disabled", [resource.address])
}
