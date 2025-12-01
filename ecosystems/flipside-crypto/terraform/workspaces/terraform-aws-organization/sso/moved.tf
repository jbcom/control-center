# ============================================================================
# Moved blocks - Migrate permission sets from module to individual resources
# ============================================================================

# Permission Sets
moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["AWSAdministratorAccess"]
  to   = aws_ssoadmin_permission_set.aws_administrator_access
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["EngineeringAccess"]
  to   = aws_ssoadmin_permission_set.engineering_access
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["AWSOrganizationsFullAccess"]
  to   = aws_ssoadmin_permission_set.aws_organizations_full_access
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["AWSPowerUserAccess"]
  to   = aws_ssoadmin_permission_set.aws_power_user_access
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["AWSReadOnlyAccess"]
  to   = aws_ssoadmin_permission_set.aws_read_only_access
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["AWSServiceCatalogAdminFullAccess"]
  to   = aws_ssoadmin_permission_set.aws_service_catalog_admin
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["AWSServiceCatalogEndUserAccess"]
  to   = aws_ssoadmin_permission_set.aws_service_catalog_end_user
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["BillingAccess"]
  to   = aws_ssoadmin_permission_set.billing_access
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["FlipsideDiscordMgmt"]
  to   = aws_ssoadmin_permission_set.flipside_discord_mgmt
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set.pset["PowerUserAccess"]
  to   = aws_ssoadmin_permission_set.power_user_access
}

# Inline Policies
moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set_inline_policy.pset_inline_policy["EngineeringAccess"]
  to   = aws_ssoadmin_permission_set_inline_policy.engineering_access_inline
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set_inline_policy.pset_inline_policy["AWSServiceCatalogEndUserAccess"]
  to   = aws_ssoadmin_permission_set_inline_policy.service_catalog_end_user_inline
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set_inline_policy.pset_inline_policy["BillingAccess"]
  to   = aws_ssoadmin_permission_set_inline_policy.billing_access_inline
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_permission_set_inline_policy.pset_inline_policy["FlipsideDiscordMgmt"]
  to   = aws_ssoadmin_permission_set_inline_policy.discord_mgmt_inline
}

# Managed Policy Attachments
moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSAdministratorAccess::AWSBillingConductorReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_admin_billing_conductor
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSAdministratorAccess::AWSBillingReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_admin_billing_readonly
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSAdministratorAccess::AdministratorAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_admin_administrator
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["EngineeringAccess::AWSCloud9User"]
  to   = aws_ssoadmin_managed_policy_attachment.eng_cloud9
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["EngineeringAccess::AWSGlueConsoleFullAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.eng_glue
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["EngineeringAccess::AmazonAthenaFullAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.eng_athena
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["EngineeringAccess::ReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.eng_readonly
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSOrganizationsFullAccess::AWSOrganizationsFullAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_orgs_full
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSPowerUserAccess::AWSBillingConductorReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_power_billing_conductor
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSPowerUserAccess::AWSBillingReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_power_billing_readonly
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSPowerUserAccess::PowerUserAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_power_power_user
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSReadOnlyAccess::ViewOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.aws_readonly_view_only
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSServiceCatalogAdminFullAccess::AWSServiceCatalogAdminFullAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.svc_catalog_admin
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["AWSServiceCatalogEndUserAccess::AWSServiceCatalogEndUserFullAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.svc_catalog_end_user
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["FlipsideDiscordMgmt::ReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.discord_readonly
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["PowerUserAccess::AWSCloud9User"]
  to   = aws_ssoadmin_managed_policy_attachment.power_cloud9
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["PowerUserAccess::AWSCodePipeline_FullAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.power_codepipeline
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["PowerUserAccess::IAMReadOnlyAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.power_iam_readonly
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_managed_policy_attachment.pset_managed_policy["PowerUserAccess::PowerUserAccess"]
  to   = aws_ssoadmin_managed_policy_attachment.power_power_user
}

# Account Assignments for root group - moved to new structure
moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:016638755067"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["016638755067"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:035940933289"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["035940933289"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:071300172781"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["071300172781"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:084215729456"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["084215729456"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:102758306705"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["102758306705"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:214816915336"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["214816915336"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:222802434940"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["222802434940"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:258529451760"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["258529451760"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:320868638264"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["320868638264"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:380267255957"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["380267255957"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:383686502118"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["383686502118"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:478897220178"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["478897220178"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:489582127624"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["489582127624"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:490041342817"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["490041342817"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:579011195466"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["579011195466"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:590183891759"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["590183891759"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:664280923171"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["664280923171"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:679987962278"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["679987962278"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:681932734762"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["681932734762"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:704693948482"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["704693948482"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:734995239048"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["734995239048"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:767966058645"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["767966058645"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:834825468941"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["834825468941"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:848579003984"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["848579003984"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:850178735765"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["850178735765"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:862006574860"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["862006574860"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:878315836224"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["878315836224"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:924682671219"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["924682671219"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:957136710666"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["957136710666"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:983615436000"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["983615436000"]
}

moved {
  from = module.aws_iam_identity_center.aws_ssoadmin_account_assignment.account_assignment["Type:GROUP__Principal:root__Permission:AWSAdministratorAccess__Account:995926874157"]
  to   = aws_ssoadmin_account_assignment.root_admin_all["995926874157"]
}

