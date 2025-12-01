data "assert_test" "total_cpu_and_base_cpu_both_null" {
  test = !(var.total_cpu == null && var.unit_cpu == null)

  throw = "For ${var.identifier}, total CPU and base CPU cannot both be null"
}

data "assert_test" "total_memory_and_base_memory_both_null" {
  test = !(var.total_memory == null && var.unit_memory == null)

  throw = "For ${var.identifier}, total memory and base memory cannot both be null"
}

locals {
  base_supported_values = {
    256 = {
      min       = 512
      max       = 2048
      increment = 1024
      range     = [512, 1024, 2048]
    }

    512 = {
      min       = 1024
      max       = 4096
      increment = 1024
    }

    1024 = {
      min       = 1024
      max       = 8192
      increment = 1024
    }

    2048 = {
      min       = 4096
      max       = 16384
      increment = 1024
    }

    4096 = {
      min       = 8192
      max       = 30720
      increment = 1024
    }

    8192 = {
      min       = 16384
      max       = 61440
      increment = 4096
    }

    16384 = {
      min       = 32768
      max       = 122880
      increment = 8192
    }
  }

  supported_values = {
    for cpu_value, memory_constraints in local.base_supported_values : cpu_value => [
      for memory_value in lookup(memory_constraints, "range", range(memory_constraints["min"], memory_constraints["max"], memory_constraints["increment"])) : tonumber(memory_value)
    ]
  }

  total_usable_cpu = tonumber(var.unit_cpu != null ? var.unit_cpu * var.scale : var.total_cpu)
  total_cpu        = tonumber(local.total_usable_cpu + var.cpu_cushion)

  supported_cpu_values = sort([
    for cpu_value, _ in local.supported_values : tonumber(cpu_value)
  ])

  nearest_supported_cpu_value = contains(local.supported_cpu_values, local.total_cpu) ? local.total_cpu : tonumber(min([
    for cpu_value in local.supported_cpu_values : cpu_value if tonumber(cpu_value) >= local.total_cpu
  ]...))

  supported_memory_values = [
    for memory_value in sort(local.supported_values[local.nearest_supported_cpu_value]) : tonumber(memory_value)
  ]

  total_usable_memory = tonumber(var.unit_memory != null ? var.unit_memory * var.scale : var.total_memory)
  total_memory        = tonumber(local.total_usable_memory + var.memory_cushion)

  nearest_supported_memory_value = contains(local.supported_memory_values, local.total_memory) ? local.total_memory : tonumber(min([
    for memory_value in local.supported_memory_values : memory_value if tonumber(memory_value) >= local.total_memory
  ]...))
}

data "assert_test" "total_cpu_exceeds_max_cpu_supported" {
  test = local.total_cpu <= local.nearest_supported_cpu_value

  throw = "For ${var.identifier}, total cpu '${local.total_cpu}' exceeds the max supported CPU '${local.nearest_supported_cpu_value}'"
}

data "assert_test" "total_memory_exceeds_max_memory_supported" {
  test = local.total_memory <= local.nearest_supported_memory_value

  throw = "For ${var.identifier}, total memory '${local.total_memory}' exceeds the max supported memory '${local.nearest_supported_memory_value}'"
}
