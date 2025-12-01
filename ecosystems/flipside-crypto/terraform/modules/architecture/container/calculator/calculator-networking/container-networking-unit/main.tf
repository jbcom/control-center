locals {
  exposed = var.config.exposed
  ingress = var.config.ingress
  port    = local.exposed ? local.ingress["port"] : 0

  raw_port_mappings = var.config.port_mappings

  port_mappings_map = {
    for port_map_definition in local.raw_port_mappings : join("_", compact([
      port_map_definition["protocol"],
      port_map_definition["containerPort"],
      port_map_definition["hostPort"] == null ? "" : port_map_definition["hostPort"],
    ])) => port_map_definition
  }

  ingress_port_mapping_keys = [
    "tcp_${local.port}_${local.port}",
    "tcp_${local.port}",
  ]

  existing_ingress_port_map_definition = {
    for key in local.ingress_port_mapping_keys : key => lookup(local.port_mappings_map, key, {})
  }

  ingress_port_mapping_found_key = one([
    for k, v in local.existing_ingress_port_map_definition : k if v != {}
  ])

  port_mappings = concat([
    for port_map_key, port_map_definition in local.port_mappings_map : port_map_definition if local.ingress_port_mapping_found_key == null || port_map_key != local.ingress_port_mapping_found_key
    ], local.ingress_port_mapping_found_key == null ? (local.exposed ? [
      {
        containerPort = local.port
        hostPort      = null
        protocol      = "tcp"
      }
    ] : []) : [
    local.existing_ingress_port_map_definition[local.ingress_port_mapping_found_key],
  ])
}

data "assert_test" "exposed_resources_must_have_port" {
  test = !local.exposed || (local.exposed && local.port != null)

  throw = "${var.identifier} is exposed but has no port set in its ingress"
}

data "assert_test" "duplicate_port_mappings" {
  count = length(local.raw_port_mappings)

  test = sum([
    for port_map_definition in local.raw_port_mappings : (local.raw_port_mappings[count.index]["containerPort"] == port_map_definition["containerPort"] && local.raw_port_mappings[count.index]["hostPort"] == port_map_definition["hostPort"] && local.raw_port_mappings[count.index]["protocol"] == port_map_definition["protocol"]) ? 1 : 0
  ]) == 1

  throw = "${var.identifier} has a duplicate port mapping:\n\n${yamlencode(local.raw_port_mappings)}"
}
