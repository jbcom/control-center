# DNS Configuration Defaults
# This file defines the default configuration for DNS

locals {
  # DNS configuration defaults
  dns_defaults = {
    enabled = false

    # Route53 Zone Configuration
    zone_id          = null
    hosted_zone_name = null
    private_zone     = false

    # DNS Record Configuration
    create_dns_records                          = false
    dns_record_name                             = null
    dns_record_type                             = "A"
    dns_record_ttl                              = 300
    dns_record_allow_overwrite                  = true
    dns_record_evaluate_target_health           = true
    dns_record_alias_target_name                = null
    dns_record_alias_target_zone_id             = null
    dns_record_values                           = []
    dns_record_set_identifier                   = null
    dns_record_health_check_id                  = null
    dns_record_multivalue_answer_routing_policy = null
    dns_record_latency_routing_policy           = null
    dns_record_geolocation_routing_policy       = null
    dns_record_failover_routing_policy          = null
    dns_record_weighted_routing_policy          = null
  }

  # Create DNS flag
  create_dns = var.create_dns_records != null ? var.create_dns_records : local.config.dns.enabled

  # Final DNS configuration with individual variable overrides and global overrides
  dns = merge(
    local.config.dns,
    {
      enabled = var.create_dns_records != null ? var.create_dns_records : local.config.dns.enabled

      # Apply global overrides for zone settings
      zone_id          = var.zone_id != null ? var.zone_id : (var.dns_zone_id != null ? var.dns_zone_id : local.config.dns.zone_id)
      hosted_zone_name = var.hosted_zone_name != null ? var.hosted_zone_name : (var.dns_hosted_zone_name != null ? var.dns_hosted_zone_name : local.config.dns.hosted_zone_name)
      private_zone     = var.private_zone != null ? var.private_zone : (var.dns_private_zone != null ? var.dns_private_zone : local.config.dns.private_zone)

      # Other DNS specific settings
      create_dns_records                          = var.create_dns_records != null ? var.create_dns_records : local.config.dns.create_dns_records
      dns_record_name                             = var.dns_record_name != null ? var.dns_record_name : local.config.dns.dns_record_name
      dns_record_type                             = var.dns_record_type != null ? var.dns_record_type : local.config.dns.dns_record_type
      dns_record_ttl                              = var.dns_record_ttl != null ? var.dns_record_ttl : local.config.dns.dns_record_ttl
      dns_record_allow_overwrite                  = var.dns_record_allow_overwrite != null ? var.dns_record_allow_overwrite : local.config.dns.dns_record_allow_overwrite
      dns_record_evaluate_target_health           = var.dns_record_evaluate_target_health != null ? var.dns_record_evaluate_target_health : local.config.dns.dns_record_evaluate_target_health
      dns_record_alias_target_name                = var.dns_record_alias_target_name != null ? var.dns_record_alias_target_name : local.config.dns.dns_record_alias_target_name
      dns_record_alias_target_zone_id             = var.dns_record_alias_target_zone_id != null ? var.dns_record_alias_target_zone_id : local.config.dns.dns_record_alias_target_zone_id
      dns_record_values                           = var.dns_record_values != null ? var.dns_record_values : local.config.dns.dns_record_values
      dns_record_set_identifier                   = var.dns_record_set_identifier != null ? var.dns_record_set_identifier : local.config.dns.dns_record_set_identifier
      dns_record_health_check_id                  = var.dns_record_health_check_id != null ? var.dns_record_health_check_id : local.config.dns.dns_record_health_check_id
      dns_record_multivalue_answer_routing_policy = var.dns_record_multivalue_answer_routing_policy != null ? var.dns_record_multivalue_answer_routing_policy : local.config.dns.dns_record_multivalue_answer_routing_policy
      dns_record_latency_routing_policy           = var.dns_record_latency_routing_policy != null ? var.dns_record_latency_routing_policy : local.config.dns.dns_record_latency_routing_policy
      dns_record_geolocation_routing_policy       = var.dns_record_geolocation_routing_policy != null ? var.dns_record_geolocation_routing_policy : local.config.dns.dns_record_geolocation_routing_policy
      dns_record_failover_routing_policy          = var.dns_record_failover_routing_policy != null ? var.dns_record_failover_routing_policy : local.config.dns.dns_record_failover_routing_policy
      dns_record_weighted_routing_policy          = var.dns_record_weighted_routing_policy != null ? var.dns_record_weighted_routing_policy : local.config.dns.dns_record_weighted_routing_policy
    }
  )
}
