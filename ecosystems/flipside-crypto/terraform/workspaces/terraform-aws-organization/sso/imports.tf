# ============================================================================
# Import existing SSO groups - Only actual Google Workspace group emails
# ============================================================================

import {
  to = aws_identitystore_group.sso_groups["it@flipsidecrypto.com"]
  id = "d-906768254f/b4f80448-5051-7009-e7da-5f2e3df30cd2"
}

import {
  to = aws_identitystore_group.sso_groups["engineers@flipsidecrypto.com"]
  id = "d-906768254f/c428c448-e0d1-70a5-bcc4-2e4b2f374942"
}

import {
  to = aws_identitystore_group.sso_groups["leads@flipsidecrypto.com"]
  id = "d-906768254f/c4685438-70f1-700e-e603-675d482864c1"
}

import {
  to = aws_identitystore_group.sso_groups["ir@flipsidecrypto.com"]
  id = "d-906768254f/c4782458-30a1-7084-0d20-9eea4377f28b"
}

import {
  to = aws_identitystore_group.sso_groups["data-partnerships@flipsidecrypto.com"]
  id = "d-906768254f/c4e834c8-3001-70fc-12a1-ab93a00616b2"
}

import {
  to = aws_identitystore_group.sso_groups["branding@flipsidecrypto.com"]
  id = "d-906768254f/d4881458-7061-7003-41d2-2aaebe3ec7d7"
}

import {
  to = aws_identitystore_group.sso_groups["trading@flipsidecrypto.com"]
  id = "d-906768254f/d498f468-4001-704e-a50c-94329278eddf"
}

import {
  to = aws_identitystore_group.sso_groups["analytics-requests@flipsidecrypto.com"]
  id = "d-906768254f/d4e88468-40f1-70dc-f575-42f7cf52d01c"
}

import {
  to = aws_identitystore_group.sso_groups["billing@flipsidecrypto.com"]
  id = "d-906768254f/e418b408-00f1-7053-844d-731c0ecdd509"
}

import {
  to = aws_identitystore_group.sso_groups["analytics@flipsidecrypto.com"]
  id = "d-906768254f/e45814e8-f051-7081-0d7c-7b755681219d"
}

import {
  to = aws_identitystore_group.sso_groups["info@flipsidecrypto.com"]
  id = "d-906768254f/e468b448-e0a1-706c-a763-0de985c6ad72"
}

import {
  to = aws_identitystore_group.sso_groups["governance@flipsidecrypto.com"]
  id = "d-906768254f/e4788438-0051-70a5-0458-2b809765813b"
}

import {
  to = aws_identitystore_group.sso_groups["api@flipsidecrypto.com"]
  id = "d-906768254f/e478d4d8-90d1-70e0-aaf8-cf95cfa029e6"
}

import {
  to = aws_identitystore_group.sso_groups["product-eng@flipsidecrypto.com"]
  id = "d-906768254f/e4c8d418-1011-700d-c26a-f548e2a4d263"
}

import {
  to = aws_identitystore_group.sso_groups["events@flipsidecrypto.com"]
  id = "d-906768254f/f42814b8-a0e1-7008-0c76-0bc8c2159e4c"
}

import {
  to = aws_identitystore_group.sso_groups["engineering@flipsidecrypto.com"]
  id = "d-906768254f/f498c488-b001-707d-3bc0-e31643d0e4bc"
}

import {
  to = aws_identitystore_group.sso_groups["team@flipsidecrypto.com"]
  id = "d-906768254f/f4a84488-80c1-702c-d935-bff6374bddf0"
}

import {
  to = aws_identitystore_group.sso_groups["network@flipsidecrypto.com"]
  id = "d-906768254f/f4b874f8-4081-704d-97cd-ce6182143371"
}

# ============================================================================
# Permission sets, inline policies, and managed policies are migrated via moved.tf
# ============================================================================

# Permission sets, inline policies, and managed policy attachments
# are migrated via moved.tf, not imported
