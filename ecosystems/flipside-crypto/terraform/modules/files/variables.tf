variable "files" {
  type = list(map(map(string)))

  description = "Files data"
}

variable "preserve_names_as_is" {
  type = list(string)

  default = []

  description = "Preserve names as is"
}

variable "rel_to_root" {
  type = string

  default = ""

  description = "Relative path to the root of the repository"
}

variable "file_base_path" {
  type = string

  default = ""

  description = "Base path for files"
}

variable "file_path_trim_prefix" {
  type = string

  default = ""

  description = "Prefix to trim off the file path"
}

variable "ownership" {
  type = object({
    name  = string
    email = string
  })

  default = {
    name  = "devops-flipsidecrypto"
    email = "devops-flipsidecrypto@users.noreply.github.com"
  }

  description = "Ownership information for the commit"
}

variable "allowlist" {
  type = list(string)

  default = []

  description = "Allowlist to filter by - Paths beginning with elements of this list will be allowed"
}

variable "denylist" {
  type = list(string)

  default = []

  description = "Denylist to filter by - Paths beginning with elements of this list will be denied"
}

variable "save_gitkeep_record" {
  type = bool

  default = false

  description = "Whether to save a gitkeep record or not"
}

variable "write_files" {
  type = bool

  default = true

  description = "Whether to write the files or not"
}