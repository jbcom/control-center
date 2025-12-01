import concurrent.futures
import hashlib
import json
import os
import secrets
import shutil
import string
import time
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Set, Tuple

import botocore.exceptions
import googleapiclient.errors
import gspread
import humanize
import pandas as pd
from gspread.utils import GridRangeType
from terraform_modules import utils
from terraform_modules.errors import FailedResponseError
from terraform_modules.github_client import GithubClient
from terraform_modules.google_client import GoogleClient
from terraform_modules.settings import (
    GCP_BOOLEAN_CONSTRAINTS,
    GCP_LIST_CONSTRAINTS,
    GCP_REQUIRED_APIS,
    GCP_REQUIRED_ORGANIZATION_ROLES,
    GCP_REQUIRED_ROLES,
    GCP_SECURITY_PROJECT,
    METADATA_RECORDS_DIR,
)
from terraform_modules.terraform_data_source import TerraformDataSource
from terraform_modules.terraform_module_resources import TerraformModuleResources
from terraform_modules.utils import FilePath, Utils

DEFAULT_SYSTEM_TRIGGER = "automated systems"


class TerraformNullResource(Utils):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ds = TerraformDataSource(**kwargs)

        (
            terraform_module_resources,
            time_elapsed,
        ) = TerraformModuleResources.get_all_resources(
            terraform_modules=utils.get_available_methods(self.__class__),
            module_params=self.get_shared_terraform_module_params(),
            module_type="null_resource",
        )

        self.logger.info(f"Getting Null Resource Terraform Module Resources took {time_elapsed:0.2f} seconds to run")

        self.terraform_module_resources = terraform_module_resources

    def update_gitkeep_record(
        self,
        record_dir: Optional[FilePath] = None,
        new_file_names: Optional[list[str]] = None,
        exit_on_completion: bool = True,
    ):
        """Updates the Gitkeep record for a directory

        generator=module_class: git

        name: record_dir, required: true, type: string
        name: new_file_names, required: true, json_encode: true"""
        if record_dir is None:
            record_dir = self.get_input("record_dir", required=True)

        if new_file_names is None:
            new_file_names = self.decode_input("new_file_names", required=True, decode_from_base64=False)

        self.logger.info(f"Updating the Gitkeep record for {record_dir}")

        record_dir = self.local_path(record_dir) if self.tld else Path(record_dir)
        record_file = record_dir.joinpath(".gitkeep")
        gitkeep_record = set(self.ds.get_gitkeep_record(record_dir=record_dir, exit_on_completion=False))

        self.logger.info(f"Existing records for {record_dir}: {gitkeep_record}")

        self.logger.info(f"Validating new record files: {new_file_names}")
        gitkeep_record.update(self.ds.get_valid_gitkeep_records(record_dir=record_dir, record_files=new_file_names))

        self.logger.info(f"New records for {record_dir}: {gitkeep_record}")

        gitkeep_record = os.linesep.join(gitkeep_record)

        if self.tld:
            results = self.update_file(file_path=record_file, file_data=gitkeep_record, allow_empty=True)
        else:
            results = self.ds.github_client.update_repository_file(
                file_path=record_file, file_data=gitkeep_record, allow_empty=True
            )

        return self.exit_run(results=results, exit_on_completion=exit_on_completion)

    def update_and_record_file(
        self,
        file_path: Optional[FilePath] = None,
        file_data: Optional[Any] = None,
        json_data: Optional[str] = None,
        yaml_data: Optional[str] = None,
        allow_encoding: Optional[bool] = None,
        allow_empty: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Updates a file and records it to a gitkeep record

        generator=module_class: os

        name: file_path, required: true, type: string
        name: file_data, required: false, json_encode: true, base64_encode: true
        name: json_data, required: false, type: string
        name: yaml_data, required: false, type: string
        name: allow_encoding, required: false
        name: allow_empty, required: false, default: false
        """
        if file_path is None:
            file_path = self.get_input("file_path", required=True)

        if file_data is None:
            file_data = self.decode_input("file_data", required=False)

        if json_data is None:
            json_data = self.decode_input("json_data", required=False, decode_from_base64=False)

        if yaml_data is None:
            yaml_data = self.decode_input(
                "yaml_data",
                required=False,
                decode_from_base64=False,
                decode_from_json=False,
                decode_from_yaml=True,
            )

        input_list = [file_data, json_data, yaml_data]
        not_none_count = sum(x is not None for x in input_list)
        if not_none_count > 1:
            raise AttributeError("file_data, json_data, and yaml_data are mutually exclusive")
        elif not_none_count == 0:
            return
        else:
            file_data = next(x for x in input_list if x is not None)

        if allow_encoding is None:
            allow_encoding = self.get_input("allow_encoding", required=False, is_bool=True)

        if allow_empty is None:
            allow_empty = self.get_input("allow_empty", required=False, default=False, is_bool=True)

        self.logger.info(f"Updating {file_path} and recording it to the gitkeep record for its parent directory")

        if self.tld:
            file_path = self.local_path(file_path)
            self.update_file(
                file_path=file_path,
                file_data=file_data,
                allow_encoding=allow_encoding,
                allow_empty=allow_empty,
            )
        else:
            file_path = Path(file_path)
            self.ds.github_client.update_repository_file(
                file_path=file_path,
                file_data=file_data,
                allow_empty=allow_empty,
            )

        self.update_gitkeep_record(
            record_dir=file_path.parent,
            new_file_names=[file_path.name],
            exit_on_completion=False,
        )

        return self.exit_run(exit_on_completion=exit_on_completion)

    def permanent_record(
        self,
        records_dir: Optional[str] = None,
        records_file_name: Optional[str] = None,
        records_file_ext: Optional[str] = None,
        records: Optional[Any] = None,
        expand_records: Optional[bool] = None,
        save_empty_records: Optional[bool] = None,
        cleanup_records_dir: Optional[bool] = None,
        workspace_dir: Optional[FilePath] = None,
        exit_on_completion: bool = True,
    ):
        """Saves permanent record(s)

        generator=module_class: utils, no_class_in_module_name: true

        name: records_dir, required: false, default: "records"
        name: records_file_name, required: false, type: string
        name: records_file_ext, required: false, default: ".json"
        name: records, required: true, json_encode: true, base64_encode: true
        name: expand_records, required: false, default: false
        name: save_empty_records, required: false, default: false
        name: cleanup_records_dir, required: false
        name: workspace_dir, required: false, type: string, trigger: "${coalesce(var.workspace_dir, basename(abspath(path.root)))}"
        """
        if records_dir is None:
            records_dir = self.get_input("records_dir", required=False, default="records")

        if records_file_name is None:
            records_file_name = self.get_input("records_file_name", required=False)

        if records_file_ext is None:
            records_file_ext = self.get_input("records_file_ext", required=False, default=".json")

        if records is None:
            records = self.decode_input("records", required=True)

        if expand_records is None:
            expand_records = self.get_input("expand_records", required=False, default=False, is_bool=True)

        if save_empty_records is None:
            save_empty_records = self.get_input("save_empty_records", required=False, default=False, is_bool=True)

        if cleanup_records_dir is None:
            cleanup_records_dir = self.get_input("cleanup_records_dir", required=False, is_bool=True)

        if workspace_dir is None:
            workspace_dir = self.get_input("workspace_dir", required=True)

        self.logger.info(f"Saving permanent records to {records_dir}")

        resolved_records_file_name = (
            Path(workspace_dir)
            if utils.is_nothing(records_file_name)
            else Path(str(records_file_name).removesuffix(records_file_ext))
        )
        resolved_records_dir = (
            Path(str(records_dir).removesuffix(f"/{resolved_records_file_name}"))
            if utils.is_nothing(records_file_name)
            else Path(records_dir)
        )

        if expand_records:
            processed_records = {
                (
                    f"{k}{records_file_ext}"
                    if utils.is_nothing(records_file_name)
                    else resolved_records_file_name.joinpath(f"{k}{records_file_ext}")
                ): v
                for k, v in records.items()
            }
        else:
            processed_records = {resolved_records_file_name.with_suffix(records_file_ext): records}

        self.log_results(processed_records, "processed records")

        for record_path, record_data in processed_records.items():
            record_path = resolved_records_dir.joinpath(record_path)
            self.logger.info(f"Saving record to {record_path}")

            self.update_and_record_file(
                file_path=record_path,
                file_data=record_data,
                allow_empty=save_empty_records,
                exit_on_completion=False,
            )

        if cleanup_records_dir or (cleanup_records_dir is None and str(records_dir).startswith(METADATA_RECORDS_DIR)):
            self.logger.info(f"Cleaning up the {resolved_records_dir} records directory")
            self.clean_directory(dir_path=resolved_records_dir, exit_on_completion=False)

        self.exit_run(exit_on_completion=exit_on_completion)

    def delete_dir(
        self,
        repository_owner: Optional[str] = None,
        repository_name: Optional[str] = None,
        dir_path: Optional[FilePath] = None,
        exit_on_completion: Optional[bool] = True,
    ):
        """Deletes a directory

        generator=module_class: os

        name: repository_owner, required: false, type: string
        name: repository_name, required: false, type: string
        name: dir_path, required: true"""
        if repository_owner is None:
            repository_owner = self.get_input("repository_owner", required=False)

        if repository_name is None:
            repository_name = self.get_input("repository_name", required=False)

        if dir_path is None:
            dir_path = self.get_input("dir_path", required=True)

        if utils.is_nothing(dir_path):
            self.errors.append("No directory path to delete")
            return self.exit_run(exit_on_completion=exit_on_completion)

        use_local_repo = len(utils.all_non_empty(repository_owner, repository_name)) == 0

        github_client = None

        if not use_local_repo:
            github_client = GithubClient(
                github_owner=repository_owner,
                github_repo=repository_name,
                github_token=self.GITHUB_TOKEN,
                **self.kwargs,
            )

        if use_local_repo and Path(dir_path).is_absolute():

            def delete_local_dir(function, path, excinfo):
                if isinstance(excinfo, FileNotFoundError):
                    return

                self.errors.append(f"{function} failed to delete {path}: {excinfo}")

            local_dir = self.local_path(dir_path)
            self.logger.warning(f"Deleting local directory {dir_path}")
            shutil.rmtree(local_dir, onerror=delete_local_dir)
        else:
            self.logger.warning(f"Scanning directory {dir_path} for files to delete")

            for fp in self.ds.scan_dir(
                files_path=dir_path,
                paths_only=True,
                decode=False,
                sanitize_keys=False,
                stem_only=False,
                recursive=True,
                exit_on_completion=False,
            ):
                if use_local_repo:
                    self.logger.info(f"Deleting local file {fp}")
                    self.delete_file(fp)
                else:
                    self.logger.info(f"Deleting remote file {fp}")
                    github_client.delete_file(file_path=fp)

        return self.exit_run(exit_on_completion=exit_on_completion)

    def clean_directory(self, dir_path: Optional[FilePath] = None, exit_on_completion: bool = True):
        """Cleans a directory using its gitkeep record

        generator=module_class: os

        name: dir_path, required: true, type: string"""

        if dir_path is None:
            dir_path = self.get_input("dir_path", required=True)

        local_dir_path = self.local_path(dir_path)

        if not local_dir_path.exists():
            self.logger.warning(f"{local_dir_path} does not exist and so does not need to be cleaned")
            return self.exit_run(exit_on_completion=exit_on_completion)

        kept_dir_files = self.ds.get_gitkeep_record(local_dir_path, exit_on_completion=False)

        self.logger.info(f"Kept directory files for {dir_path}: {kept_dir_files}")

        current_dir_files = self.ds.scan_dir(
            files_path=local_dir_path,
            files_glob="*.json",
            paths_only=True,
            recursive=False,
            exit_on_completion=False,
        )

        for current_workspace_file in current_dir_files:
            local_current_workspace_file = self.local_path(current_workspace_file)
            current_workspace_file_name = local_current_workspace_file.name
            if current_workspace_file_name not in kept_dir_files:
                self.logger.warning(f"Deleting orphan directory file {current_workspace_file_name}")
                self.delete_file(file_path=local_current_workspace_file)

        return self.exit_run(exit_on_completion=exit_on_completion)

    def _aws_get_tagged_ecs_clusters(self, tags: dict[str, str], execution_role_arn: str | None = None):
        """
        Get tagged AWS ECS clusters that match all specified tags.

        # NOPARSE
        """

        resourcegroupstaggingapi_client = self.ds.get_aws_client(
            client_name="resourcegroupstaggingapi",
            execution_role_arn=execution_role_arn,
        )

        # Convert tags dictionary to list of tag filters
        tag_filters = [{"Key": key, "Values": [value]} for key, value in tags.items()]

        # Fetch ECS clusters by tags
        tagged_clusters = []
        response = resourcegroupstaggingapi_client.get_resources(
            ResourceTypeFilters=["ecs:cluster"], TagFilters=tag_filters
        )
        for resource in response["ResourceTagMappingList"]:
            self.logger.debug(f"Found ECS cluster {resource}")
            cluster_arn = resource["ResourceARN"]
            tagged_clusters.append(cluster_arn)

        return tagged_clusters

    def _aws_get_tagged_ecs_services(
        self,
        cluster_name: str,
        tags: dict[str, str],
        execution_role_arn: str | None = None,
    ):
        """
        Get tagged AWS ECS services for a cluster that match all specified tags.

        # NOPARSE
        """

        ecs_client = self.ds.get_aws_client(client_name="ecs", execution_role_arn=execution_role_arn)
        resourcegroupstaggingapi_client = self.ds.get_aws_client(
            client_name="resourcegroupstaggingapi",
            execution_role_arn=execution_role_arn,
        )

        # Convert tags dictionary to list of tag filters
        tag_filters = [{"Key": key, "Values": [value]} for key, value in tags.items()]

        # Fetch all ECS services in the cluster
        paginator = ecs_client.get_paginator("list_services")
        all_service_arns = []
        for page in paginator.paginate(cluster=cluster_name):
            all_service_arns.extend(page["serviceArns"])

        # Fetch all tagged ECS services in the account that match the tag filters
        tagged_service_arns = []
        response = resourcegroupstaggingapi_client.get_resources(
            ResourceTypeFilters=["ecs:service"], TagFilters=tag_filters
        )

        # Filter for services that belong to the specified cluster
        for resource in response["ResourceTagMappingList"]:
            service_arn = resource["ResourceARN"]
            if service_arn in all_service_arns:
                self.logger.debug(f"Found ECS service {service_arn} in cluster {cluster_name}")
                tagged_service_arns.append(service_arn)

        return tagged_service_arns

    def _aws_force_redeploy_ecs_services(
        self,
        cluster_name: str,
        service_arns: list[str],
        dry_run: bool = False,
        execution_role_arn: str | None = None,
    ):
        """
        Force redeployment of ECS services for a cluster

        # NOPARSE
        """
        ecs_client = self.ds.get_aws_client(client_name="ecs", execution_role_arn=execution_role_arn)

        for service_arn in service_arns:
            # Get the latest task definition for the service
            response = ecs_client.describe_services(cluster=cluster_name, services=[service_arn])
            task_definition = response["services"][0]["taskDefinition"]

            # Print action instead of executing if in dry run mode
            if dry_run:
                self.logger.debug(
                    f"[DRY RUN] Service {service_arn} would be redeployed with task definition {task_definition}"
                )
            else:
                # Force a new deployment with the latest task definition
                ecs_client.update_service(
                    cluster=cluster_name,
                    service=service_arn,
                    taskDefinition=task_definition,
                    forceNewDeployment=True,
                )
                self.logger.info(f"Service {service_arn} redeployed with task definition {task_definition}")

    def restart_aws_ecs_services_matching_tags(
        self,
        tags: dict[str, str] | None = None,
        cluster_tags: dict[str, str] | None = None,
        service_tags: dict[str, str] | None = None,
        execution_role_arn: str | None = None,
        dry_run: bool | None = None,
        exit_on_completion: bool = True,
    ):
        """Restart AWS ECS services matching tags

        generator=module_class: aws

        name: tags, required: true, json_encode: true, base64_encode: true
        name: cluster_tags, required: false, default: {}, json_encode: true, base64_encode: true
        name: service_tags, required: false, default: {}, json_encode: true, base64_encode: true
        name: execution_role_arn, required: false, type: string
        name: dry_run, required: false, default: false"""
        if tags is None:
            tags = self.decode_input("tags", required=True)

        if cluster_tags is None:
            cluster_tags = self.decode_input("cluster_tags", required=False, default={}, allow_none=False)

        if service_tags is None:
            service_tags = self.decode_input("service_tags", required=False, default={}, allow_none=False)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if dry_run is None:
            dry_run = self.get_input("dry_run", required=False, default=False, is_bool=True)

        self.logger.info(
            f"Restarting AWS ECS services" + f" for {execution_role_arn}"
            if not utils.is_nothing(execution_role_arn)
            else ""
        )

        if not tags and not cluster_tags and not service_tags:
            self.logger.warning("No tags provided. Exiting as there are no criteria for ECS clusters or services.")
            return self.exit_run(exit_on_completion=exit_on_completion)

        for k, v in tags.items():
            self.logger.debug(f"Matching tag {k}: {v}")

        cluster_tags = cluster_tags or {}
        for k, v in cluster_tags.items():
            self.logger.debug(f"Matching cluster tag {k}: {v}")

        service_tags = service_tags or {}
        for k, v in service_tags.items():
            self.logger.debug(f"Matching service tag {k}: {v}")

        # Get tagged clusters and redeploy services in each
        cluster_arns = self._aws_get_tagged_ecs_clusters(tags | cluster_tags, execution_role_arn=execution_role_arn)
        if not cluster_arns:
            self.logger.warning("No ECS clusters found with the specified tags.")
            return self.exit_run(exit_on_completion=exit_on_completion)

        for cluster_arn in cluster_arns:
            cluster_name = cluster_arn.split("/")[-1]  # Extract cluster name from ARN
            self.logger.info(f"Processing cluster: {cluster_name}")
            service_arns = self._aws_get_tagged_ecs_services(
                cluster_name, tags | service_tags, execution_role_arn=execution_role_arn
            )
            if not service_arns:
                self.logger.warning(f"No tagged services found in cluster: {cluster_name}")
                continue

            self._aws_force_redeploy_ecs_services(
                cluster_name,
                service_arns,
                dry_run=dry_run,
                execution_role_arn=execution_role_arn,
            )

        self.exit_run(exit_on_completion=exit_on_completion)

    def _delete_matching_secrets_from_aws_account(
        self,
        secrets: list[str],
        execution_role_arn: str,
        role_session_name: str | None = None,
        dry_run: bool = False,
    ):
        """Deletes matching secrets from an AWS account

        # NOPARSE
        """
        # Extract account_id from the execution_role_arn
        # Assuming ARN format: arn:aws:iam::<account_id>:role/<role_name>
        account_id = execution_role_arn.split(":")[4]
        self.logger.info(f"Deleting secrets matching account '{account_id}'")

        account_secrets = self.ds.list_aws_account_secrets(
            filters=[],
            get_secrets=False,
            no_empty_secrets=False,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            exit_on_completion=False,
        )

        asm = self.ds.get_aws_client(
            "secretsmanager",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        if not account_secrets:
            self.logger.warning(f"No secrets found for account '{execution_role_arn}'")
            return

        client_errors = []
        for secret in secrets:
            if secret in account_secrets:
                if dry_run:
                    self.logger.debug(f"[DRY RUN] deleting secret '{secret}' from account '{account_id}'")
                    continue

                try:
                    # Use the Secrets Manager client to delete the secret
                    asm.delete_secret(SecretId=secret, ForceDeleteWithoutRecovery=True)
                    self.logger.info(f"Deleted secret '{secret}' from account '{account_id}'")
                except botocore.exceptions.ClientError as exc:
                    client_errors.append(exc)

        if client_errors:
            raise ExceptionGroup(
                f"Failed to delete secrets from AWS account '{account_id}'",
                client_errors,
            )

    def delete_matching_secrets_from_aws_accounts(
        self,
        secrets: list[str] | None = None,
        execution_role_arns: list[str] | None = None,
        role_session_name: str | None = None,
        dry_run: bool | None = None,
        exit_on_completion: bool = True,
    ):
        """Deletes matching secrets from AWS accounts

        generator=module_class: aws

        name: secrets, required: true, json_encode: true, base64_encode: false
        name: execution_role_arns, required: true, json_encode: true, base64_encode: false
        name: role_session_name, required: false, type: string
        name: dry_run, required: false, default: false"""
        if secrets is None:
            secrets = self.decode_input("secrets", required=True, decode_from_base64=False)

        if execution_role_arns is None:
            execution_role_arns = self.decode_input("execution_role_arns", required=True, decode_from_base64=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        if dry_run is None:
            dry_run = self.get_input("dry_run", required=False, default=False, is_bool=True)

        self.logger.info(
            "Deleting secrets matching '"
            + ", ".join(secrets)
            + ", from accounts: '"
            + ", ".join(execution_role_arns)
            + "'"
        )

        tic = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    self._delete_matching_secrets_from_aws_account,
                    secrets,
                    execution_role_arn=execution_role_arn,
                    role_session_name=role_session_name,
                    dry_run=dry_run,
                )
                for execution_role_arn in execution_role_arns
            ]

            client_errors = []

            for future in concurrent.futures.as_completed(futures):
                exc = future.exception()
                if isinstance(exc, Exception):
                    client_errors.append(exc)

        toc = time.perf_counter()
        self.logger.info(f"Deleting secrets {toc - tic:0.2f} seconds to run")

        if client_errors:
            raise ExceptionGroup("Failed to delete secrets from AWS accounts", client_errors)

        self.exit_run(exit_on_completion=exit_on_completion)

    def cleanup_aws_peering_connections(
        self, execution_role_arn: Optional[str] = None, exit_on_completion: bool = True
    ):
        """Cleans up AWS peering connections

        generator=module_class: aws

        name: execution_role_arn, required: false, type: string"""
        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        self.logger.info(
            "Cleaning up AWS peering connections" + f" for {execution_role_arn}"
            if not utils.is_nothing(execution_role_arn)
            else ""
        )

        ec2 = self.ds.get_aws_client(client_name="ec2", execution_role_arn=execution_role_arn)

        self.logger.info("Checking for peering connections")
        peering_connections = ec2.describe_vpc_peering_connections(
            Filters=[
                {
                    "Name": "status-code",
                    "Values": [
                        "active",
                    ],
                },
            ]
        )["VpcPeeringConnections"]

        for peering_connection in peering_connections:
            skip_deletion = False

            peering_connection_id = peering_connection["VpcPeeringConnectionId"]
            tags = peering_connection["Tags"]

            for tag in tags:
                if tag["Key"] == "Cleanup" and tag["Value"] == "false":
                    skip_deletion = True

            if skip_deletion:
                self.logger.info(f"Skipping deletion of {peering_connection_id}")
            else:
                self.logger.info(f"Deleting peering connection ID: {peering_connection_id}")

                response = ec2.delete_vpc_peering_connection(VpcPeeringConnectionId=peering_connection_id)

                if response["Return"]:
                    self.logger.info("Success!")
                else:
                    self.logger.info("Failure :(")

        self.logger.info("Checking for blackhole routes")

        rts = ec2.describe_route_tables()["RouteTables"]

        for rt in rts:
            route_table_id = rt["RouteTableId"]

            routes = rt["Routes"]

            for route in routes:
                state = route["State"]
                if state == "blackhole":
                    self.logger.info(f"Deleting blackhole route '{route}' in route table '{route_table_id}'")
                    ec2.delete_route(
                        DestinationCidrBlock=route["DestinationCidrBlock"],
                        RouteTableId=route_table_id,
                    )

        return self.exit_run(exit_on_completion=exit_on_completion)

    def poll_aws_autoscaling_group(
        self,
        group_name: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        timeout: Optional[int] = None,
        interval: Optional[int] = None,
        exit_on_completion: bool = True,
    ):
        """Polls an AWS autoscaling group

        generator=module_class: aws

        name: group_name, required: true, type: string
        name: execution_role_arn, required: false, type: string
        name: timeout, required: false, default: 300
        name: interval, required: false, default: 5"""
        if group_name is None:
            group_name = self.get_input("group_name", required=True)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if timeout is None:
            timeout = self.get_input("timeout", required=False, default=300, is_integer=True)

        if interval is None:
            interval = self.get_input("interval", required=False, default=5, is_integer=True)

        self.logger.info(
            f"Polling autoscaling group {group_name}" + f" for {execution_role_arn}"
            if not utils.is_nothing(execution_role_arn)
            else ""
        )

        autoscaling = self.ds.get_aws_client(client_name="autoscaling", execution_role_arn=execution_role_arn)

        try:
            refresh = autoscaling.describe_instance_refreshes(AutoScalingGroupName=group_name, MaxRecords=1)[
                "InstanceRefreshes"
            ][0]
        except KeyError:
            self.logger.warning(f"No refreshes triggered for {group_name}")
            return self.exit_run(exit_on_completion=exit_on_completion)

        elapsed = 0

        while refresh["Status"] not in ["Successful", "Failed", "Cancelled"]:
            self.logger.info(
                f"Instance Refresh {refresh['Status']} "
                f"[{refresh.get('PercentageComplete', 0)}%]: "
                f"{refresh.get('StatusReason', '')}"
            )

            elapsed += interval
            if elapsed > timeout:
                self.errors.append(f"{group_name} instance refresh timed out after {timeout} seconds")
                break

            time.sleep(interval)

            refresh = autoscaling.describe_instance_refreshes(
                AutoScalingGroupName=group_name,
                InstanceRefreshIds=[refresh["InstanceRefreshId"]],
            )["InstanceRefreshes"][0]

        try:
            self.logger.info(f"Instance Refresh {refresh['Status']} at {refresh['EndTime']}")
        except KeyError:
            self.logged_statement("Instance Refresh failed", json_data=refresh, log_level="error")

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_aws_s3_bucket(
        self,
        bucket_name: Optional[str] = None,
        acl: Optional[str] = None,
        object_ownership: Optional[str] = None,
        enable_versioning: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Creates an AWS S3 bucket

        generator=module_class: aws

        name: bucket_name, required: true, type: string
        name: acl, required: false, type: string
        name: object_ownership, required: false, default: BucketOwnerEnforced
        name: enable_versioning, required: false, default: false
        """
        if bucket_name is None:
            bucket_name = self.get_input("bucket_name", required=True)

        if acl is None:
            acl = self.get_input("acl", required=False)

        if object_ownership is None:
            object_ownership = self.get_input("object_ownership", required=False, default="BucketOwnerEnforced")

        if enable_versioning is None:
            enable_versioning = self.get_input("enable_versioning", required=False, default=False, is_bool=True)

        s3 = self.ds.get_aws_resource(service_name="s3")
        bucket = s3.Bucket(bucket_name)
        creation_date = bucket.creation_date
        if creation_date:
            self.logger.info(f"Bucket already created at {creation_date}")
        else:
            self.logger.info(f"Creating AWS bucket {bucket_name}")
            opts = {}
            if acl in [
                "private",
                "public-read",
                "public-read-write",
                "authenticated-read",
            ]:
                opts["ACL"] = acl
            elif not utils.is_nothing(acl):
                raise RuntimeError(f"ACL {acl} is invalid for S3 bucket {bucket_name}")

            if object_ownership in [
                "BucketOwnerPreferred",
                "ObjectWriter",
                "BucketOwnerEnforced",
            ]:
                opts["ObjectOwnership"] = object_ownership
            elif not utils.is_nothing(object_ownership):
                raise RuntimeError(f"Object ownership {object_ownership} is invalid for S3 bucket {bucket_name}")

            bucket.create(**opts)
            bucket.wait_until_exists()

        if enable_versioning:
            self.logger.info(f"Enabling versioning for {bucket_name}")
            bucket_versioning = bucket.Versioning()
            bucket_versioning.enable()

        self.exit_run(exit_on_completion=exit_on_completion)

    def activate_cost_explorer_tags(
        self,
        tag: Optional[str] = None,
        tags: Optional[list[str]] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Activates at least one cost explorer tag

        generator=module_class: aws

        name: tag, required: false, type:string
        name: tags, required: false, default: [], json_encode: true
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        """
        if tag is None:
            tag = self.get_input("tag", required=False)

        if tags is None:
            tags = self.decode_input(
                "tags",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        tags = set(tags)
        tags.add(tag)
        tags = utils.all_non_empty(*tags)

        if utils.is_nothing(tags):
            self.logger.warning("No tags to activate")
            return self.exit_run(exit_on_completion=exit_on_completion)

        self.logger.info(f"Activating cost explorer tag(s): {tags}")

        ce = self.ds.get_aws_client(
            client_name="ce",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        found_tags = {}

        def get_tags(last_token: Optional[str] = None):
            kwargs = utils.get_aws_call_params(TagKeys=tags, NextToken=last_token)
            results = ce.list_cost_allocation_tags(**kwargs)

            for t in results.get("CostAllocationTags", []):
                found_tags[t["TagKey"]] = t

            return results.get("NextToken")

        next_token = get_tags()

        while not utils.is_nothing(next_token):
            self.logger.info("Still more users to get...")
            next_token = get_tags(next_token)

        self.logged_statement("Found tags", json_data=found_tags)

        tags_diff = set(tags) - set(found_tags.keys())

        if tags_diff:
            self.logger.warning(f"Some tags cannot be activated yet: {tags_diff}")

        update_batch = []
        errors = []
        for k, v in found_tags.items():
            if v["Status"] == "Active":
                self.logger.info(f"Skipping already active tag {k}")
                continue

            self.logger.info(f"Activating tag {k}")
            update_batch.append(
                dict(
                    TagKey=k,
                    Status="Active",
                )
            )

            if len(update_batch) == 20:
                self.logger.info("Updating the next batch of tags")
                errors.extend(ce.update_cost_allocation_tags_status(CostAllocationTagsStatus=update_batch)["Errors"])
                update_batch = []

        if update_batch:
            self.logger.info("Updating the remaining batch of tags")
            errors.extend(ce.update_cost_allocation_tags_status(CostAllocationTagsStatus=update_batch)["Errors"])

        for error in errors:
            self.errors.append("[{Code}] Error while updating cost allocation tag {TagKey}: {Message}".format(**error))

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_s3_bucket_sizes_report(
        self,
        report_file: Optional[FilePath] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Creates an S3 bucket sizes report for an AWS account

        generator=module_class: aws

        name: report_file, required: true, type: string
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        """
        if report_file is None:
            report_file = self.get_input("report_file", required=True)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        local_report_file = self.local_path(file_path=report_file)
        local_report_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Saving a report of S3 bucket sizes to {local_report_file}")

        s3_bucket_sizes = []
        for bucket_name, storage_classes in self.ds.get_aws_s3_bucket_sizes_in_account(
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            exit_on_completion=False,
        ).items():
            avg_total_size = 0
            bucket_size_data = {
                "Bucket Name": bucket_name,
            }

            for storage_type in self.ds.S3_STORAGE_TYPES:
                avg_total_size += storage_classes.get(storage_type, 0)

            bucket_size_data["Total"] = humanize.naturalsize(avg_total_size)
            s3_bucket_sizes.append(bucket_size_data)

        self.logger.info("Turning the bucket sizes into a CSV")
        df = pd.DataFrame(s3_bucket_sizes)
        df.to_csv(local_report_file)

        self.exit_run(exit_on_completion=exit_on_completion)

    def purge_all_matching_s3_buckets(
        self,
        name_tags: Optional[list[str]] = None,
        names: Optional[list[str]] = None,
        purge_file: Optional[FilePath] = None,
        exit_on_completion: bool = True,
    ):
        """Purges all matching S3 buckets

        generator=module_class: aws

        name: name_tags, required: false, default: [], json_encode: true
        name: names, required: false, default: [], json_encode: true
        name: purge_file, required: false, type: string
        """
        if name_tags is None:
            name_tags = self.decode_input(
                "name_tags",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if names is None:
            names = self.decode_input(
                "names",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if purge_file is None:
            purge_file = self.get_input("purge_file", required=False)

        if not utils.is_nothing(purge_file):
            local_purge_file = self.local_path(purge_file)
            if not local_purge_file.exists():
                raise FileNotFoundError(f"Purge file {local_purge_file} does not exist to read from")

            purge_file_data = self.get_file(file_path=local_purge_file)
            names.extend(purge_file_data.get("names", []))
            name_tags.extend(purge_file_data.get("name_tags", []))
            force_purge = utils.strtobool(purge_file_data.get("force", False))

            if force_purge:
                self.logger.warning("Force-purging all files in buckets")

        self.logger.info(f"Purging all matching S3 buckets in each AWS account, names: {names}, name tags: {name_tags}")
        aws_accounts = self.ds.get_gitops_repository_file(
            file_path="records/metadata/networked_accounts_by_json_key.json"
        )

        def bucket_name_matches(bn: str):
            if bn in names:
                return True

            for nt in name_tags:
                if nt in bn:
                    return True

            return False

        def expire_bucket_objects(bucket):
            bucket_name = bucket.name
            bucket_lifecycle_configuration = None

            try:
                bucket_versioning = bucket.Versioning()
                if bucket_versioning.status == "Enabled":
                    self.logger.warning("Suspending versioning for the bucket")
                    bucket_versioning.suspend()

                bucket_lifecycle_configuration = bucket.LifecycleConfiguration()
                expected_rules = {
                    "FullDelete",
                    "DeleteMarkers",
                }

                bucket_rules = {rule["ID"] for rule in bucket_lifecycle_configuration.rules}

                orphan_rules = bucket_rules - expected_rules

                if utils.is_nothing(orphan_rules):
                    self.logger.info(f"{bucket_name} already has the expected lifecycle rules: {expected_rules}")
                    return

                self.logger.warning(
                    f"Bucket {bucket_name} has orphan lifecycle rule(s): {orphan_rules}, replacing them"
                )
                bucket_lifecycle_configuration.delete()
            except botocore.exceptions.ClientError:
                self.logger.info(f"No existing lifecycle configuration for the bucket: {bucket_name}")

            if bucket_lifecycle_configuration is None:
                bucket_lifecycle_configuration = bucket.LifecycleConfiguration()

            return bucket_lifecycle_configuration.put(
                LifecycleConfiguration={
                    "Rules": [
                        {
                            "Expiration": {"Days": 1},
                            "ID": "FullDelete",
                            "Filter": {"Prefix": ""},
                            "Status": "Enabled",
                            "NoncurrentVersionExpiration": {"NoncurrentDays": 1},
                            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1},
                        },
                        {
                            "Expiration": {"ExpiredObjectDeleteMarker": True},
                            "ID": "DeleteMarkers",
                            "Filter": {"Prefix": ""},
                            "Status": "Enabled",
                        },
                    ]
                },
            )

        def purge_matching_buckets_for_account(jk: str, ad: Any):
            self.logger.info(f"Purging matching S3 buckets for {jk}")
            s3 = self.ds.get_aws_resource(service_name="s3", execution_role_arn=ad.get("execution_role_arn"))

            for bucket in s3.buckets.all():
                bucket_name = bucket.name
                if not bucket_name_matches(bucket_name):
                    self.logger.info(f"{bucket_name} not a match, skipping")
                    continue

                self.logger.info(f"{bucket_name} matches any of names: {names}, or name tags: {name_tags}")

                if force_purge:
                    self.logger.warning(f"Force-purging all objects in {bucket_name}")
                    bucket_versioning = s3.BucketVersioning(bucket_name)
                    if bucket_versioning.status == "Enabled":
                        bucket.object_versions.delete()
                    else:
                        bucket.objects.all().delete()

                self.logger.warning(f"Attempting to delete {bucket_name}")
                try:
                    bucket.delete()
                    self.logger.info(f"Successfully purged {bucket_name}")
                except botocore.exceptions.ClientError as exc:
                    if exc.response["Error"]["Code"] == "BucketNotEmpty":
                        self.logger.warning(
                            f"{bucket_name} is not yet empty, pushing a 1 day expiration policy for bucket"
                        )
                        expire_bucket_objects(bucket)
                    else:
                        raise FailedResponseError(exc, f"Failed to delete bucket {bucket_name}")

        tic = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []

            for json_key, account_data in aws_accounts.items():
                futures.append(executor.submit(purge_matching_buckets_for_account, json_key, account_data))

            for future in concurrent.futures.as_completed(futures):
                exc = future.exception()
                if exc is not None:
                    executor.shutdown(wait=False, cancel_futures=True)
                    if isinstance(exc, botocore.exceptions.ClientError):
                        raise FailedResponseError(exc, "Failed to purge buckets") from exc

                    raise RuntimeError(f"Failed to purge buckets") from exc

        toc = time.perf_counter()
        self.logger.info(f"Purging S3 buckets took {toc - tic:0.2f} seconds to run")

        self.exit_run(exit_on_completion=exit_on_completion)

    def name_tag_all_s3_buckets_in_account(
        self,
        name_tag: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Tags all S3 buckets in an AWS account

        generator=module_class: aws

        name: name_tag, required: false, default: s3-bucket-name
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        """
        if name_tag is None:
            name_tag = self.get_input("name_tag", required=False, default="s3-bucket-name")

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        self.logger.info(f"Tagging all S3 buckets in the AWS account with their bucket name using tag {name_tag}")

        s3 = self.ds.get_aws_resource(
            service_name="s3",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        for s3_bucket in s3.buckets.all():
            s3_bucket_name = s3_bucket.name
            self.logger.info(f'Setting tag "{name_tag}" in "{s3_bucket_name}" to "{s3_bucket_name}"...')

            bucket_tagging = s3.BucketTagging(s3_bucket_name)
            try:
                tags = bucket_tagging.tag_set
            except botocore.exceptions.ClientError:
                tags = [{"Key": name_tag, "Value": s3_bucket_name}]

            if len([x for x in tags if x["Key"] == name_tag]) == 0:
                tags.append({"Key": name_tag, "Value": s3_bucket_name})

            self.logger.info(f"Setting tags for {s3_bucket_name} to: {tags}")
            bucket_tagging.put(Tagging={"TagSet": tags})

        self.logger.info(f"Activating {name_tag} as a cost allocation tag")
        self.activate_cost_explorer_tags(
            tag=name_tag,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            exit_on_completion=False,
        )

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_codedeploy_deployment(
        self,
        application_name: Optional[str] = None,
        deployment_group_name: Optional[str] = None,
        task_definition_arn: Optional[str] = None,
        container_name: Optional[str] = None,
        container_port: Optional[int] = None,
        poll_delay: Optional[int] = None,
        max_attempts: Optional[int] = None,
        execution_role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """Creates a CodeDeploy deployment

        generator=module_class: aws

        name: application_name, required: true, type: string
        name: deployment_group_name, required: true, type: string
        name: task_definition_arn, required: true, type: string
        name: container_name, required: true, type: string
        name: container_port, required: true, type: number
        name: poll_delay, required: false, default: 15
        name: max_attempts, required: false, default: 120
        name: execution_role_arn, required: false, type: string
        name: role_session_name, required: false, type: string
        """
        if application_name is None:
            application_name = self.get_input(
                "application_name",
                required=True,
            )

        if deployment_group_name is None:
            deployment_group_name = self.get_input(
                "deployment_group_name",
                required=True,
            )

        if task_definition_arn is None:
            task_definition_arn = self.get_input(
                "task_definition_arn",
                required=True,
            )

        if container_name is None:
            container_name = self.get_input(
                "container_name",
                required=True,
            )

        if container_port is None:
            container_port = self.get_input(
                "container_port",
                required=True,
                is_integer=True,
            )

        if poll_delay is None:
            poll_delay = self.get_input("poll_delay", required=False, default=15, is_integer=True)

        if max_attempts is None:
            max_attempts = self.get_input("max_attempts", required=False, default=60, is_integer=True)

        if execution_role_arn is None:
            execution_role_arn = self.get_input("execution_role_arn", required=False)

        if role_session_name is None:
            role_session_name = self.get_input("role_session_name", required=False)

        self.logger.info(
            f"Creating a new CodeDeploy deployment for {application_name} in deployment group {deployment_group_name}"
        )

        code_deploy = self.ds.get_aws_client(
            client_name="codedeploy",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )

        waiter = code_deploy.get_waiter("deployment_successful")

        def wait_for_deployment(di: str):
            try:
                waiter.wait(
                    deploymentId=di,
                    WaiterConfig={
                        "Delay": poll_delay,
                        "MaxAttempts": max_attempts,
                    },
                )
            except botocore.exceptions.WaiterError as exc:
                raise RuntimeError(f"Deployment {di} failed to become successful") from exc

        self.logger.info("Checking for in-progress deployments first...")
        try:
            in_progress_deployments = self.ds.get_aws_codedeploy_deployments(
                application_name=application_name,
                deployment_group_name=deployment_group_name,
                include_only=[
                    "InProgress",
                ],
                execution_role_arn=execution_role_arn,
                role_session_name=role_session_name,
                raise_on_error=True,
                exit_on_completion=False,
            )
        except botocore.exceptions.ClientError as exc:
            raise RuntimeError("Client error when checking for in-progress deployments") from exc

        for deployment_id in in_progress_deployments:
            self.logger.warning(f"In-progress deployment {deployment_id} needs to finish first...")
            wait_for_deployment(deployment_id)

        app_spec = {
            "version": 0.0,
            "Resources": [
                {
                    "TargetService": {
                        "Type": "AWS::ECS::Service",
                        "Properties": {
                            "TaskDefinition": task_definition_arn,
                            "LoadBalancerInfo": {
                                "ContainerName": container_name,
                                "ContainerPort": container_port,
                            },
                        },
                    }
                }
            ],
        }

        self.logged_statement("AppSpec", json_data=app_spec)

        app_spec_str = json.dumps(app_spec)
        app_spec_hash = hashlib.sha256(app_spec_str.encode()).hexdigest()

        deployment = code_deploy.create_deployment(
            applicationName=application_name,
            deploymentGroupName=deployment_group_name,
            revision={
                "revisionType": "AppSpecContent",
                "appSpecContent": {
                    "content": app_spec_str,
                    "sha256": app_spec_hash,
                },
            },
            autoRollbackConfiguration={
                "enabled": True,
                "events": [
                    "DEPLOYMENT_FAILURE",
                    "DEPLOYMENT_STOP_ON_ALARM",
                    "DEPLOYMENT_STOP_ON_REQUEST",
                ],
            },
        )

        deployment_id = deployment.get("deploymentId")
        if not deployment_id:
            raise RuntimeError("AWS did not return a deployment ID for the new deployment")

        self.logger.info(f"New deployment {deployment_id} created, waiting for it to succeed...")
        wait_for_deployment(deployment_id)

        return self.exit_run(exit_on_completion=exit_on_completion)

    def sync_flipsidecrypto_rev_ops_groups(self, exit_on_completion: bool = True):
        """Syncs FlipsideCrypto Rev-Ops groups

        generator=module_class: groups
        """
        group_leader = "simon@flipsidecrypto.com"
        ts_format = "%-m/%-d/%Y %-H:%-M:%-S"

        rev_ops_groups = {}

        self.logger.info("Finding the groups actively owned by Rev-Ops")
        for group_name, group_data in self.ds.get_google_groups(unhump_groups=True, exit_on_completion=False).items():

            def get_group_members():
                gm = []
                for member_email, member_data in group_data["members"].items():
                    if member_email == group_leader:
                        if member_data["role"] != "OWNER":
                            self.logger.warning(f"Skipping non-rev-ops group {group_name}")
                            return None

                        continue

                    gm.append(member_email)

                return gm

            group_members = get_group_members()
            if not utils.is_nothing(group_members):
                rev_ops_groups[group_name] = group_members

        self.logger.info("Syncing FlipsideCrypto rev-ops groups")

        google_client = GoogleClient(**self.kwargs)
        sheets_client = gspread.Client(auth=google_client.credentials)
        worksheets = sheets_client.open_by_key("1sk2CbxcbaQmXjK7LcpurqHEwfYKRVE0aB--hdEf4OCo")
        sheet = worksheets.sheet1
        rows = sheet.get(return_type=GridRangeType.ListOfLists)

        if utils.is_nothing(rows):
            raise RuntimeError("Headers are missing from rev-ops worksheet")

        duplicate_rev_ops_groups = utils.get_default_dict()
        duplicate_raw_rev_ops_groups = utils.get_default_dict()
        new_rev_ops_groups = []
        registered_rev_ops_groups = set()

        for row in rows[1:]:
            group_name = row[2]
            group_members = row[3].split(os.linesep)

            if group_name not in rev_ops_groups:
                self.logger.info("New rev-ops group!")
                rev_ops_groups[group_name] = group_members
                new_rev_ops_groups.append(row)
                registered_rev_ops_groups.add(group_name)
                continue

            ts = row[0]
            duplicate_rev_ops_groups[group_name][ts] = group_members
            duplicate_raw_rev_ops_groups[group_name][ts] = row

        self.logger.info("Going through duplicate groups")
        for group_name, duplicates in duplicate_rev_ops_groups.items():
            newest_members = rev_ops_groups.get(group_name, [])
            newest_ts = None
            newest_ts_raw = None

            for ts, group_members in duplicates.items():
                ts_as_time = datetime.strptime(ts, ts_format)

                if newest_ts is None or newest_ts < ts_as_time:
                    newest_ts = ts_as_time
                    newest_ts_raw = ts
                    newest_members = group_members

            if newest_ts is None or newest_ts_raw is None:
                raise RuntimeError(f"{group_name} failed to process timestamps for its duplicates")

            rev_ops_groups[group_name] = newest_members
            new_rev_ops_groups.append(duplicate_raw_rev_ops_groups[group_name][newest_ts_raw])
            registered_rev_ops_groups.add(group_name)

        self.logger.info(f"Found rev-ops groups: {", ".join(rev_ops_groups.keys())}")
        self.log_results(rev_ops_groups, "rev-ops groups")

        if len(rows) > 1:
            self.logger.warning("Wiping the existing sheet data")
            sheet.delete_rows(2, len(rows))

        self.logger.info("Syncing rev-ops groups")
        for group_name, group_members in rev_ops_groups.items():
            if group_name in registered_rev_ops_groups:
                continue

            dt = datetime.now()
            ts = dt.strftime(ts_format)
            new_rev_ops_groups.append(
                [
                    ts,
                    "internal-tooling-bot@flipsidecrypto.com",
                    group_name,
                    os.linesep.join(group_members),
                ]
            )

        sheet.update(new_rev_ops_groups, "A2")

        self.exit_run(exit_on_completion=exit_on_completion)

    def build_state_file_for_workspace_from_aws_s3_state_files(
        self,
        workspace_dir: Optional[FilePath] = None,
        state_files: list[Optional[FilePath]] = None,
        s3_bucket: Optional[str] = None,
        fail_on_not_found: Optional[bool] = None,
        exit_on_completion: bool = True,
    ):
        """Builds the state file for a Terraform workspace from AWS S3 state files

        generator=key: state, module_class: terraform

        name: workspace_dir, required: true, type: string
        name: state_files, required: true, json_encode: true
        name: s3_bucket, required: false, default: flipside-crypto-internal-tooling
        name: fail_on_not_found, required: false, default: false
        """
        if workspace_dir is None:
            workspace_dir = self.get_input("workspace_dir", required=True)

        if state_files is None:
            state_files = self.decode_input(
                "state_files",
                required=True,
                decode_from_base64=False,
            )

        if s3_bucket is None:
            s3_bucket = self.get_input("s3_bucket", required=False, default="flipside-crypto-internal-tooling")

        if fail_on_not_found is None:
            fail_on_not_found = self.get_input("fail_on_not_found", required=False, default=False, is_bool=True)

        self.logger.info(f"Building the state file for {workspace_dir}")
        state_data = self.ds.merge_aws_s3_terraform_state_files(
            state_files=state_files,
            s3_bucket=s3_bucket,
            fail_on_not_found=False,
            exit_on_completion=False,
        )

        if utils.is_nothing(state_data):
            report = f"Could not merge state data from the provided state files: {state_files}"
            if fail_on_not_found:
                self.errors.append(report)
            else:
                self.logger.warning(report)

            return self.exit_run(exit_on_completion=exit_on_completion)

        repository_workspace_dir = self.get_repository_dir(workspace_dir)
        self.logger.info(f"Saving the generated terraform.tfstate to {repository_workspace_dir}")
        self.permanent_record(
            records_dir=repository_workspace_dir,
            records_file_name="terraform",
            records_file_ext=".tfstate",
            records=state_data,
            workspace_dir=workspace_dir,
            exit_on_completion=False,
        )

        return self.exit_run(exit_on_completion=exit_on_completion)

    def assign_google_iam_roles(
        self,
        project_id: Optional[str] = None,
        roles: Optional[list[str]] = None,
        service_account_identifier: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Assigns IAM roles to a service account for a project.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: roles, required: false, json_encode: true
        name: service_account_identifier, required: false, type: string, default: "terraform@flipsidecrypto.com"
        """

        project_id = project_id or self.get_input("project_id", required=True)
        roles = roles or self.decode_input("roles", required=False, decode_from_base64=False)
        if not roles:
            roles = GCP_REQUIRED_ROLES

        service_account_identifier = service_account_identifier or self.get_input(
            "service_account_identifier",
            required=False,
            default="terraform@flipsidecrypto.com",
        )

        if not service_account_identifier.startswith("serviceAccount:"):
            service_account_identifier = f"serviceAccount:{service_account_identifier}"

        google_client = self.ds.get_google_client()
        resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        # Assign roles
        for role in roles:
            try:
                resource_manager.projects().setIamPolicy(
                    resource=project_id,
                    body={
                        "policy": {
                            "bindings": [
                                {
                                    "role": role,
                                    "members": [service_account_identifier],
                                }
                            ]
                        }
                    },
                ).execute()
                self.logger.info(
                    f"Assigned role '{role}' to '{service_account_identifier}' for project '{project_id}'."
                )
            except Exception as e:
                self.logger.error(f"Failed to assign role '{role}': {e}")

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_google_kms_key(
        self,
        project_id: Optional[str] = None,
        kms_keyring_name: Optional[str] = None,
        kms_key_name: Optional[str] = None,
        region: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Creates a KMS keyring and key if they do not already exist.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: kms_keyring_name, required: true, type: string
        name: kms_key_name, required: true, type: string
        name: region, required: false, type: string, default: "us-east1"
        """

        project_id = project_id or self.get_input("project_id", required=True)
        kms_keyring_name = kms_keyring_name or self.get_input("kms_keyring_name", required=True)
        kms_key_name = kms_key_name or self.get_input("kms_key_name", required=True)
        region = region or self.get_input("region", required=False) or "us-east1"

        google_client = self.ds.get_google_client()
        kms = google_client.get_service("cloudkms", "v1")

        # Create keyring
        try:
            kms.projects().locations().keyRings().create(
                parent=f"projects/{project_id}/locations/{region}",
                keyRingId=kms_keyring_name,
                body={},
            ).execute()
            self.logger.info(f"Created KMS keyring '{kms_keyring_name}' in region '{region}'.")
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 409:
                self.logger.info(f"KMS keyring '{kms_keyring_name}' already exists.")
            else:
                self.logger.error(f"Failed to create KMS keyring '{kms_keyring_name}': {e}")
                raise

        # Create key
        try:
            kms.projects().locations().keyRings().cryptoKeys().create(
                parent=f"projects/{project_id}/locations/{region}/keyRings/{kms_keyring_name}",
                cryptoKeyId=kms_key_name,
                body={"purpose": "ENCRYPT_DECRYPT"},
            ).execute()
            self.logger.info(f"Created KMS key '{kms_key_name}'.")
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 409:
                self.logger.info(f"KMS key '{kms_key_name}' already exists.")
            else:
                self.logger.error(f"Failed to create KMS key '{kms_key_name}': {e}")
                raise

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_google_project(
        self,
        project_name: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        exit_on_completion: bool = True,
    ):
        """
        Creates a GCP project by name if it does not already exist.

        generator=module_class: google

        name: project_name, required: true, type: string
        name: labels, required: false, json_encode: true
        """

        project_name = project_name or self.get_input("project_name", required=True)
        labels = labels or self.decode_input("labels", required=False)
        if not labels:
            labels = GCP_SECURITY_PROJECT.get("resource_labels", {})

        # Get Google Client and Resource Manager service
        google_client = self.ds.get_google_client()
        resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        # Search for the project by name
        project_id = None
        try:
            response = resource_manager.projects().list(filter=f"name:{project_name}").execute()
            projects = response.get("projects", [])
            if projects:
                project_id = projects[0]["projectId"]
                self.logger.info(f"Project '{project_name}' already exists with ID '{project_id}'.")
            else:
                self.logger.info(f"No existing project found with name '{project_name}'.")
        except Exception as e:
            self.logger.error(f"Failed to search for project '{project_name}': {e}")
            raise

        # If the project does not exist, create it
        if not project_id:
            self.logger.info(f"Creating project '{project_name}'...")
            try:
                create_response = (
                    resource_manager.projects()
                    .create(
                        body={
                            "projectId": project_name.lower().replace(" ", "-"),
                            "name": project_name,
                            "labels": labels,
                        }
                    )
                    .execute()
                )
                project_id = create_response["projectId"]
                self.logger.info(f"Project '{project_name}' created successfully with ID '{project_id}'.")
            except Exception as e:
                self.logger.error(f"Failed to create project '{project_name}': {e}")
                raise
        else:
            # Check and update labels if necessary
            current_labels = projects[0].get("labels", {})
            if current_labels != labels:
                self.logger.info(f"Updating labels for project '{project_name}'...")
                try:
                    resource_manager.projects().update(projectId=project_id, body={"labels": labels}).execute()
                    self.logger.info(f"Labels updated for project '{project_name}'.")
                except Exception as e:
                    self.logger.error(f"Failed to update labels for project '{project_name}': {e}")
                    raise

        return self.exit_run(
            results=project_id,
            format_results=False,
            key="project_id",
            exit_on_completion=exit_on_completion,
        )

    def enable_google_apis(
        self,
        project_id: Optional[str] = None,
        apis: Optional[list[str]] = None,
        exit_on_completion: bool = True,
    ):
        """
        Enables required APIs for the project.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: apis, required: false, json_encode: true
        """

        project_id = project_id or self.get_input("project_id", required=True)
        apis = apis or self.decode_input("apis", required=False, decode_from_base64=False)
        if not apis:
            apis = GCP_REQUIRED_APIS

        google_client = self.ds.get_google_client()
        service_usage = google_client.get_service("serviceusage", "v1")

        enabled_apis = []
        failed_apis = []
        service_usage_disabled = False

        for api in apis:
            if api == "serviceusage.googleapis.com":
                self.logger.warning("Skipping serviceusage.googleapis.com as it cannot enable itself")
                continue

            if service_usage_disabled:
                failed_apis.append(api)
                continue

            try:
                service_usage.services().enable(name=f"projects/{project_id}/services/{api}").execute()
                self.logger.info(f"Enabled API: {api}")
                enabled_apis.append(api)
            except Exception as e:
                if "has already been enabled" in str(e):
                    self.logger.info(f"API already enabled: {api}")
                    enabled_apis.append(api)
                else:
                    self.logger.error(f"Failed to enable API '{api}': {e}")
                    failed_apis.append(api)
                    # If we can't use service usage API, no point trying the rest
                    if "serviceusage" in str(e).lower():
                        self.logger.error("serviceusage API appears to be disabled - skipping remaining APIs")
                        service_usage_disabled = True

        return self.exit_run(
            results={"enabled_apis": enabled_apis, "failed_apis": failed_apis},
            key="enabled_apis",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def assign_google_project_iam_roles(
        self,
        project_id: Optional[str] = None,
        roles: Optional[list[str]] = None,
        service_account_identifier: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Assigns IAM roles to a service account in the specified project.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: roles, required: false, json_encode: true
        name: service_account_identifier, required: false, type: string
        """

        # Decode inputs
        project_id = project_id or self.get_input("project_id", required=True)
        roles = roles or self.decode_input("roles", required=False, decode_from_base64=False)
        if not roles:
            roles = GCP_REQUIRED_ROLES

        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Initialize Google client
        google_client = self.ds.get_google_client(service_account_file=service_account_file)

        # Use provided service account identifier or default to the client subject
        if not service_account_identifier:
            service_account_identifier = google_client.subject
            if not service_account_identifier:
                raise ValueError("Service account identifier could not be resolved.")

        # Ensure the identifier is correctly formatted
        if not service_account_identifier.startswith("serviceAccount:"):
            service_account_identifier = f"serviceAccount:{service_account_identifier}"

        resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        # Assign roles
        for role in roles:
            try:
                resource_manager.projects().setIamPolicy(
                    resource=project_id,
                    body={
                        "policy": {
                            "bindings": [
                                {
                                    "role": role,
                                    "members": [service_account_identifier],
                                }
                            ]
                        }
                    },
                ).execute()
                self.logger.info(f"Assigned role '{role}' to '{service_account_identifier}' in project '{project_id}'.")
            except Exception as e:
                self.logger.error(f"Failed to assign role '{role}' to '{service_account_identifier}': {e}")
                raise

        return self.exit_run(exit_on_completion=exit_on_completion)

    def assign_service_account_to_google_organization(
        self,
        organization_id: Optional[str] = None,
        service_account_email: Optional[str] = None,
        roles: Optional[list[str]] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Assigns specific IAM roles to a service account in the target Google Cloud organization.

        generator=module_class: google

        name: organization_id, required: false, type: string
        name: service_account_email, required: false, type: string
        name: roles, required: false, json_encode: true
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Decode inputs
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)
        organization_id = organization_id or self.get_input("organization_id", required=False)
        roles = roles or self.decode_input("roles", required=False, decode_from_base64=False)
        if not roles:
            roles = GCP_REQUIRED_ORGANIZATION_ROLES

        # Resolve organization ID
        if not organization_id:
            self.logger.info("No organization ID provided. Attempting to resolve organization ID dynamically...")
            organization_id = self.ds.get_google_organization_id(
                service_account_file=service_account_file,
                exit_on_completion=False,
            )
            if not organization_id:
                raise ValueError("Organization ID could not be resolved and is required.")

        # Initialize Google client and services
        google_client = self.ds.get_google_client(service_account_file=service_account_file)
        resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        # Resolve service account email
        if not service_account_email:
            service_account_email = google_client.subject
            if not service_account_email:
                raise ValueError("Service account email could not be resolved and is required.")

        # Ensure the service account identifier is properly formatted
        if not service_account_email.startswith("serviceAccount:"):
            service_account_email = f"serviceAccount:{service_account_email}"

        # Fetch the current IAM policy for the organization
        try:
            self.logger.info(f"Fetching current IAM policy for organization '{organization_id}'...")
            current_policy = (
                resource_manager.organizations()
                .getIamPolicy(resource=f"organizations/{organization_id}", body={})
                .execute()
            )
        except Exception as e:
            self.logger.error(f"Failed to fetch IAM policy for organization '{organization_id}': {e}")
            raise

        # Check if all roles are already assigned
        bindings = current_policy.get("bindings", [])
        all_roles_assigned = True
        for role in roles:
            role_binding = next((b for b in bindings if b["role"] == role), None)
            if role_binding and service_account_email in role_binding.get("members", []):
                self.logger.info(
                    f"Service account '{service_account_email}' already has role '{role}' in organization '{organization_id}'."
                )
            else:
                self.logger.info(
                    f"Service account '{service_account_email}' does not have role '{role}' in organization '{organization_id}'."
                )
                all_roles_assigned = False

        # Short-circuit if all roles are already assigned
        if all_roles_assigned:
            self.logger.info(
                f"All specified roles are already assigned to '{service_account_email}' in organization '{organization_id}'. Exiting."
            )
            return self.exit_run(
                results={
                    "organization_id": organization_id,
                    "roles_already_assigned": roles,
                    "service_account_email": service_account_email,
                },
                key="organization_iam_role_assignment",
                format_results=True,
                exit_on_completion=exit_on_completion,
            )

        # Update IAM policy with new roles
        for role in roles:
            role_binding = next((b for b in bindings if b["role"] == role), None)
            if role_binding:
                if service_account_email not in role_binding.get("members", []):
                    role_binding["members"].append(service_account_email)
            else:
                bindings.append(
                    {
                        "role": role,
                        "members": [service_account_email],
                    }
                )

        # Set organization-level IAM policy
        try:
            self.logger.info(f"Updating IAM policy for organization '{organization_id}'...")
            resource_manager.organizations().setIamPolicy(
                resource=f"organizations/{organization_id}",
                body={"policy": {"bindings": bindings}},
            ).execute()
            self.logger.info(
                f"Successfully assigned roles '{roles}' to '{service_account_email}' in organization '{organization_id}'."
            )
        except Exception as e:
            self.logger.error(f"Failed to update IAM policy for organization '{organization_id}': {e}")
            raise

        return self.exit_run(
            results={
                "organization_id": organization_id,
                "roles_assigned": roles,
                "service_account_email": service_account_email,
            },
            key="organization_iam_role_assignment",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def enable_google_organization_project_administration_policies(
        self,
        organization_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        boolean_constraints: Optional[dict] = None,
        list_constraints: Optional[dict] = None,
        exit_on_completion: bool = True,
    ):
        """
        Enables and configures organization-level policies to ensure proper project administration.

        generator=module_class: google

        name: organization_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        name: boolean_constraints, required: false, json_encode: true
        name: list_constraints, required: false, json_encode: true
        """

        # Decode inputs
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)
        organization_id = organization_id or self.get_input("organization_id", required=False)

        # Decode constraints or use defaults from settings
        boolean_constraints = (
            boolean_constraints
            or self.decode_input("boolean_constraints", required=False, decode_from_base64=False)
            or GCP_BOOLEAN_CONSTRAINTS
        )

        list_constraints = (
            list_constraints
            or self.decode_input("list_constraints", required=False, decode_from_base64=False)
            or GCP_LIST_CONSTRAINTS
        )

        # Resolve organization ID
        if not organization_id:
            self.logger.info("No organization ID provided. Attempting to resolve organization ID dynamically...")
            organization_id = self.ds.get_google_organization_id(
                service_account_file=service_account_file,
                exit_on_completion=False,
            )
            if not organization_id:
                raise ValueError("Organization ID could not be resolved and is required.")

        # Initialize Google client and services
        google_client = self.ds.get_google_client(service_account_file=service_account_file)
        org_policy_service = google_client.get_service("cloudresourcemanager", "v1")

        # Update boolean constraints
        for constraint, enforced in boolean_constraints.items():
            try:
                self.logger.info(f"Setting organization policy '{constraint}' to enforced={enforced}...")
                org_policy_service.organizations().setOrgPolicy(
                    resource=f"organizations/{organization_id}",
                    body={
                        "policy": {
                            "constraint": constraint,
                            "booleanPolicy": {"enforced": enforced},
                        }
                    },
                ).execute()
                self.logger.info(f"Successfully updated policy '{constraint}'.")
            except Exception as e:
                self.logger.error(f"Failed to update policy '{constraint}': {e}")
                raise

        # Update list constraints
        for constraint, settings in list_constraints.items():
            try:
                self.logger.info(f"Updating list constraint '{constraint}' with settings: {settings}...")
                org_policy_body = {
                    "policy": {
                        "constraint": constraint,
                    }
                }

                # Apply enforcement or allowedValues based on settings
                if "enforced" in settings:
                    org_policy_body["policy"]["listPolicy"] = {
                        "allValues": "ALLOW" if not settings["enforced"] else "DENY"
                    }
                if "allowedValues" in settings:
                    org_policy_body["policy"]["listPolicy"] = {"allowedValues": settings["allowedValues"]}

                org_policy_service.organizations().setOrgPolicy(
                    resource=f"organizations/{organization_id}",
                    body=org_policy_body,
                ).execute()
                self.logger.info(f"Successfully updated list constraint '{constraint}'.")
            except Exception as e:
                self.logger.error(f"Failed to update list constraint '{constraint}': {e}")
                raise

        return self.exit_run(
            results={
                "organization_id": organization_id,
                "policies_updated": len(boolean_constraints) + len(list_constraints),
            },
            key="organization_policies",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def enable_google_project_administration_policies(
        self,
        project_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        boolean_constraints: Optional[dict] = None,
        list_constraints: Optional[dict] = None,
        exit_on_completion: bool = True,
    ):
        """
        Enables and configures project-level policies to ensure proper administration.

        generator=module_class: google

        name: project_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        name: boolean_constraints, required: false, json_encode: true
        name: list_constraints, required: false, json_encode: true
        """

        # Decode inputs
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)
        project_id = project_id or self.get_input("project_id", required=False)

        # Decode constraints or use defaults from settings
        boolean_constraints = (
            boolean_constraints
            or self.decode_input("boolean_constraints", required=False, decode_from_base64=False)
            or GCP_BOOLEAN_CONSTRAINTS
        )

        list_constraints = (
            list_constraints
            or self.decode_input("list_constraints", required=False, decode_from_base64=False)
            or GCP_LIST_CONSTRAINTS
        )

        # Ensure project ID is provided
        if not project_id:
            raise ValueError("Project ID is required.")

        # Initialize Google client and services
        google_client = self.ds.get_google_client(service_account_file=service_account_file)
        org_policy_service = google_client.get_service("cloudresourcemanager", "v1")

        # Update boolean constraints
        for constraint, enforced in boolean_constraints.items():
            try:
                self.logger.info(f"Setting project policy '{constraint}' to enforced={enforced}...")
                org_policy_service.projects().setOrgPolicy(
                    resource=f"projects/{project_id}",
                    body={
                        "policy": {
                            "constraint": constraint,
                            "booleanPolicy": {"enforced": enforced},
                        }
                    },
                ).execute()
                self.logger.info(f"Successfully updated policy '{constraint}'.")
            except Exception as e:
                self.logger.error(f"Failed to update policy '{constraint}': {e}")
                raise

        # Update list constraints
        for constraint, settings in list_constraints.items():
            try:
                self.logger.info(f"Updating list constraint '{constraint}' with settings: {settings}...")
                org_policy_body = {
                    "policy": {
                        "constraint": constraint,
                    }
                }

                # Apply enforcement or allowedValues based on settings
                if "enforced" in settings:
                    org_policy_body["policy"]["listPolicy"] = {
                        "allValues": "ALLOW" if not settings["enforced"] else "DENY"
                    }
                if "allowedValues" in settings:
                    org_policy_body["policy"]["listPolicy"] = {"allowedValues": settings["allowedValues"]}

                org_policy_service.projects().setOrgPolicy(
                    resource=f"projects/{project_id}",
                    body=org_policy_body,
                ).execute()
                self.logger.info(f"Successfully updated list constraint '{constraint}'.")
            except Exception as e:
                self.logger.error(f"Failed to update list constraint '{constraint}': {e}")
                raise

        return self.exit_run(
            results={
                "project_id": project_id,
                "policies_updated": len(boolean_constraints) + len(list_constraints),
            },
            key="project_policies",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def assign_service_account_to_google_project(
        self,
        project_id: Optional[str] = None,
        service_account_email: Optional[str] = None,
        roles: Optional[list[str]] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Assigns specific IAM roles to a service account in the target Google Cloud project.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: service_account_email, required: false, type: string
        name: roles, required: false, json_encode: true
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Decode inputs
        project_id = project_id or self.get_input("project_id", required=True)
        roles = roles or self.decode_input("roles", required=False)
        if not roles:
            roles = GCP_REQUIRED_ROLES

        service_account_email = service_account_email or self.get_input("service_account_email", required=False)
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Initialize Google client and services
        google_client = self.ds.get_google_client(service_account_file=service_account_file)
        resource_manager = google_client.get_service("cloudresourcemanager", "v1")

        # Resolve service account email
        if not service_account_email:
            service_account_email = google_client.subject
            if not service_account_email:
                raise ValueError("Service account email could not be resolved and is required.")

        # Ensure the service account identifier is properly formatted
        if not service_account_email.startswith("serviceAccount:"):
            service_account_email = f"serviceAccount:{service_account_email}"

        # Assign roles directly
        for role in roles:
            try:
                resource_manager.projects().setIamPolicy(
                    resource=project_id,
                    body={
                        "policy": {
                            "bindings": [
                                {
                                    "role": role,
                                    "members": [service_account_email],
                                }
                            ]
                        }
                    },
                ).execute()
                self.logger.info(f"Assigned role '{role}' to '{service_account_email}' for project '{project_id}'.")
            except Exception as e:
                self.logger.error(
                    f"Failed to assign role '{role}' to '{service_account_email}' for project '{project_id}': {e}"
                )

        return self.exit_run(
            results={
                "project_id": project_id,
                "roles_assigned": roles,
                "service_account_email": service_account_email,
            },
            key="iam_role_assignment",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def link_google_billing_account(
        self,
        project_id: Optional[str] = None,
        billing_account_name: Optional[str] = None,
        billing_account_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Links the specified GCP project to a billing account.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: billing_account_name, required: false, type: string, default: "Primary"
        name: billing_account_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        project_id = project_id or self.get_input("project_id", required=True)
        billing_account_id = billing_account_id or self.get_input("billing_account_id", required=False)
        if not billing_account_id:
            billing_account_name = billing_account_name or self.get_input(
                "billing_account_name", required=False, default="Primary"
            )
            billing_account_id = self.ds.get_google_billing_account(
                billing_account_name=billing_account_name,
                service_account_file=service_account_file,
                exit_on_completion=False,
            )

        # Initialize Google Client
        google_client = self.ds.get_google_client(service_account_file=service_account_file)
        billing = google_client.get_service("cloudbilling", "v1")

        # Link the project to the billing account
        try:
            billing.projects().updateBillingInfo(
                name=f"projects/{project_id}",
                body={"billingAccountName": f"billingAccounts/{billing_account_id}"},
            ).execute()
            self.logger.info(f"Linked project '{project_id}' to billing account '{billing_account_id}'.")
        except Exception as e:
            self.logger.error(f"Failed to link project '{project_id}' to billing account '{billing_account_id}': {e}")
            raise

        return self.exit_run(exit_on_completion=exit_on_completion)

    def delete_empty_google_project(
        self,
        project_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ) -> bool:
        """
        Deletes a Google Cloud project if it is determined to be empty.

        generator=module_class: google

        name: project_id, required: true, type: string
        name: organization_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Decode inputs
        project_id = project_id or self.get_input("project_id", required=True)
        organization_id = organization_id or self.get_input("organization_id", required=False)
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Check if the project is empty
        self.logger.info(f"Checking if project '{project_id}' is empty...")
        try:
            self.enable_google_apis(project_id=project_id, exit_on_completion=False)

            is_empty = self.ds.is_google_project_empty(
                project_id=project_id,
                organization_id=organization_id,
                service_account_file=service_account_file,
                exit_on_completion=False,
            )
        except Exception as e:
            self.logger.error(f"Error determining if project '{project_id}' is empty: {e}")
            return self.exit_run(
                results=False,
                key="delete_empty_project",
                format_results=False,
                exit_on_completion=exit_on_completion,
            )

        if not is_empty:
            self.logger.info(f"Project '{project_id}' is not empty. Skipping deletion.")
            return self.exit_run(
                results=False,
                key="delete_empty_project",
                format_results=False,
                exit_on_completion=exit_on_completion,
            )

        # Delete the project if empty
        self.logger.info(f"Project '{project_id}' is empty. Proceeding with deletion...")
        try:
            google_client = self.ds.get_google_client(service_account_file=service_account_file)
            resource_manager = google_client.get_service("cloudresourcemanager", "v1")

            # Request to delete the project
            delete_request = resource_manager.projects().delete(projectId=project_id)
            delete_request.execute()

            self.logger.info(f"Successfully deleted project '{project_id}'.")
            return self.exit_run(
                results=True,
                key="delete_empty_project",
                format_results=False,
                exit_on_completion=exit_on_completion,
            )
        except Exception as e:
            self.logger.error(f"Failed to delete project '{project_id}': {e}")
            return self.exit_run(
                results=False,
                key="delete_empty_project",
                format_results=False,
                exit_on_completion=exit_on_completion,
            )

    def move_google_projects_to_billing_account(
        self,
        billing_account_name: Optional[str] = None,
        billing_account_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        service_account_file: Optional[Mapping] = None,
        exit_on_completion: bool = True,
    ):
        """
        Moves all Google projects to the specified billing account and deletes empty projects.

        generator=module_class: google

        name: billing_account_name, required: false, type: string, default: "Primary"
        name: billing_account_id, required: false, type: string
        name: organization_id, required: false, type: string
        name: service_account_file, required: false, json_encode: true, base64_encode: true
        """

        # Decode service account file
        service_account_file = service_account_file or self.decode_input("service_account_file", required=False)

        # Resolve organization ID if not provided
        organization_id = organization_id or self.get_input("organization_id", required=False)
        if not organization_id:
            self.logger.info("No organization ID provided. Attempting to resolve dynamically...")
            organization_id = self.ds.get_google_organization_id(
                service_account_file=service_account_file,
                exit_on_completion=False,
            )
            if not organization_id:
                raise ValueError("Organization ID could not be resolved.")
            self.logger.info(f"Resolved organization ID: {organization_id}")

        # Resolve billing account ID if not provided
        billing_account_id = billing_account_id or self.get_input("billing_account_id", required=False)
        if not billing_account_id:
            billing_account_name = billing_account_name or self.get_input(
                "billing_account_name", required=False, default="Primary"
            )
            billing_account_id = self.ds.get_google_billing_account(
                billing_account_name=billing_account_name,
                service_account_file=service_account_file,
                exit_on_completion=False,
            )

        # Retrieve all projects
        all_projects = self.ds.get_google_projects(
            service_account_file=service_account_file,
            exit_on_completion=False,
        )

        # Process each project
        for project_id, project_data in all_projects.items():
            project_name = project_data.get("name", project_id)
            project_billing_account_id = project_data.get("billingAccountID")
            if project_billing_account_id == billing_account_id:
                self.logger.info(
                    f"Skipping project '{project_name}' [{project_id}] as it is already linked to billing account."
                )
                continue

            if project_data.get("lifecycleState") != "ACTIVE":
                self.logger.warning(
                    f"Skipping project '{project_name}' [{project_id}] as it is not in 'ACTIVE' lifecycle state."
                )
                continue

            if project_billing_account_id:
                self.logger.info(
                    f"Skipping emptiness check for project '{project_name}' [{project_id}] as project has an assigned billing account"
                )
            else:
                # Check if project is empty and delete if it is
                if self.delete_empty_google_project(
                    project_id=project_id,
                    organization_id=organization_id,
                    service_account_file=service_account_file,
                    exit_on_completion=False,
                ):
                    self.logger.warning(f"Empty project '{project_name}' [{project_id}] was deleted instead.")
                    continue

            self.link_google_billing_account(
                project_id=project_id,
                billing_account_id=billing_account_id,
                service_account_file=service_account_file,
                exit_on_completion=False,
            )

        # Final result summary
        return self.exit_run(
            results={
                "billing_account_name": billing_account_name,
                "processed_projects": all_projects,
            },
            key="moved_projects",
            format_results=True,
            exit_on_completion=exit_on_completion,
        )

    def create_google_user(
        self,
        given_name: Optional[str] = None,
        family_name: Optional[str] = None,
        user_password: Optional[str] = None,
        primary_email: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Creates a Google Workspace user

        generator=module_class: google

        name: given_name, required: true, type: string
        name: family_name, required: true, type: string
        name: user_password, required: true, type: string
        name: primary_email, required: true, type: string
        name: exit_on_completion, required: false, default: true
        """

        if given_name is None:
            given_name = self.get_input("given_name", required=True)
        if family_name is None:
            family_name = self.get_input("family_name", required=True)
        if user_password is None:
            user_password = self.get_input("user_password", required=True)
        if primary_email is None:
            primary_email = self.get_input("primary_email", required=True)

        google_client = self.ds.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")

        # Check if the user already exists
        try:
            directory.users().get(userKey=primary_email).execute()
            self.logger.info(f"Google user already exists: {primary_email}")
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 404:
                user_body = {
                    "name": {"givenName": given_name, "familyName": family_name},
                    "password": user_password,
                    "primaryEmail": primary_email,
                }
                try:
                    directory.users().insert(body=user_body).execute()
                    self.logger.info(f"Created Google user: {primary_email}")
                except Exception as e:
                    self.logger.error(f"Failed to create Google user: {e}")
            else:
                self.logger.error(f"Failed to check if Google user exists: {e}")

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_google_group(
        self,
        group_email: Optional[str] = None,
        group_name: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Creates a Google Workspace group

        generator=module_class: google

        name: group_email, required: true, type: string
        name: group_name, required: true, type: string
        name: exit_on_completion, required: false, default: true
        """

        if group_email is None:
            group_email = self.get_input("group_email", required=True)
        if group_name is None:
            group_name = self.get_input("group_name", required=True)

        google_client = self.ds.get_google_client()
        directory = google_client.get_service("admin", "directory_v1")

        # Check if the group already exists
        try:
            directory.groups().get(groupKey=group_email).execute()
            self.logger.info(f"Google group already exists: {group_email}")
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 404:
                group_body = {"email": group_email, "name": group_name}
                try:
                    directory.groups().insert(body=group_body).execute()
                    self.logger.info(f"Created Google group: {group_email}")
                except Exception as e:
                    self.logger.error(f"Failed to create Google group: {e}")
            else:
                self.logger.error(f"Failed to check if Google group exists: {e}")

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_aws_sso_user(
        self,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_password: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Creates an AWS SSO user

        generator=module_class: aws

        name: user_name, required: true, type: string
        name: user_email, required: true, type: string
        name: user_password, required: true, type: string
        name: execution_role_arn, required: false, type: string
        name: exit_on_completion, required: false, default: true
        """
        if user_name is None:
            user_name = self.get_input("user_name", required=True)
        if user_email is None:
            user_email = self.get_input("user_email", required=True)
        if user_password is None:
            user_password = self.get_input("user_password", required=True)

        client = self.ds.get_aws_client(client_name="sso-admin", execution_role_arn=execution_role_arn)

        # Check if the user already exists
        try:
            client.describe_user(UserName=user_name)
            self.logger.info(f"AWS SSO user already exists: {user_name}")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                user_body = {
                    "UserName": user_name,
                    "UserEmail": user_email,
                    "UserPassword": user_password,
                }
                try:
                    client.create_user(**user_body)
                    self.logger.info(f"Created AWS SSO user: {user_email}")
                except botocore.exceptions.ClientError as e:
                    self.logger.error(f"Failed to create AWS SSO user: {e}")
            else:
                self.logger.error(f"Failed to check if AWS SSO user exists: {e}")

        return self.exit_run(exit_on_completion=exit_on_completion)

    def create_aws_sso_group(
        self,
        group_name: Optional[str] = None,
        execution_role_arn: Optional[str] = None,
        exit_on_completion: bool = True,
    ):
        """
        Creates an AWS SSO group

        generator=module_class: aws

        name: group_name, required: true, type: string
        name: execution_role_arn, required: false, type: string
        name: exit_on_completion, required: false, default: true
        """
        if group_name is None:
            group_name = self.get_input("group_name", required=True)

        client = self.ds.get_aws_client(client_name="sso-admin", execution_role_arn=execution_role_arn)
        group = None

        # Check if the group already exists
        try:
            group = client.describe_group(GroupName=group_name)
            self.logger.info(f"AWS SSO group already exists: {group_name}")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                group_body = {"GroupName": group_name}
                try:
                    group = client.create_group(**group_body)
                    self.logger.info(f"Created AWS SSO group: {group_name}")
                except botocore.exceptions.ClientError as e:
                    self.logger.error(f"Failed to create AWS SSO group: {e}")
            else:
                self.logger.error(f"Failed to check if AWS SSO group exists: {e}")

        return self.exit_run(results=group, exit_on_completion=exit_on_completion)

    # User Status & Type Management
    def _get_user_params(self, user_data: Dict) -> Tuple[str, bool, bool]:
        """Gets user parameters from user data.
        # NOPARSE
        """
        return (
            user_data.get("orgUnitPath", ""),
            user_data.get("archived", False),
            user_data.get("suspended", False),
        )

    def _get_user_type(self, user_data: Dict) -> Tuple[str, bool, bool, str]:
        """Determines user type and status.
        # NOPARSE
        """
        org_unit_path, archived, suspended = self._get_user_params(user_data)
        if org_unit_path.startswith("/Automation"):
            calculated_user_type = "bot"
        elif archived or suspended:
            calculated_user_type = "inactive"
        else:
            calculated_user_type = "active"
        return org_unit_path, archived, suspended, calculated_user_type

    def _onboard_new_users(
        self,
        directory_client,
        slack_client,
        onboard_users: Dict,
        existing_google_users: Dict,
    ) -> None:
        """Onboards new users to Google Workspace.
        # NOPARSE
        """

        def generate_password(length=12):
            characters = string.ascii_letters + string.digits + string.punctuation
            return "".join(secrets.choice(characters) for _ in range(length))

        for new_email, new_user_data in onboard_users.items():
            self.logger.info(f"Checking if {new_email} needs to be onboarded")
            if new_email in existing_google_users:
                self.logger.info(f"{new_email} has already been onboarded")
                continue

            initial_password = generate_password()
            try:
                user_body = self.merger.merge(
                    {
                        "primaryEmail": new_email,
                        "suspended": False,
                        "password": initial_password,
                        "changePasswordAtNextLogin": True,
                        "orgUnitPath": "/Users",
                        "includeInGlobalAddressList": True,
                    },
                    deepcopy(new_user_data),
                )

                existing_google_users[new_email] = directory_client.users().insert(body=user_body).execute()

                slack_client.send_message(
                    text="New Onboarding Event!",
                    channel_id="C07FCAX8Y2J",
                    lines=[
                        f"{new_email} has been onboarded at FlipsideCrypto",
                        f"Their initial password has been set as '{initial_password}', without the quotes.",
                        "A member of this channel will need to email them with their login instructions.",
                        "CC @Kerri @Will",
                    ],
                )
            except Exception as e:
                self.errors.append(f"Failed to onboard user {new_email} or notify channel: {e}")

    # Calendar Access Management
    def _handle_calendar_access(
        self,
        calendar_client,
        google_email: str,
        existing_shares: Dict,
        suspended: bool,
        archived: bool,
    ) -> None:
        """Manages user access to team calendar.
        # NOPARSE
        """
        if google_email in existing_shares:
            rule_id = existing_shares[google_email]["id"]
            if suspended or archived:
                self.logger.warning(f"Removing suspended/archived user {google_email} from Team calendar")
                calendar_client.acl().delete(calendarId=self.ds.TEAM_CALENDAR_ID, ruleId=rule_id).execute()
            else:
                self.logger.info(f"{google_email} is already in the Team calendar")
        elif suspended or archived:
            self.logger.warning(f"Skipping adding suspended/archived user {google_email} to Team calendar")
        else:
            self.logger.info(f"Adding {google_email} to team calendar")
            rule = {
                "scope": {
                    "type": "user",
                    "value": google_email,
                },
                "role": "writer",
            }
            created_rule = calendar_client.acl().insert(calendarId=self.ds.TEAM_CALENDAR_ID, body=rule).execute()
            self.logger.info(f"Created new rule: {created_rule['id']}")

    def _add_google_user_to_team_calendar(
        self,
        primary_email: str,
        calendar_client,
    ) -> Any:
        """Adds a user to the team calendar.
        # NOPARSE
        """

        try:
            self.logger.info(f"Adding {primary_email} to team calendar")
            rule = {
                "scope": {
                    "type": "user",
                    "value": primary_email,
                },
                "role": "writer",
            }
            created_rule = calendar_client.acl().insert(calendarId=self.ds.TEAM_CALENDAR_ID, body=rule).execute()
            self.logger.info(f"Created new rule: {created_rule['id']}")
            return created_rule
        except googleapiclient.errors.HttpError as e:
            self.errors.append(f"Failed to add user {primary_email} to team calendar: {e}")
            return None

    def _remove_google_user_from_team_calendar(
        self,
        primary_email: str,
        rule_id: str,
        calendar_client,
    ) -> None:
        """Removes a user from the team calendar.
        # NOPARSE
        """
        try:
            self.logger.warning(f"Removing user {primary_email} from Team calendar")
            calendar_client.acl().delete(calendarId=self.ds.TEAM_CALENDAR_ID, ruleId=rule_id).execute()
        except googleapiclient.errors.HttpError as e:
            self.errors.append(f"Failed to remove user {primary_email} from team calendar: {e}")

    # License Management
    def _get_license_allocations(self, google_client) -> pd.DataFrame:
        """Gets and processes license allocations from the Google Sheet.
        # NOPARSE
        """
        google_client_credentials = google_client.get_credentials()
        sheets = gspread.Client(auth=google_client_credentials)
        license_allocations_worksheet = sheets.open_by_key("1mX6Z8hyOCarIkiOw7BuHqhb4Q_Jc9G5WBr3zSRS8-mQ")
        license_allocations_sheet = license_allocations_worksheet.sheet1
        return pd.DataFrame(license_allocations_sheet.get_all_records())

    def _manage_gemini_licenses(
        self,
        licensing_client,
        license_allocations: pd.DataFrame,
        existing_google_users: Dict,
        slack_users: Dict,
    ) -> list[str]:
        """Manages Gemini license assignments and returns Slack user IDs for the Gemini channel.
        # NOPARSE
        """
        current_licenses = self.ds.list_available_google_workspace_licenses(exit_on_completion=False)
        gemini_assignments = set()
        if "101047" in current_licenses:
            for sku_data in current_licenses["101047"]["skus"].values():
                for assignment in sku_data["assignments"].get("users", []):
                    gemini_assignments.add(assignment["user_id"].lower())

        self._cleanup_inactive_gemini_licenses(licensing_client, gemini_assignments, existing_google_users)
        return self._process_gemini_assignments(
            licensing_client,
            license_allocations,
            existing_google_users,
            slack_users,
            gemini_assignments,
        )

    def _cleanup_inactive_gemini_licenses(
        self,
        licensing_client,
        gemini_assignments: Set[str],
        existing_google_users: Dict,
    ) -> None:
        """Removes Gemini licenses from inactive or old users.
        # NOPARSE
        """
        for email in gemini_assignments:
            if (
                email.endswith("-old@flipsidecrypto.com")
                or email not in existing_google_users
                or existing_google_users[email].get("archived")
                or existing_google_users[email].get("suspended")
            ):
                try:
                    licensing_client.licenseAssignments().delete(
                        productId="101047", skuId="1010470001", userId=email
                    ).execute()
                    self.logger.info(f"Removed Gemini license from inactive/old user: {email}")
                except googleapiclient.errors.HttpError as e:
                    self.errors.append(f"Failed to remove Gemini license from user {email}: {e}")

    def _process_gemini_assignments(
        self,
        licensing_client,
        license_allocations: pd.DataFrame,
        existing_google_users: Dict,
        slack_users: Dict,
        gemini_assignments: Set[str],
    ) -> list[str]:
        """Process Gemini license assignments and returns list of Slack user IDs.
        # NOPARSE
        """
        gemini_channel_user_ids = []
        for email in license_allocations["Email"]:
            email = email.strip().lower()

            # Handle Slack channel membership
            if email not in slack_users:
                self.logger.warning(f"Email {email} not found in Slack and must be added manually")
            else:
                slack_userid = slack_users[email]["slack_userid"]
                self.logger.info(f"User {email} found on Slack: {slack_userid}")
                gemini_channel_user_ids.append(slack_userid)

            # Skip license assignment for inactive users
            if (
                email not in existing_google_users
                or existing_google_users[email].get("archived")
                or existing_google_users[email].get("suspended")
            ):
                self.logger.warning(f"Skipping Gemini license for inactive user: {email}")
                continue

            # Skip if already licensed
            if email in gemini_assignments:
                self.logger.info(f"{email} already has a Gemini license")
                continue

            try:
                licensing_client.licenseAssignments().insert(
                    productId="101047", skuId="1010470001", body={"userId": email}
                ).execute()
                self.logger.info(f"Assigned Gemini license to user {email}")
            except googleapiclient.errors.HttpError as e:
                self.errors.append(f"Failed to assign Gemini license to user {email}: {e}")

        return gemini_channel_user_ids

    # Vendor Integration Management
    def _handle_aws_account_assignment(
        self,
        directory_client,
        group_name: str,
        member_email: str,
        existing_google_users: Dict,
    ) -> None:
        """Assigns AWS account name to user's custom schema.
        # NOPARSE
        """
        aws_username = "User-" + member_email.split("@")[0].lower().replace(".", "_")

        custom_schemas = deepcopy(existing_google_users[member_email].get("customSchemas", {}))
        if "VendorAttributes" not in custom_schemas:
            custom_schemas["VendorAttributes"] = {}

        if not custom_schemas["VendorAttributes"].get("awsAccountName"):
            custom_schemas["VendorAttributes"]["awsAccountName"] = aws_username
            try:
                directory_client.users().update(userKey=member_email, body={"customSchemas": custom_schemas}).execute()
                self.logger.info(f"Assigned AWS username {aws_username} to {member_email}")
            except googleapiclient.errors.HttpError as e:
                self.errors.append(f"Failed to assign AWS username to {member_email}: {e}")

    def _add_google_user_to_group(
        self, primary_email: str, group_key: str, directory_client, role: str = "MEMBER"
    ) -> bool:
        """Adds Google user to a group
        # NOPARSE
        """
        try:
            directory_client.members().insert(
                groupKey=group_key,
                body={"email": primary_email, "role": role},
            ).execute()
            return True
        except googleapiclient.errors.HttpError as e:
            if "Member already exists" in str(e):
                self.logger.warning(f"{primary_email} already in {group_key}")
                return True

            self.errors.append(f"Failed to add {primary_email} to {group_key}: {e}")
            return False

    def _remove_google_user_from_group(self, primary_email: str, group_key: str, directory_client) -> bool:
        """Removes Google user from a group
        # NOPARSE
        """
        try:
            directory_client.members().delete(groupKey=group_key, memberKey=primary_email).execute()
            self.logger.info(f"Removed {primary_email} from {group_key}")
            return True
        except googleapiclient.errors.HttpError as e:
            self.errors.append(f"Failed to remove {primary_email} from {group_key}: {e}")
            return False

    def _sync_vendor_integrations(
        self,
        existing_google_users: Dict,
        existing_google_groups: Dict,
        existing_github_users: Dict,
    ) -> None:
        """Synchronizes user access across Zoom and updates GitHub information.
        # NOPARSE
        """

        failed_to_archive = []
        active_google_users = []

        # # Sync GitHub username to custom schema
        # github_user_data = github_users_by_email.get(google_email)
        # github_username = github_user_data["login"] if github_user_data else None
        # if github_username:
        #     if self._populate_custom_schema_field(
        #         google_email,
        #         "VendorAttributes",
        #         "githubUsername",
        #         github_username,
        #         existing_google_users,
        #     ):
        #         users_with_schema_updates.add(google_email)
        #
        # # Update users with schema changes
        # for email in users_with_schema_updates:
        #     try:
        #         user_custom_schema_data = existing_google_users[email].get(
        #             "customSchemas", {}
        #         )
        #         directory.users().update(
        #             userKey=email, body={"customSchemas": user_custom_schema_data}
        #         ).execute()
        #         self.logger.info(f"Updated schema for user {email}")
        #     except googleapiclient.errors.HttpError as e:
        #         self.errors.append(f"Failed to update customSchemas for {email}: {e}")

    # Schema Management
    def _populate_custom_schema_field(
        self,
        schema_user_email: str,
        field_schema_name: str,
        schema_field_name: str,
        field_value: str,
        existing_google_users: dict[str, Any],
    ) -> bool:
        """Populates a custom schema field for a user.
        # NOPARSE
        """
        if not field_value:
            return False

        custom_schemas = deepcopy(existing_google_users[schema_user_email].get("customSchemas", {}))
        if field_schema_name not in custom_schemas:
            custom_schemas[field_schema_name] = {}

        stored_schema_value = custom_schemas[field_schema_name].get(schema_field_name)
        if not utils.is_nothing(stored_schema_value):
            self.logger.warning(
                f"User {schema_user_email} custom schema {field_schema_name} field {schema_field_name} already has a value: '{stored_schema_value}'"
            )
            return False

        custom_schemas[field_schema_name][schema_field_name] = field_value
        existing_google_users[schema_user_email]["customSchemas"] = custom_schemas
        return True

    def _ensure_custom_schemas(self, directory_client) -> None:
        """Ensures required custom schemas exist and are up to date.
        # NOPARSE
        """
        existing_schemas = {
            schema["schemaName"]: schema
            for schema in directory_client.schemas().list(customerId="my_customer").execute().get("schemas", [])
        }

        required_schemas = {
            "VendorAttributes": ["githubUsername", "awsAccountName"],
        }

        for schema_name, schema_fields in required_schemas.items():
            self.logger.info(f"Ensuring that custom schema {schema_name} exists and is up to date")
            existing_schema = existing_schemas.get(schema_name)

            if existing_schema:
                # Track updates and deletions needed
                fields_to_add = []
                fields_to_delete = []
                existing_fields = {field["fieldName"]: field for field in existing_schema.get("fields", [])}

                # Identify fields to add
                for required_field in schema_fields:
                    if required_field not in existing_fields:
                        fields_to_add.append(
                            {
                                "fieldName": required_field,
                                "fieldType": "STRING",
                                "multiValued": False,
                                "readAccessType": "ADMINS_AND_SELF",
                            }
                        )

                # Identify fields to delete
                for existing_field_name in existing_fields.keys():
                    if existing_field_name not in schema_fields:
                        fields_to_delete.append(existing_field_name)

                # Remove extra fields if any
                if fields_to_delete:
                    self.logger.warning(f"Removing extra fields from {schema_name}: {fields_to_delete}")
                    for field_to_delete in fields_to_delete:
                        try:
                            directory_client.schemas().delete(
                                customerId="my_customer",
                                schemaKey=existing_schema["schemaId"],
                                body={"fields": [{"fieldName": field_to_delete}]},
                            ).execute()
                            self.logger.info(f"Field {field_to_delete} removed from {schema_name}")
                        except googleapiclient.errors.HttpError as e:
                            self.errors.append(f"Failed to delete field {field_to_delete} in {schema_name}: {e}")

                # Add missing fields if any
                if fields_to_add:
                    self.logger.info(f"Adding new fields to {schema_name}: {fields_to_add}")
                    try:
                        directory_client.schemas().patch(
                            customerId="my_customer",
                            schemaKey=existing_schema["schemaId"],
                            body={"fields": fields_to_add},
                        ).execute()
                        self.logger.info(f"New fields added to {schema_name}: {fields_to_add}")
                    except googleapiclient.errors.HttpError as e:
                        self.errors.append(f"Failed to add fields in {schema_name}: {e}")
            else:
                # Schema does not exist, create it
                self.logger.info(f"Creating {schema_name} custom schema")
                schema_body = {
                    "schemaName": schema_name,
                    "fields": [
                        {
                            "fieldName": field_name,
                            "fieldType": "STRING",
                            "multiValued": False,
                            "readAccessType": "ADMINS_AND_SELF",
                        }
                        for field_name in schema_fields
                    ],
                }
                try:
                    directory_client.schemas().insert(customerId="my_customer", body=schema_body).execute()
                    self.logger.info(f"{schema_name} custom schema created successfully.")
                except googleapiclient.errors.HttpError as e:
                    self.errors.append(f"Failed to create {schema_name} custom schema: {e}")

    # Main Sync Method
    def sync_flipsidecrypto_users_and_groups(
        self,
        group_members_assigned_aws_accounts: Optional[list[Any]] = None,
        onboard_users: Optional[dict[str, Any]] = None,
        exit_on_completion: bool = True,
    ):
        """Syncs FlipsideCrypto users and groups

        generator=module_class: gitops

        name: group_members_assigned_aws_accounts, required: false, default: [], json_encode: true
        name: onboard_users, required: false, default: {}, json_encode: true, base64_encode: true
        """
        # Initialize inputs
        if group_members_assigned_aws_accounts is None:
            group_members_assigned_aws_accounts = self.decode_input(
                "group_members_assigned_aws_accounts",
                required=False,
                default=[],
                allow_none=False,
                decode_from_base64=False,
            )

        if onboard_users is None:
            onboard_users = self.decode_input("onboard_users", required=False, default={}, allow_none=False)

        # Initialize all clients
        google_client = self.ds.get_google_client()
        calendar = google_client.get_service("calendar", "v3")
        zoom_client = self.ds.get_zoom_client()
        zoom_users = zoom_client.get_zoom_users()
        # users_with_schema_updates = set()
        # directory = self.ds.get_google_client().get_service("admin", "directory_v1")

        existing_shares = self.ds.get_flipsidecrypto_team_calendar_shares(exit_on_completion=False)
        directory = google_client.get_service("admin", "directory_v1")

        # licensing = google_client.get_service("licensing", "v1")
        # slack_client = self.ds.get_slack_client()
        # slack_users = self.ds.get_slack_users(
        #     include_app_users=False,
        #     include_deleted=False,
        #     include_bots=False,
        #     flipsidecrypto_users_only=True,
        #     exit_on_completion=False,
        # )

        # # Get license allocations
        # license_allocations = self._get_license_allocations(google_client)

        # Get all existing data

        existing_google_users = self.ds.get_google_users(unhump_users=False, exit_on_completion=False)
        existing_google_groups = self.ds.get_google_groups(
            unhump_groups=False,
            sort_by_name=True,
            exit_on_completion=False,
        )
        existing_team_group_members = set(existing_google_groups.get("Team", {}).get("members", {}).keys())
        # existing_github_users = self.ds.get_github_users(
        #     exit_on_completion=False,
        # )
        # github_users_by_email = {
        #     user_data["primary_email"]: user_data
        #     for user_data in existing_github_users.values()
        #     if user_data.get("primary_email")
        # }
        zoom_client = self.ds.get_zoom_client()

        # Ensure custom schemas exist
        self._ensure_custom_schemas(directory)
        if len(self.errors) > 0:
            return self.exit_run(exit_on_completion=exit_on_completion)

        # Onboard new users
        # self._onboard_new_users(
        #     directory, slack_client, onboard_users, existing_google_users
        # )
        # Process each user for team membership and calendar access

        failed_to_archive = []

        for google_email, user_data in deepcopy(existing_google_users).items():
            org_unit_path, archived, suspended, user_type = self._get_user_type(user_data)

            if user_type == "bot":
                self.logger.warning(f"Skipping bot user {google_email}")
                continue

            first_name = user_data.get("name", {}).get("givenName", "")
            last_name = user_data.get("name", {}).get("familyName", "")

            if suspended or archived:
                if not org_unit_path.endswith("LimitedAccess"):
                    try:
                        directory.users().update(userKey=google_email, body={"orgUnitPath": "/LimitedAccess"}).execute()
                        self.logger.info(f"Moved user {google_email} to LimitedAccess")
                        org_unit_path = "/LimitedAccess"
                    except googleapiclient.errors.HttpError as e:
                        self.errors.append(f"Failed to move user {google_email} to LimitedAccess: {e}")

                if org_unit_path.endswith("LimitedAccess") and not archived:
                    try:
                        directory.users().update(
                            userKey=google_email,
                            body={"archived": True, "suspended": False},
                        ).execute()
                        self.logger.info(f"Archived user: {google_email}")
                        existing_google_users[google_email]["archived"] = True
                        existing_google_users[google_email]["suspended"] = False
                    except googleapiclient.errors.HttpError as e:
                        self.logger.error(f"Failed to archive user {google_email}: {e}")
                        failed_to_archive.append(google_email)

                if google_email in existing_shares:
                    self.logger.warning(f"Removing suspended or archived user {google_email} from Team Google calendar")
                    rule_id = existing_shares[google_email]["id"]
                    self._remove_google_user_from_team_calendar(google_email, rule_id, calendar)

                if google_email in zoom_users:
                    self.logger.warning(f"Removing suspended or archived user {google_email} from Zoom")
                    zoom_client.remove_zoom_user(google_email)

            else:
                if org_unit_path == "/Consultants":
                    self.logger.info(f"Ensuring consultant {google_email} is not in Team calendar or group")
                    if google_email in existing_team_group_members:
                        self.logger.warning(f"Removing consultant {google_email} from Team group")
                        if self._remove_google_user_from_group(google_email, "team@flipsidecrypto.com", directory):
                            existing_team_group_members.remove(google_email)

                    if google_email in existing_shares:
                        self.logger.warning(f"Removing consultant {google_email} from Team calendar")
                        rule_id = existing_shares[google_email]["id"]
                        self._remove_google_user_from_team_calendar(google_email, rule_id, calendar)
                else:
                    if google_email not in existing_team_group_members:
                        self.logger.info(f"Attempting to add {google_email} to the Team group")
                        if self._add_google_user_to_group(google_email, "team@flipsidecrypto.com", directory):
                            existing_team_group_members.add(google_email)

                    if google_email not in existing_shares and not org_unit_path == "/Consultants":
                        self.logger.info(f"Attempting to add {google_email} to the Team calendar")
                        created_rule = self._add_google_user_to_team_calendar(google_email, calendar)
                        if not utils.is_nothing(created_rule):
                            existing_shares[google_email] = created_rule

                if google_email not in zoom_users:
                    self.logger.info(f"Attempting to add {google_email} to Zoom")
                    if zoom_client.create_zoom_user(google_email, first_name, last_name):
                        zoom_users[google_email] = {}

        if failed_to_archive:
            self.errors.append(
                f"Users: {', '.join(failed_to_archive)}, failed to archive. Please purchase {len(failed_to_archive)} archive licenses and rerun."
            )

        for group_name, group_data in existing_google_groups.items():
            self.logger.info(f"Syncing Google group {group_name}")
            existing_members = group_data["members"]
            group_email = group_data["email"]
            deleted_members = set()

            for member_email in existing_members:
                if not member_email.endswith("@flipsidecrypto.com"):
                    self.logger.warning(f"Ignoring external member {member_email}")
                    continue

                member_data = existing_google_users.get(member_email, {})
                _, member_archived, member_suspended = self._get_user_params(member_data)

                if member_email not in existing_google_users or member_suspended or member_archived:
                    self.logger.warning(f"Member {member_email} is no longer active")
                    if self._remove_google_user_from_group(member_email, group_email, directory):
                        deleted_members.add(member_email)

                elif group_members_assigned_aws_accounts and (
                    group_name in group_members_assigned_aws_accounts
                    or group_email in group_members_assigned_aws_accounts
                ):
                    self._handle_aws_account_assignment(
                        directory,
                        group_name,
                        member_email,
                        existing_google_users,
                    )

        # # Handle Gemini licenses and Slack channel
        # gemini_channel_user_ids = self._manage_gemini_licenses(
        #     licensing, license_allocations, existing_google_users, slack_users
        # )

        # # Update Slack channel membership
        # slack_client.update_channel_members(
        #     channel_name="gemini-onboarding",
        #     is_private=False,
        #     user_ids=gemini_channel_user_ids,
        #     remove_other_users=False,
        #     raise_on_api_error=False,
        # )

        return self.exit_run(exit_on_completion=exit_on_completion)
