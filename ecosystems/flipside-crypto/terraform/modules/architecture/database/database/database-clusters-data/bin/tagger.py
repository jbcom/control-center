#!/usr/bin/env python3.9

"""Script to add tags to unmanaged RDS instances"""

import os
import sys
import logging
import json
from datetime import datetime
import botocore
import boto3
from dateutil.tz import tzlocal

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION")
AWS_ASSUMED_ROLE_ARN = os.getenv("AWS_ASSUMED_ROLE_ARN")

assume_role_cache: dict = {}


def assumed_role_session(role_arn: str, base_session: botocore.session.Session = None):
    base_session = base_session or boto3.session.Session()._session
    fetcher = botocore.credentials.AssumeRoleCredentialFetcher(
        client_creator=base_session.create_client,
        source_credentials=base_session.get_credentials(),
        role_arn=role_arn,
    )
    creds = botocore.credentials.DeferredRefreshableCredentials(
        method="assume-role",
        refresh_using=fetcher.fetch_credentials,
        time_fetcher=lambda: datetime.now(tzlocal()),
    )
    botocore_session = botocore.session.Session()
    botocore_session._credentials = creds
    return boto3.Session(botocore_session=botocore_session)


if AWS_ASSUMED_ROLE_ARN != "":
    session = assumed_role_session(AWS_ASSUMED_ROLE_ARN)
else:
    session = boto3.session.Session()

rds = session.client(service_name="rds", region_name=AWS_REGION)


def split_tags_into_pairs(tags):
    pairs = []

    for k, v in tags.items():
        pairs.append({"Key": k, "Value": v})

    return pairs


def tag_database_instances(databases, tags):
    for database_name, database_arn in databases.items():
        logger.info(
            f"Adding tags '{tags}' to database name: {database_name}, ARN: {database_arn}"
        )
        response = rds.add_tags_to_resource(
            ResourceName=database_arn, Tags=split_tags_into_pairs(tags)
        )

        logger.info(f"Database {database_name} tagged: {response}")


def main():
    logger.setLevel(logging.DEBUG)
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    params = {}

    for param in ["DATABASES", "TAGS"]:
        try:
            params[param.lower()] = json.loads(os.getenv(param))
        except Exception as exc:
            logger.critical(f"Failed to load {param} from environment: {exc}")
            sys.exit(1)

    logger.debug(f"Params: {params}")
    tag_database_instances(**params)


if __name__ == "__main__":
    main()
