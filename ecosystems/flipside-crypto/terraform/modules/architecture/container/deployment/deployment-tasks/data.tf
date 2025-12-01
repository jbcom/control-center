data "aws_ecr_image" "this" {
  for_each = var.ecr_repository_urls

  repository_name = each.key
  image_tag       = var.image_tag
}

locals {
  repository_images = {
    for repository_name, image_data in data.aws_ecr_image.this : repository_name => merge(image_data, {
      url  = var.ecr_repository_urls[repository_name]
      name = format("%v:%v", var.ecr_repository_urls[repository_name], image_data.image_tag)
    })
  }
}