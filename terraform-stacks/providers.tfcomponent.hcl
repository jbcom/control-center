# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

required_providers {
  github = {
    source  = "integrations/github"
    version = "~> 6.0"
  }
}

provider "github" "jbcom" {
  config {
    owner = "jbcom"
    token = var.github_token
  }
}
