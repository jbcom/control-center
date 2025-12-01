locals {
  image_tag = formatdate("YYYYMMDDhhmmss", timestamp())
}

resource "docker_image" "this" {
  for_each = var.ecr_repository_urls

  name     = format("%v:%v", var.ecr_repository_urls[each.key], local.image_tag)
  platform = try(coalesce(var.repositories[each.key]["docker"]["platform"]), "linux/amd64")

  build {
    context    = format("%v/%v/%v", path.root, var.rel_to_root, try(coalesce(var.repositories[each.key]["docker"]["context"]), "."))
    tag        = ["${each.key}:${local.image_tag}"]
    dockerfile = try(coalesce(var.repositories[each.key]["docker"]["file"]), "Dockerfile")
    #    build_args = try(coalesce(var.repositories[each.key]["docker"]["build_args"]), null)
  }
}

resource "docker_registry_image" "this" {
  for_each = docker_image.this

  name = each.value.name

  keep_remotely = true

  triggers = {
    image_id = each.value.image_id
  }
}

locals {
  records_config = {
    repository_images = docker_registry_image.this
  }
}

module "permanent_record" {
  source = "../../../../utils/permanent-record"

  records = local.records_config

  records_dir = var.records_dir

  records_file_name = var.records_file_name
}
