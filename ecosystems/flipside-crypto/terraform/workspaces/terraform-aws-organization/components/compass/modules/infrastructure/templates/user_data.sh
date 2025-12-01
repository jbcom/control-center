#!/bin/bash

set -eo pipefail

exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

apt-get -yqq update
apt-get install -yqq --no-install-recommends \
  ca-certificates \
  curl \
  unzip

curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf ./aws*

datadog_api_key=$(aws ssm get-parameter --name "${datadog_api_key_ssm_path}" --with-decryption --query "Parameter.Value" --output text)

DD_SITE="datadoghq.com" \
DD_API_KEY="$${datadog_api_key}" \
bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"

secret_backend_command_path="/etc/datadog-secret-backend"
secret_backend_command_bin="$${secret_backend_command_path}/datadog-secret-backend"

mkdir -p "$secret_backend_command_path"
curl -L https://github.com/rapdev-io/datadog-secret-backend/releases/latest/download/datadog-secret-backend-linux-arm64.tar.gz -o /tmp/datadog-secret-backend-linux-arm64.tar.gz
tar -xvzf /tmp/datadog-secret-backend-linux-arm64.tar.gz -C "$secret_backend_command_path"
rm -f /tmp/datadog-secret-backend-linux-arm64.tar.gz

chown dd-agent:root "$secret_backend_command_bin"
chmod 500 "$secret_backend_command_bin"

cat << EOF > "$${secret_backend_command_path}/datadog-secret-backend.yaml"
---
backends:
  default:
    backend_type: aws.ssm
    parameters:
%{ for database_data in values(databases) ~}
      - ${database_data["database_monitoring"]["role_password"]}
%{ endfor ~}
    aws_session:
      aws_region: ${region}
EOF

sed -i 's/^# ec2_prefer_imdsv2: false/ec2_prefer_imdsv2: true/' /etc/datadog-agent/datadog.yaml
sed -i "s|^# secret_backend_command: <COMMAND_PATH>|secret_backend_command: $${secret_backend_command_bin}|" /etc/datadog-agent/datadog.yaml


cat << EOF > /etc/datadog-agent/conf.d/postgres.d/conf.yaml
---
init_config:
instances:
%{ for environment_name, database_data in databases ~}
  - dbm: true
    host: '${database_data["address"]}'
    port: ${database_data["port"]}
    username: '${database_data["database_monitoring"]["role_name"]}'
    password: 'ENC[default:${database_data["database_monitoring"]["role_password"]}]'
    dbname: '${database_data["database_name"]}'
    dbstrict: true
    collect_schemas:
      enabled: true
    relations:
      - relation_regex: .*
    aws:
      instance_endpoint: '${database_data["endpoint"]}'
      region: '${region}'
    tags:
      - 'env:${environment_name}'
      - 'service:compass'
      - 'dbclusteridentifier:${database_data["db_cluster_identifier"]}'
      - 'dbinstanceidentifier:${database_data["db_instance_identifier"]}'
      - 'region:${region}'
%{ endfor ~}
EOF

systemctl restart datadog-agent
