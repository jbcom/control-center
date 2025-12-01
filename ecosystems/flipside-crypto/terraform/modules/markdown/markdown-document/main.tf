locals {
  link_template             = "<a href=\"%s\">%s</a>"
  list_template             = "<ol type=\"I\">\n%s\n</ol>\n"
  categorized_list_template = "<b>%s</b>\n\n${local.list_template}"
  collapsible_list_template = "<details>\n<summary>%s</summary>\n\n${local.list_template}</details>\n"
  list_item_template        = "<li>\n%s\n</li>\n"

  section_data = [
    for section_data in var.config.sections : merge(section_data, {
      reference = format("#%s", lower(replace(replace(section_data["title"], "_", "-"), " ", "-")))
      heading   = coalesce(section_data["format_headings"], var.config.format_headings) ? title(replace(replace(section_data["title"], "-", " "), "_", " ")) : section_data["title"]

      snippets = [
        for snippet_data in section_data["snippets"] : merge(snippet_data, {
          reference = format("#%s", lower(replace(replace(snippet_data["title"], "_", "-"), " ", "-")))
          heading   = coalesce(snippet_data["format_heading"], section_data["format_headings"], var.config.format_headings) ? title(replace(replace(snippet_data["title"], "-", " "), "_", " ")) : snippet_data["title"]
        })
      ]

      tables = [
        for table_data in section_data["tables"] : merge(table_data, {
          reference = format("#%s", lower(replace(replace(table_data["title"], "_", "-"), " ", "-")))
          heading   = coalesce(table_data["format_heading"], section_data["format_headings"], var.config.format_headings) ? title(replace(replace(table_data["title"], "-", " "), "_", " ")) : table_data["title"]
        })
      ]
    })
  ]

  index_section_raw_data = [
    for section_data in local.section_data : {
      link = format(local.link_template, section_data["reference"], section_data["heading"])
      nested = concat([
        for snippet_data in section_data["snippets"] : format(local.link_template, snippet_data["reference"], snippet_data["heading"])
        ], [
        for table_data in section_data["tables"] : format(local.link_template, table_data["reference"], table_data["heading"])
      ])
    }
  ]

  index_section_base_data = compact(flatten([
    for raw_data in local.index_section_raw_data : [
      raw_data["link"],
      length(raw_data["nested"]) > 0 ? format(local.list_template, join("\n", formatlist(local.list_item_template, raw_data["nested"]))) : ""
    ]
  ]))

  index_sections_data = length(local.index_section_base_data) > 0 ? format((var.config.collapsible_index ? local.collapsible_list_template : local.categorized_list_template), "Sections", join("\n", formatlist(local.list_item_template, local.index_section_base_data))) : ""

  index_pages_root_data = [
    for index_data in lookup(var.config.index, ".", []) :
    format(local.link_template, index_data["url"], index_data["title"])
  ]

  index_pages_nested_base_data = {
    for category_name, category_indexes in var.config.index : category_name => [
      for index_data in category_indexes :
      format(local.link_template, index_data["url"], index_data["title"])
    ] if category_name != "." && length(category_indexes) > 0
  }

  index_pages_nested_data = [
    for category_name, category_urls in local.index_pages_nested_base_data : format(local.categorized_list_template, category_name, join("\n", formatlist(local.list_item_template, category_urls)))
  ]

  index_pages_base_data = flatten(concat(local.index_pages_root_data, local.index_pages_nested_data))

  index_pages_data = length(local.index_pages_base_data) > 0 ? format((var.config.collapsible_index ? local.collapsible_list_template : local.categorized_list_template), "Pages", join("\n", formatlist(local.list_item_template, local.index_pages_base_data))) : ""

  index_base_metadata = compact([
    local.index_sections_data,
    local.index_pages_data,
  ])

  index_html_data = length(local.index_base_metadata) > 0 ? format(local.list_template, join("\n", formatlist(local.list_item_template, local.index_base_metadata))) : ""

  table_metadata = {
    for section_data in local.section_data : section_data["title"] => {
      for idx, table_data in section_data["tables"] : idx => {
        headers = [
          for column_data in table_data["columns"] : column_data["header"]
        ]

        row_count = max([
          for column_data in table_data["columns"] : length(column_data["rows"])
        ]...)
      }
    }
  }

  markdown_base_document = templatefile("${path.module}/templates/README.md", merge(var.config, {
    section_heading_level        = var.config.title != null ? "##" : "#"
    nested_section_heading_level = var.config.title != null ? "###" : "##"

    sections = local.section_data

    index_html_data = local.index_html_data

    table_metadata = local.table_metadata
  }))

  markdown_document = var.config.template != null ? templatefile(var.config.template, merge(var.config.template_vars, {
    rendered = local.markdown_base_document
  })) : local.markdown_base_document
}

resource "local_sensitive_file" "default" {
  count = var.config.path != null ? 1 : 0

  filename = var.config.path

  content = local.markdown_document
}