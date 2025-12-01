variable "username" {
  type = string

  description = "Username for the bot"
}

variable "create_login_profile" {
  type = bool

  default = false

  description = "Whether or not to create a login profile"
}

variable "attach_admin_policy" {
  type = bool

  default = false

  description = "Attach admin policy to the bot"
}

variable "custom_policy_arns" {
  type = list(string)

  default = []

  description = "Custom policies to attach to the bot"
}

variable "number_of_policies" {
  type = number

  default = 0

  description = "Number of custom policies being attached to the bot"
}

variable "save_secrets_to_github" {
  type = bool

  default = false

  description = "Whether to save secrets to GitHub"
}

variable "generate_gpg_key" {
  type = bool

  default = false

  description = "Whether to generate a GPG key for the bot"
}

variable "attach_key_pair" {
  type = bool

  default = false

  description = "Whether to attach an SSH key-pair to the bot"
}

variable "write_key_pair_to_file" {
  type = bool

  default = false

  description = "Write the SSH key to a file"
}

variable "write_key_pair_to_github" {
  type = bool

  default = false

  description = "Write the SSH key to Github Actions"
}

variable "save_to_aws_profile" {
  type = bool

  default = false

  description = "Whether to save the bot user to an AWS profile locally"
}

variable "password_reset_required" {
  description = "Whether the user should be forced to reset the generated password on first login."
  type        = bool
  default     = false
}

variable "password_length" {
  description = "The length of the generated password"
  type        = number
  default     = 24
}

variable "context" {
  type = any

  description = "Context data"
}