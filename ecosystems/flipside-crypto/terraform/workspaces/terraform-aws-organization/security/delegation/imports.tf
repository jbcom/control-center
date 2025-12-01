# Import existing AWS Security Delegation resources

# Delegated administrators
import {
  to = aws_organizations_delegated_administrator.this["security:config.amazonaws.com"]
  id = "383686502118:config.amazonaws.com"
}

import {
  to = aws_organizations_delegated_administrator.this["security:guardduty.amazonaws.com"]
  id = "383686502118:guardduty.amazonaws.com"
}

import {
  to = aws_organizations_delegated_administrator.this["log_archive:config.amazonaws.com"]
  id = "850178735765:config.amazonaws.com"
}

import {
  to = aws_organizations_delegated_administrator.this["transit:inspector2.amazonaws.com"]
  id = "734995239048:inspector2.amazonaws.com"
}

import {
  to = aws_organizations_delegated_administrator.this["transit:ipam.amazonaws.com"]
  id = "734995239048:ipam.amazonaws.com"
}

import {
  to = aws_organizations_delegated_administrator.this["transit:sso.amazonaws.com"]
  id = "734995239048:sso.amazonaws.com"
}
