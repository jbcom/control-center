module "aws_acm_certificates" {
  source  = "digitickets/cli/aws"
  version = "7.1.1"

  aws_cli_commands = ["acm", "list-certificates"]
  aws_cli_query    = "CertificateSummaryList"

  assume_role_arn = var.execution_role_arn
}

locals {
  aws_acm_certificates_raw_data = {
    for record in module.aws_acm_certificates.result : record["DomainName"] => record...
  }

  aws_acm_certificates_singular = {
    for domain_name, domain_certificates in local.aws_acm_certificates_raw_data : domain_name =>
    one(domain_certificates) if length(domain_certificates) <= 1
  }

  aws_acm_certificates_raw_multiple = {
    for domain_name, domain_certificates in local.aws_acm_certificates_raw_data : domain_name =>
    domain_certificates if length(domain_certificates) > 1
  }

  aws_acm_certificates_multiple = merge(flatten([
    for domain_name, domain_certificates in local.aws_acm_certificates_raw_data : [
      for idx, certificate_data in domain_certificates : {
        "${domain_name}_${idx}" = certificate_data
      }
    ]
  ])...)

  aws_acm_certificates_base_data = {
    for domain_name, certificate_data in merge(local.aws_acm_certificates_singular, local.aws_acm_certificates_multiple) :
    domain_name => merge({
      for k, v in certificate_data :
      replace(lower(replace(replace(k, "/(.)([A-Z][a-z]+)/", "$1-$2"), "/([a-z0-9])([A-Z])/", "$1-$2")), "-", "_") => v
      if k != "SubjectAlternativeNameSummaries"
      }, {
      subject_alternative_names = certificate_data["SubjectAlternativeNameSummaries"]
      domain_chunks             = split(".", trimprefix(certificate_data["DomainName"], "*."))
    })
  }

  aws_acm_certificates_data = {
    for domain_name, certificate_data in local.aws_acm_certificates_base_data : domain_name => merge(certificate_data, {
      subdomain = length(certificate_data["domain_chunks"]) > 2 ? certificate_data["domain_chunks"][0] : null
      tld       = length(certificate_data["domain_chunks"]) > 2 ? join(".", slice(certificate_data["domain_chunks"], 1, length(certificate_data["domain_chunks"]))) : join(".", certificate_data["domain_chunks"])
    })
  }
}