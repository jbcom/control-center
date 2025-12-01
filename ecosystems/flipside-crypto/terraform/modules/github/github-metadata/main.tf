data "curl" "get_github_metadata" {
  http_method = "GET"
  uri         = "https://api.github.com/meta"
}

locals {
  github_metadata = jsondecode(data.curl.get_github_metadata.response)
}