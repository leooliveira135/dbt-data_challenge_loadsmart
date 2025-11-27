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

resource "aws_athena_data_catalog" "aws-star-schema" {
  name        = "aws-star-schema"
  description = "Loadsmart Glue based Data Catalog"
  type        = "GLUE"

  parameters = {
    "catalog-id" = data.aws_caller_identity.current.account_id
  }
}
