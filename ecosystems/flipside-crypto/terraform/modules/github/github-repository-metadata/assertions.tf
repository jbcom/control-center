data "assert_test" "repository_is_managed" {
  test = contains(keys(local.repositories_data), local.repository_name)

  throw = "Repository '${local.repository_name}' is not in the managed repositories"
}
