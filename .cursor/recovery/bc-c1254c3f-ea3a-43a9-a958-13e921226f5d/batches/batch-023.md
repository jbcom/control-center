# Messages 221-230

## [221] 👤 USER

That token has full admin so there is ZERO else I can grant

---

## [222] 🤖 ASSISTANT

They're an admin! Let me check the org's Actions permissions:

---

## [223] 👤 USER

There try again

---

## [224] 👤 USER

I reser permissions

---

## [225] 🤖 ASSISTANT

Now let me sync all the secrets:

---

## [226] 👤 USER

Looks like it's just a usage thing by now

---

## [227] 👤 USER

Also. Making sure we set to private always

---

## [228] 👤 USER

https://github.com/fsc-internal-tooling-administration/terraform-organization-administration/actions/runs/19720454286/job/56501806729 good thing is WHILE you wait for that you can pivot. I know what to work on immediately next. We can't use OIDC auth for the AWS workflow for this one. If you review terraform-modules terraform/terraform/terraform-pipeline and trace the workflow variable for disabling OIDC auth in workflow config it should ultimately be handled by a terraform_data_sources.py library module. If y you look at it it you SHOULD be able between that and the terraform pipeline module itself trsce exactly what you need to MANUALLY change over in the workflow to make an EFFECTIVE change in the workflow to MATCH how it would look . Basically we're gonna set oidc to false in the workflow config merge in generator/main.tf AND make an effective update to the actual generator workflow to unblock kit because OIDC is ONLY setup for the FlipsideCrypto  org. Once that is done we should be totally set to run the workflow in that org admin repo

---

## [229] 🤖 ASSISTANT

Let me trace the OIDC auth configuration through terraform-modules:

---

## [230] 🤖 ASSISTANT

Now I understand the pattern. When `use_oidc_auth = false`:
- Uses `EXTERNAL_CI_ACCESS_KEY` and `EXTERNAL_CI_SECRET_KEY` instead of `AWS_OIDC_ROLE_ARN`

Let me check the terraform-organization-administration repo:

---

