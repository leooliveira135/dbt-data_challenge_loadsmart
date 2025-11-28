terraform {
	required_providers {
		aws = {
			source  = "hashicorp/aws"
			version = "~> 5.0"
		}
	    pgp = {
	      source = "ekristen/pgp"
	      version = "0.2.4"
	    }
	}
}

data "aws_caller_identity" "current" {}

provider "aws" {
	region = var.aws_region
}

locals {
  users = {
    "terraform-aws" = {
      name  = "Terraform AWS User"
      email = "terraform_aws@example.com"
    } 
  }
}

resource "aws_iam_user" "create_user" {
  for_each = local.users

  name = "terraform-aws"
  force_destroy = false
}

resource "aws_iam_access_key" "user_access_key" {
  for_each = local.users
  
  user       = each.key
  depends_on = [aws_iam_user.create_user]
}

resource "pgp_key" "user_login_key" {
  for_each = local.users

  name    = each.value.name
  email   = each.value.email
  comment = "PGP Key for ${each.value.name}"
}

resource "aws_iam_user_login_profile" "user_login" {
  for_each = local.users

  user                    = each.key
  pgp_key                 = pgp_key.user_login_key[each.key].public_key_base64
  password_reset_required = true

  depends_on = [aws_iam_user.create_user, pgp_key.user_login_key]
}

data "pgp_decrypt" "user_password_decrypt" {
  for_each = local.users

  ciphertext          = aws_iam_user_login_profile.user_login[each.key].encrypted_password
  ciphertext_encoding = "base64"
  private_key         = pgp_key.user_login_key[each.key].private_key
}

resource "aws_s3_bucket" "raw" {
  bucket = "data-challenge-loadsmart-raw"

  tags = {
    Name = "data-challenge-loadsmart-raw"
    Env = "dev"
    Tier = "raw"
  }
}

resource "aws_s3_object" "data_challenge" {
  bucket = aws_s3_bucket.raw.id
  key    = "data/2025_data_challenge_loadsmart.csv"
  source = "${path.module}/2025_data_challenge_ae.csv"
  etag   = filemd5("${path.module}/2025_data_challenge_ae.csv")
}

resource "aws_s3_bucket" "stg" {
  bucket = "data-challenge-loadsmart-stg"

  tags = {
    Name = "data-challenge-loadsmart-stg"
    Env = "stg"
    Tier = "staging"
  }
}

resource "aws_s3_bucket" "prd" {
  bucket = "data-challenge-loadsmart"

  tags = {
    Name = "data-challenge-loadsmart"
    Env = "prd"
    Tier = "production"
  }
}

resource "aws_athena_data_catalog" "aws_star_schema" {
  name        = "aws_star_schema"
  description = "Loadsmart Glue based Data Catalog"
  type        = "GLUE"

  parameters = {
    "catalog-id" = data.aws_caller_identity.current.account_id
  }
}

# IAM Policy for Glue and Athena access
resource "aws_iam_policy" "athena_glue_policy" {
  name        = "athena-glue-dbt-policy"
  description = "Policy for dbt to access Glue and Athena"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:CreateDatabase",
          "glue:UpdateDatabase",
          "glue:DeleteDatabase",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:BatchCreatePartition",
          "glue:UpdatePartition",
          "glue:DeletePartition",
          "glue:BatchDeletePartition"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:StopQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:ListQueryExecutions",
          "athena:GetWorkGroup",
          "athena:ListWorkGroups"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketVersioning",
          "s3:ListBucketVersions"
        ]
        Resource = [
          "arn:aws:s3:::data-challenge-loadsmart-raw",
          "arn:aws:s3:::data-challenge-loadsmart-raw/*",
          "arn:aws:s3:::data-challenge-loadsmart-stg",
          "arn:aws:s3:::data-challenge-loadsmart-stg/*",
          "arn:aws:s3:::data-challenge-loadsmart",
          "arn:aws:s3:::data-challenge-loadsmart/*"
        ]
      }
    ]
  })
}

# Attach policy to the terraform-aws user
resource "aws_iam_user_policy_attachment" "terraform_aws_policy" {
  for_each = local.users

  user       = aws_iam_user.create_user[each.key].name
  policy_arn = aws_iam_policy.athena_glue_policy.arn
}
