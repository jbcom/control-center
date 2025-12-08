# Copyright (c) jbcom
# SPDX-License-Identifier: MIT

# Import existing repository into state
# The 'id' is the repository name
import {
  to = github_repository.this
  id = var.name
}

# Import existing branch protection
# The 'id' format is "repository:branch"
import {
  to = github_branch_protection.main
  id = "${var.name}:${var.default_branch}"
}

# Note: github_repository_security_and_analysis and github_repository_pages
# will be created fresh (they don't support import or will auto-adopt)
