variable "role_name" {
  type = string

  description = "Role name"
}

variable "policy_arns" {
  type = list(string)

  default = []

  description = "Policy ARNs to attach to the role"
}