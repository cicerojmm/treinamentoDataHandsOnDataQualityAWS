terraform {
  backend "s3" {
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Project     = "DataHandsOn-DQ"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DataTeam"
      Application = "DataQuality"
    }
  }
}
