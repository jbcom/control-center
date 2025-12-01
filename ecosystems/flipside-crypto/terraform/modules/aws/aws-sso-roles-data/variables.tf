variable "allowlist" {
  type = list(string)

  default = [
    "AWSAdministratorAccess",
    "AWSPowerUserAccess",
    "EngineeringAccess",
    "PowerUserAccess",
    "LeadsAccess",
  ]

  description = "SSO roles to include in the filter"
}